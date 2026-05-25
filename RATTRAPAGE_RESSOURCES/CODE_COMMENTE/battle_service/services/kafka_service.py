# =============================================================================
# BATTLE SERVICE — services/kafka_service.py
# Producteur Kafka : publication d'événements de bataille en asynchrone
# =============================================================================
# RÔLE DU FICHIER :
# Ce fichier est responsable d'envoyer des événements Kafka chaque fois qu'un
# tour est joué ou qu'une bataille se termine.
# Le chat_service CONSOMME ces événements pour afficher les résultats en temps réel.
# IMPORTANT : Kafka est OPTIONNEL. Si Kafka est down, la bataille continue quand même.
# =============================================================================

import json      # Pour sérialiser les messages Python en JSON avant envoi Kafka
import logging   # Pour logger les erreurs sans crasher le service

# AIOKafkaProducer : producteur Kafka asynchrone (compatible asyncio)
# "aio" = asyncio. On utilise le driver async pour ne pas bloquer le serveur FastAPI
from aiokafka import AIOKafkaProducer

from app.core.config import settings  # Pour lire KAFKA_BOOTSTRAP_SERVERS et KAFKA_TOPIC_BATTLE

# Logger nommé par module : dans les logs, on voit "battle_service.services.kafka_service"
logger = logging.getLogger(__name__)


# =============================================================================
# SINGLETON DU PRODUCTEUR KAFKA
# =============================================================================
# Variable globale au niveau du MODULE (pas d'une classe)
# _producer vaut None au démarrage, puis est instancié au premier appel
# 
# POURQUOI UN SINGLETON ?
# Créer un AIOKafkaProducer est COÛTEUX : il établit une connexion TCP avec le broker
# et négocie des paramètres de session. Le réutiliser à chaque requête serait un
# gaspillage de ressources énorme. On crée donc UN SEUL producteur pour toute la vie
# de l'application.
_producer: AIOKafkaProducer | None = None


# =============================================================================
# FONCTION : get_producer — Accès au singleton (lazy initialization)
# =============================================================================
async def get_producer() -> AIOKafkaProducer:
    global _producer  # Nécessaire pour MODIFIER la variable globale du module
    
    if _producer is None:
        # Première fois : on crée et démarre le producteur
        p = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            # value_serializer : fonction appelée avant chaque envoi
            # Elle convertit notre dict Python → bytes JSON
            # lambda v: = fonction anonyme, v = la valeur à sérialiser
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        # p.start() : établit la connexion TCP avec le broker Kafka
        # C'est une opération async (réseau) → on l'attend
        await p.start()
        _producer = p  # On stocke dans le singleton pour les prochains appels
    
    return _producer  # Retourne toujours le même objet


# =============================================================================
# FONCTION : publish_battle_event — Publier un événement de bataille
# =============================================================================
async def publish_battle_event(event_type: str, data: dict) -> None:
    global _producer
    try:
        # Récupère (ou crée) le singleton producteur
        producer = await get_producer()
        
        # On construit le payload complet : type + toutes les données du tour
        # L'opérateur **data "déplie" le dict : {"a":1, "b":2} → a=1, b=2
        payload = {"type": event_type, **data}
        # Exemple de payload :
        # {
        #   "type": "turn_played",
        #   "battle_id": "uuid...",
        #   "turn_number": 3,
        #   "pokemon_red": "Dracaufeu",
        #   "pokemon_blue": "Blastoise",
        #   "score_red": "8.0",
        #   "score_blue": "0.5",
        #   "result": "A"
        # }
        
        # send_and_wait : envoie le message ET attend la confirmation du broker
        # (que le message a bien été écrit dans le log Kafka)
        # settings.KAFKA_TOPIC_BATTLE = "battle-events"
        await producer.send_and_wait(settings.KAFKA_TOPIC_BATTLE, payload)
        
    except Exception as exc:
        # =================================================================
        # GESTION D'ERREUR — Le service ne crashe PAS si Kafka est down
        # =================================================================
        # On reset le singleton : au prochain appel, on essaiera de se reconnecter
        _producer = None
        # On LOG un warning (pas une erreur critique) pour ne pas remplir les logs
        logger.warning("Kafka unavailable, event dropped: %s", exc)
        # ON NE FAIT PAS "raise exc" → l'erreur est silencieuse pour le reste du code
        # Conséquence : le tour est joué normalement, seul l'event temps réel est perdu
        
        # QUESTION PIÈGE "Pourquoi pas raise ?"
        # Kafka est un "nice to have" : si le chat temps réel ne fonctionne pas,
        # la bataille doit quand même avancer. On a séparé la logique métier (tour joué)
        # de la diffusion temps réel (Kafka). C'est un design choix de résilience.


# =============================================================================
# FONCTION : stop_producer — Fermer proprement la connexion
# =============================================================================
async def stop_producer() -> None:
    global _producer
    if _producer:
        # Ferme proprement la connexion TCP avec Kafka
        # Envoie les messages en attente avant de fermer (graceful shutdown)
        await _producer.stop()
        _producer = None  # Remet le singleton à None

# =============================================================================
# FLUX COMPLET D'UN ÉVÉNEMENT KAFKA
# =============================================================================
# 1. Joueur joue un tour → POST /api/battle/battles/{id}/turn
# 2. routes/battle.py appelle publish_battle_event("turn_played", {...})
# 3. kafka_service envoie le message sur le topic "battle-events"
# 4. chat_service (qui est ABONNÉ à ce topic) reçoit le message
# 5. chat_service fait un broadcast WebSocket à tous les clients connectés
# 6. Le frontend Angular affiche "Tour 3 — Rouge remporte le tour !"
