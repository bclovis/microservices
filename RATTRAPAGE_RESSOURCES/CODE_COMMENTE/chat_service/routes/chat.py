# =============================================================================
# CHAT SERVICE — routes/chat.py
# Routes WebSocket et HTTP du service de chat
# =============================================================================
# RÔLE DU FICHIER :
# Ce fichier est le plus important à comprendre pour l'oral car il montre
# comment fonctionnent les WebSockets dans FastAPI.
#
# DIFFÉRENCE HTTP vs WebSocket :
# ┌─────────────────────────────────────────────────────────────┐
# │  HTTP   : Client → Serveur (requête) → Client (réponse)     │
# │           Connexion fermée après chaque échange             │
# │                                                             │
# │  WebSocket : Client ←──────────────── Serveur              │
# │              Connexion PERSISTANTE bidirectionnelle          │
# │              Le serveur peut pousser des données sans        │
# │              que le client ait demandé                       │
# └─────────────────────────────────────────────────────────────┘
# =============================================================================

import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.schemas.message import ChatMessage
from app.services import chat_service

logger = logging.getLogger(__name__)
router = APIRouter()  # Pas de prefix : les WebSocket URLs ne suivent pas la convention REST


# =============================================================================
# GET /api/chat/history — Historique des messages
# =============================================================================
# Route HTTP classique pour récupérer les derniers messages (ex: quand on rejoint le chat)
@router.get("/api/chat/history")
async def get_chat_history(limit: int = 50):
    # limit : paramètre de query optionnel ex: /api/chat/history?limit=100
    return await chat_service.get_history(limit)


# =============================================================================
# WebSocket /ws/chat/{team} — Chat en temps réel par équipe
# =============================================================================
# URL : ws://localhost/ws/chat/red?username=Betsaleel
# {team} = paramètre de chemin : "red" ou "blue"
# username = paramètre de query obligatoire (Query(...) = obligatoire)
@router.websocket("/ws/chat/{team}")
async def chat_endpoint(
    websocket: WebSocket,        # L'objet WebSocket représente la connexion au client
    team: str,                   # "red" ou "blue"
    username: str = Query(...)   # ... = paramètre obligatoire, erreur si absent
):
    logger.info(f"New connection request: team={team}, username={username}")

    # Validation : seuls "red" et "blue" sont acceptés
    if team not in ("red", "blue"):
        logger.warning(f"Invalid team: {team}")
        # code=1003 = code WebSocket pour "Unsupported Data" (mauvais format/valeur)
        await websocket.close(code=1003)
        return

    try:
        # ÉTAPE 1 : Accepter et enregistrer la connexion
        # chat_service.connect() appelle websocket.accept() et ajoute à _connections[team]
        await chat_service.connect(team, websocket)
        logger.info(f"Connected: {username} to {team}")

        # ÉTAPE 2 : Boucle de lecture des messages entrants
        # Cette boucle tourne INDÉFINIMENT tant que la connexion est ouverte
        while True:
            # receive_text() : BLOQUE (de manière async) jusqu'à recevoir un message
            # Si le client ferme la connexion → lève WebSocketDisconnect
            data = await websocket.receive_text()
            logger.info(f"Message from {username} ({team}): {data}")
            
            # Construit le message à distribuer
            msg = {
                "author": username,
                "content": data,
                "is_bot": False,
                "team": team
            }
            # publish_message : sauvegarde en BDD ET publie sur Kafka
            # Kafka redistribuera le message à TOUTES les instances du chat service
            # (important si on scale horizontalement avec plusieurs pods K8s)
            await chat_service.publish_message(msg)

    except WebSocketDisconnect:
        # Client a fermé la connexion (onglet fermé, réseau coupé...)
        logger.info(f"Disconnected: {username} from {team}")
        chat_service.disconnect(team, websocket)  # Retire de _connections[team]
        
    except Exception as e:
        # Toute autre erreur : on déconnecte proprement
        logger.error(f"Error in chat_endpoint for {username}: {e}")
        chat_service.disconnect(team, websocket)


# =============================================================================
# WebSocket /ws/battle/{battle_id} — Chat d'une salle de bataille
# =============================================================================
# URL : ws://localhost/ws/battle/uuid-de-la-bataille?username=Betsaleel
# Chaque bataille a SA PROPRE "room" (salon de chat dédié)
@router.websocket("/ws/battle/{battle_id}")
async def battle_endpoint(battle_id: str, username: str, websocket: WebSocket):
    # On crée un identifiant de room unique pour cette bataille
    # "battle_uuid123" → tous les joueurs de cette bataille sont dans la même room
    room = f"battle_{battle_id}"
    
    await chat_service.connect(room, websocket)

    try:
        while True:
            data = await websocket.receive_text()
            try:
                # On essaie de parser en JSON (si le frontend envoie un objet structuré)
                msg = json.loads(data)
                msg["room"] = room  # On ajoute la room pour le routing Kafka
            except Exception:
                # Si c'est du texte brut, on le wrape dans un dict
                msg = {
                    "type": "chat",
                    "author": username,
                    "content": data,
                    "is_bot": False,
                    "room": room
                }
            await chat_service.publish_message(msg)
            
    except WebSocketDisconnect:
        chat_service.disconnect(room, websocket)

# =============================================================================
# FAN-OUT PATTERN — Comment un message atteint tous les clients
# =============================================================================
# 1. Joueur A envoie "Allez les rouges !" via WebSocket
# 2. chat_endpoint reçoit le message
# 3. publish_message() : 
#    a. Sauvegarde en BDD chat_db
#    b. Publie sur Kafka topic "chat-messages"
# 4. kafka_consumer_loop (dans main.py) reçoit le message du topic
# 5. broadcast() ou broadcast_all() envoie à tous les WebSocket connectés
# 6. Joueur B et Joueur C reçoivent le message en temps réel
#
# AVANTAGE : Si on a 3 instances du chat service (K8s replicas=3),
# chaque instance a ses propres connexions WebSocket, mais TOUTES reçoivent
# le message via Kafka et le redistribuent à leurs clients locaux.
