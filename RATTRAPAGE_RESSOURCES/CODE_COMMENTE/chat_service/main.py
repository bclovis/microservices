# =============================================================================
# CHAT SERVICE — main.py
# Point d'entrée : gestion du cycle de vie, consumer Kafka en tâche de fond
# =============================================================================
# RÔLE DU FICHIER :
# Ce fichier est le plus complexe du chat service car il orchestre trois choses :
# 1. Le démarrage de l'application FastAPI (comme tout service)
# 2. Le lancement d'un consumer Kafka en arrière-plan (tâche asyncio)
# 3. La gestion gracieuse de l'arrêt (annulation de la tâche, fermeture du producer)
#
# ARCHITECTURE DU CHAT :
# ┌──────────────────────────────────────────────┐
# │           Chat Service                        │
# │                                              │
# │  [HTTP]  GET /api/chat/history              │
# │  [WS]    /ws/chat/{team}     ←→ clients     │
# │  [WS]    /ws/battle/{id}     ←→ clients     │
# │                                              │
# │  [Kafka Consumer] ← battle-events           │
# │  [Kafka Consumer] ← chat-messages           │
# │  [Kafka Producer] → chat-messages           │
# └──────────────────────────────────────────────┘
# =============================================================================

import asyncio    # Pour créer des tâches asyncio en arrière-plan
import json       # Pour désérialiser les messages Kafka (bytes → dict)
import logging    # Pour les logs
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.routes.chat import router as chat_router
from app.services import chat_service  # Le module de gestion des connexions WebSocket

logger = logging.getLogger(__name__)


# =============================================================================
# KAFKA CONSUMER LOOP — Boucle infinie qui lit les messages Kafka
# =============================================================================
async def kafka_consumer_loop():
    """
    Tâche asyncio lancée au démarrage du service.
    S'abonne à DEUX topics Kafka et dispatche les messages aux clients WebSocket.
    Implémente une reconnexion automatique avec backoff exponentiel.
    """
    retry_delay = 2  # Délai initial de reconnexion en secondes
    
    while True:  # Boucle infinie = le consumer tourne toute la vie du service
        # On crée un nouveau consumer à chaque tentative de connexion
        # (si Kafka est down au démarrage, on réessaie)
        consumer = AIOKafkaConsumer(
            settings.KAFKA_TOPIC_BATTLE,  # "battle-events" → résultats de tours
            settings.KAFKA_TOPIC_CHAT,    # "chat-messages" → messages des joueurs
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            # value_deserializer : fonction inverse du serializer du producer
            # bytes → str → dict Python
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            # auto_offset_reset="latest" : ne lit que les NOUVEAUX messages
            # (ne relit pas l'historique Kafka au redémarrage)
            # Alternative "earliest" = tout relire depuis le début (non voulu ici)
            auto_offset_reset="latest",
        )
        try:
            await consumer.start()  # Connexion au broker Kafka
            logger.info("[Kafka] Consumer connected to %s and %s",
                        settings.KAFKA_TOPIC_BATTLE, settings.KAFKA_TOPIC_CHAT)
            retry_delay = 2  # Reset du délai si connexion réussie
            
            # "async for msg in consumer" : boucle qui reçoit les messages au fil de l'eau
            # msg.value = le dict Python (après désérialisation)
            # msg.topic = quel topic a produit ce message
            async for msg in consumer:
                event = msg.value
                topic = msg.topic

                # === TRAITEMENT DES EVENTS DE BATAILLE ===
                if topic == settings.KAFKA_TOPIC_BATTLE:
                    etype = event.get("type", "")
                    if etype == "turn_played":
                        # On construit un message de notification "bot"
                        result = event.get("result", "?")
                        turn = event.get("turn_number", "?")
                        # Traduction du résultat en texte lisible
                        winner = "Rouge" if result == "A" else ("Bleu" if result == "B" else "Egalité")
                        notif = {
                            "author": "bot",       # Message système, pas d'un joueur
                            "content": f"Tour {turn} — {winner} remporte le tour !",
                            "is_bot": True         # Le frontend peut styliser différemment
                        }
                        logger.info("[Kafka] Battle Event -> broadcast_all")
                        # broadcast_all = envoie à toutes les équipes (red et blue)
                        await chat_service.broadcast_all(notif)

                # === TRAITEMENT DES MESSAGES DE CHAT ===
                elif topic == settings.KAFKA_TOPIC_CHAT:
                    room = event.get("room")
                    if room:
                        # Message pour une salle de bataille spécifique
                        await chat_service.broadcast(room, event)
                    else:
                        # Message global (chat principal) → toutes les équipes
                        await chat_service.broadcast_all(event)

        except asyncio.CancelledError:
            # La tâche a été annulée proprement (au shutdown de l'app)
            await consumer.stop()
            return  # On sort de la boucle = fin propre de la tâche
            
        except Exception as e:
            # Kafka indisponible : on logue et on réessaie
            logger.warning("Kafka unavailable, retrying in %ds : %s", retry_delay, e)
            await asyncio.sleep(retry_delay)  # Attente avant retry
            # Backoff exponentiel : 2s → 4s → 8s → 16s → 30s max
            # Évite de spammer le broker avec des connexions si Kafka est surchargé
            retry_delay = min(retry_delay * 2, 30)
            
        finally:
            # On s'assure de fermer le consumer même en cas d'exception
            try:
                await consumer.stop()
            except Exception:
                pass  # Si le consumer n'était pas démarré, on ignore l'erreur


# =============================================================================
# LIFESPAN — Démarrage et arrêt de l'application
# =============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    await init_db()  # Crée les tables SQL si elles n'existent pas
    
    # Démarre le consumer Kafka en TÂCHE DE FOND (non-bloquant)
    # asyncio.create_task() lance kafka_consumer_loop() sans attendre qu'elle finisse
    # L'application continue de démarrer et de répondre aux requêtes HTTP
    task = asyncio.create_task(kafka_consumer_loop())
    
    yield  # L'application tourne ici
    
    # SHUTDOWN : arrêt propre
    task.cancel()  # Annule la tâche Kafka (déclenche asyncio.CancelledError dans la boucle)
    await chat_service.stop_producer()  # Ferme le producer Kafka


# =============================================================================
# APPLICATION FASTAPI
# =============================================================================
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    docs_url="/docs",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Les routes WebSocket ET REST sont dans le même routeur
app.include_router(chat_router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "service": "chat"}

# =============================================================================
# POURQUOI UNE TÂCHE DE FOND ET PAS UN WORKER SÉPARÉ ?
# =============================================================================
# On aurait pu faire un microservice séparé juste pour consumer Kafka.
# Mais ça aurait compliqué l'architecture : le consumer a besoin d'accès aux
# connexions WebSocket (chat_service._connections), donc il doit tourner dans
# le même processus. asyncio.create_task() est la solution la plus simple.
