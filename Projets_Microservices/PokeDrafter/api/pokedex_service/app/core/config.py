from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    PROJECT_NAME: str = "PokeDrafter — Pokédex Service"
    DEBUG: bool = False
    REDIS_URL: str = "redis://localhost:6379/0"
    POKEAPI_BASE_URL: str = "https://pokeapi.co/api/v2"
    POKEAPI_CACHE_TTL: int = 86400

settings = Settings()