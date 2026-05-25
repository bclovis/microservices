# =============================================================================
# POKEDEX SERVICE — main.py
# =============================================================================
# RÔLE DU FICHIER : Point d'entrée du service Pokédex.
# Ce service est le plus simple de l'architecture : pas de BDD, pas de Kafka.
# Il expose une API REST qui proxifie PokeAPI avec un cache Redis.
# =============================================================================
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.cache import close_redis     # Pour fermer proprement la connexion Redis
from app.core.config import settings
from app.routes.pokedex import router as pokedex_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield  # Pas de setup au démarrage (Redis se connecte lazy, à la première requête)
    # SHUTDOWN : on ferme proprement le pool de connexions Redis
    await close_redis()

app = FastAPI(title=settings.PROJECT_NAME, version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pokedex_router)

@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "service": "pokedex"}
