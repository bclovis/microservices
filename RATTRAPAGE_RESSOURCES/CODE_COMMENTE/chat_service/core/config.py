# =============================================================================
# CHAT SERVICE — core/config.py
# Configuration centralisée du Chat Service via variables d'environnement
# =============================================================================
# RÔLE DU FICHIER :
# Centralise toute la configuration du service.
# Les valeurs viennent soit du fichier .env (dev), soit des variables d'environnement
# (Docker Compose / Kubernetes).
#
# DEUX TOPICS KAFKA DANS CE SERVICE :
# - KAFKA_TOPIC_BATTLE : "battle-events" → le chat CONSOMME ce topic
#   (pour recevoir les résultats de tours et les broadcaster dans le chat)
# - KAFKA_TOPIC_CHAT   : "chat-messages" → le chat PRODUIT sur ce topic
#   (pour distribuer les messages entre instances du service)
# =============================================================================

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Lit depuis .env en premier, ensuite les variables d'environnement système
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "PokeDrafter — Chat Service"
    DEBUG: bool = False  # False en prod, True localement pour voir les requêtes SQL

    # URL de connexion à la base de données du chat
    # asyncpg = driver asynchrone PostgreSQL (nécessaire pour SQLAlchemy async)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/chat_db"

    # Adresse du broker Kafka
    # En Docker Compose/K8s : "kafka:29092" (résolution DNS interne)
    # En local sans Docker : "localhost:9092"
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:29092"

    # Topic sur lequel le Chat Service PUBLIE les messages de chat
    KAFKA_TOPIC_CHAT: str = "chat-messages"

    # Topic sur lequel le Chat Service ÉCOUTE les événements du combat
    # Quand battle_service publie un résultat de tour → chat service le reçoit
    # et le broadcast en temps réel dans le chat de la room de bataille
    KAFKA_TOPIC_BATTLE: str = "battle-events"


# Instance singleton utilisée dans toute l'application
settings = Settings()
