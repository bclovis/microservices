# =============================================================================
# POKEDEX SERVICE — core/config.py
# Configuration centralisée du Pokédex Service
# =============================================================================
# RÔLE DU FICHIER :
# Centralise toute la configuration du service.
# Ce service est le plus simple : pas de Kafka, pas de BDD propre.
# Il a juste besoin de Redis (cache) et l'URL de l'API externe PokeAPI.
# =============================================================================

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "PokeDrafter — Pokédex Service"
    DEBUG: bool = False

    # URL du serveur Redis (cache)
    # En Docker Compose/K8s : "redis://redis:6379/0"
    # En local : "redis://localhost:6379/0"
    # /0 = base de données Redis numéro 0 (Redis peut avoir plusieurs "databases" 0-15)
    REDIS_URL: str = "redis://localhost:6379/0"

    # URL de base de l'API publique Pokémon
    # Cette API est gratuite, sans clé, mais limitée en débit (100 req/min)
    # D'où l'importance du cache Redis pour ne pas la spammer
    POKEAPI_BASE_URL: str = "https://pokeapi.co/api/v2"

    # Durée de vie du cache en secondes
    # 86400 secondes = 24 heures = 1 journée
    # Les données Pokémon changent très rarement → TTL long est approprié
    POKEAPI_CACHE_TTL: int = 86400


settings = Settings()
