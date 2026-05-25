# =============================================================================
# CHAT SERVICE — services/chat_service.py
# Gestionnaire des connexions WebSocket et publication Kafka
# =============================================================================
# RÔLE DU FICHIER :
# C'est le cœur du chat service. Il gère :
# 1. Le registre des connexions WebSocket actives (qui est connecté où)
# 2. La persistance des messages en base de données
# 3. La publication des messages sur Kafka (pour le fan-out)
# 4. La distribution des messages aux clients connectés (broadcast)
# =============================================================================

import json
from collections import defaultdict   # Dict avec valeur par défaut (liste vide)
from typing import Dict, List
from fastapi import WebSocket
import logging
from aiokafka import AIOKafkaProducer
from sqlalchemy import select
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.message import Message

logger = logging.getLogger(__name__)


# =============================================================================
# REGISTRE DES CONNEXIONS WEBSOCKET
# =============================================================================
# Dict[str, List[WebSocket]] : 
#   clé = nom de la room (ex: "red", "blue", "battle_uuid123")
#   valeur = liste des WebSocket actifs dans cette room
#
# defaultdict(list) : si on accède à une clé inexistante → retourne [] automatiquement
# Évite le "KeyError" et les vérifications "if key not in dict"
_connections: Dict[str, List[WebSocket]] = defaultdict(list)

# Singleton du producer Kafka (même pattern que battle_service)
_producer: AIOKafkaProducer | None = None


# =============================================================================
# SINGLETON KAFKA PRODUCER
# =============================================================================
async def get_producer() -> AIOKafkaProducer:
    global _producer
    if _producer is None:
        p = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        await p.start()
        _producer = p
    return _producer


# =============================================================================
# FONCTION : connect — Accepter et enregistrer une connexion WebSocket
# =============================================================================
async def connect(room: str, ws: WebSocket):
    # websocket.accept() : complète le handshake WebSocket (HTTP Upgrade → WS)
    # Sans cet appel, la connexion reste en attente et le client reçoit une erreur
    await ws.accept()
    
    # Ajoute le WebSocket à la liste des connexions de cette room
    _connections[room].append(ws)
    logger.info(f"WebSocket accepted for room: {room}. Total in room: {len(_connections[room])}")


# =============================================================================
# FONCTION : disconnect — Retirer une connexion fermée
# =============================================================================
def disconnect(room: str, ws: WebSocket):
    # disconnect est synchrone (pas async) : on modifie juste une liste en mémoire
    try:
        if ws in _connections[room]:
            _connections[room].remove(ws)
            logger.info(f"WebSocket removed from room: {room}. Remaining: {len(_connections[room])}")
    except Exception as e:
        logger.error(f"Error during disconnect: {e}")


# =============================================================================
# FONCTION : publish_message — Sauvegarder en BDD ET publier sur Kafka
# =============================================================================
async def publish_message(message: dict):
    # ÉTAPE 1 : Persistance en base de données
    # On sauvegarde AVANT d'envoyer à Kafka pour garantir qu'on ne perd pas le message
    try:
        async with AsyncSessionLocal() as db:
            db_msg = Message(
                room=message.get("room"),       # None si message global
                author=message.get("author"),
                content=message.get("content"),
                is_bot=message.get("is_bot", False),
                team=message.get("team")        # "red" ou "blue"
            )
            db.add(db_msg)
            await db.commit()
    except Exception as e:
        logger.error(f"Error saving message to DB: {e}")
        # On continue même si la BDD est en erreur

    # ÉTAPE 2 : Publication sur Kafka
    # Le consumer (dans main.py) recevra ce message et fera le broadcast WebSocket
    try:
        producer = await get_producer()
        # KAFKA_TOPIC_CHAT = "chat-messages"
        await producer.send_and_wait(settings.KAFKA_TOPIC_CHAT, message)
    except Exception as e:
        logger.warning(f"Kafka producer error: {e}")
        # On continue même si Kafka est down
        # Dans ce cas, le message est sauvegardé en BDD mais pas diffusé en temps réel


# =============================================================================
# FONCTION : broadcast — Envoyer un message à tous les clients d'une room
# =============================================================================
async def broadcast(room: str, message: dict):
    if room not in _connections:
        return  # Personne dans cette room, rien à faire
    
    dead = []  # Liste des connexions mortes à nettoyer
    
    # On itère sur une COPIE de la liste (list()) pour pouvoir la modifier
    for ws in list(_connections[room]):
        try:
            # send_json : envoie le dict sérialisé en JSON via WebSocket
            await ws.send_json(message)
        except Exception as e:
            # La connexion a planté (client déconnecté sans fermeture propre)
            logger.warning(f"Failed to send to client in {room}, marking dead: {e}")
            dead.append(ws)

    # Nettoyage des connexions mortes
    for ws in dead:
        disconnect(room, ws)


# =============================================================================
# FONCTION : broadcast_all — Envoyer à toutes les équipes (red + blue)
# =============================================================================
async def broadcast_all(message: dict):
    # Utilisé pour les notifications de résultats de tours (tout le monde doit voir)
    logger.info(f"Broadcasting to all teams: {message.get('content')}")
    for team in ["red", "blue"]:
        await broadcast(team, message)


# =============================================================================
# FONCTION : get_history — Récupérer l'historique des messages
# =============================================================================
async def get_history(limit: int = 50) -> List[dict]:
    async with AsyncSessionLocal() as db:
        # ORDER BY sent_at DESC pour avoir les plus récents en premier
        # LIMIT pour ne pas charger toute la table
        result = await db.execute(
            select(Message).order_by(Message.sent_at.desc()).limit(limit)
        )
        messages = result.scalars().all()
        # reversed() : on retourne en ordre chronologique (les vieux en premier)
        return [
            {
                "author": m.author,
                "content": m.content,
                "is_bot": m.is_bot,
                "team": m.team,
                "sent_at": m.sent_at.isoformat() if m.sent_at else None
            }
            for m in reversed(messages)  # reversed() pour ordre chronologique
        ]


# =============================================================================
# FONCTION : stop_producer — Fermer proprement la connexion Kafka
# =============================================================================
async def stop_producer():
    global _producer
    if _producer:
        await _producer.stop()
        _producer = None

# =============================================================================
# QUESTION PIÈGE : "Pourquoi stocker dans _connections en mémoire ?"
# =============================================================================
# Les connexions WebSocket sont des objets Python vivants (sockets TCP actifs).
# On NE PEUT PAS les stocker en base de données ou dans Redis.
# Une connexion = un socket = une ressource mémoire de ce processus.
# C'est pourquoi en production multi-instances, chaque pod K8s a SES connexions,
# et Kafka sert de "bus" pour synchroniser les messages entre instances.
