# =============================================================================
# BATTLE SERVICE — core/config.py
# Gestion de la configuration via variables d'environnement
# =============================================================================

# BaseSettings : classe Pydantic qui lit automatiquement les variables d'environnement
# Avantage : on ne met JAMAIS de secrets hardcodés dans le code
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # SettingsConfigDict définit comment Pydantic lit la config
    model_config = SettingsConfigDict(
        env_file=".env",   # Cherche un fichier .env en local (utile en dev)
        extra="ignore"     # Ignore les variables d'env inconnues (ne plante pas)
    )

    # Nom du projet affiché dans la doc Swagger
    PROJECT_NAME: str = "PokeDrafter — Battle Service"
    
    # Mode debug : si True, SQLAlchemy affiche toutes les requêtes SQL dans les logs
    DEBUG: bool = False

    # URL de connexion à PostgreSQL
    # Format : driver://user:password@host:port/database
    # "postgresql+asyncpg" = PostgreSQL avec le driver async (asyncpg)
    # En Docker, "postgres" est le nom du service Docker Compose → résolution DNS automatique
    # En dehors de Docker, on utiliserait "localhost"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/battle_db"

    # Clé secrète pour signer/vérifier les JWT
    # ⚠️ En prod, cette valeur doit être une vraie clé aléatoire longue
    # Elle est injectée via la variable d'env JWT_SECRET dans docker-compose.yml
    JWT_SECRET: str = "change-me-in-production"
    
    # Algorithme de signature JWT : HS256 = HMAC-SHA256 (symétrique, clé partagée)
    JWT_ALGORITHM: str = "HS256"

    # Timeout par tour de jeu (en secondes)
    # Si un joueur ne joue pas en 90s, on pourrait implémenter un forfait auto
    TURN_TIMEOUT: int = 90

    # Adresse du broker Kafka
    # "kafka:29092" = nom de service Docker + port interne
    # On utilise le port 29092 (PLAINTEXT interne) et pas 9092 (exposé à l'hôte)
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:29092"
    
    # Nom du topic Kafka où battle_service publie ses events
    # battle_service PRODUIT sur ce topic
    # chat_service CONSOMME ce topic pour afficher les résultats en temps réel
    KAFKA_TOPIC_BATTLE: str = "battle-events"


# Instanciation unique (pattern module singleton)
# Ce module est importé partout → settings est créé une seule fois en mémoire
settings = Settings()

# =============================================================================
# POURQUOI PYDANTIC SETTINGS ?
# =============================================================================
# 1. Typage fort : si DATABASE_URL n'est pas une str, Pydantic lève une erreur au démarrage
# 2. Priorité : env variable > .env file > valeur par défaut
# 3. Sécurité : on ne met pas les secrets dans le code source (git)
# 4. En docker-compose, on passe les variables via la section "environment:"
