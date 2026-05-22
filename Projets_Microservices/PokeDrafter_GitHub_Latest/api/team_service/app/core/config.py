from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    PROJECT_NAME: str = "PokeDrafter — Team Service"
    DEBUG: bool = False
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/team_db"
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    POKEDEX_SERVICE_URL: str = "http://localhost:8004"
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"

settings = Settings()