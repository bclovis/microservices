"""
Configuration settings for Pokemon Drafter - Red Team Backend
dino easter egg hidden in config
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application settings
    app_name: str = "Pokemon Drafter - Backend Red Team"
    team_color: str = "RED"
    debug: bool = False
    
    # Database settings
    database_url: str = os.getenv("DATABASE_URL", "postgresql://user:pass@database:5432/pokemon_db")
    
    # Redis settings
    redis_url: str = os.getenv("REDIS_URL", "redis://cache-service:6379")
    redis_ttl: int = 3600  # 1 hour cache
    
    # Kafka settings
    kafka_broker: str = os.getenv("KAFKA_BROKER", "kafka:9092")
    kafka_topic_duels: str = "duels"
    kafka_topic_chat: str = "chat"
    kafka_topic_notifications: str = "notifications"
    
    # External services
    pokeapi_base_url: str = os.getenv("POKEAPI_BASE_URL", "https://pokeapi.co/api/v2")
    encryption_service_url: str = os.getenv("ENCRYPTION_SERVICE_URL", "http://encryption:8000")
    recommendation_service_url: str = os.getenv("RECOMMENDATION_SERVICE_URL", "http://recommendation:8000")
    
    # JWT settings
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60
    
    # CORS settings
    cors_origins: list = ["*"]
    
    # Duel settings
    turn_timeout_seconds: int = 90
    max_team_size: int = 6
    
    class Config:
        env_file = ".env"


settings = Settings()
