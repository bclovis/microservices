# =============================================================================
# BATTLE SERVICE — main.py
# Point d'entrée de l'application FastAPI du service de bataille
# =============================================================================

# asynccontextmanager : décorateur Python pour créer un "context manager" asynchrone
# On l'utilise pour le cycle de vie (startup / shutdown) de l'app
from contextlib import asynccontextmanager

# FastAPI : le framework web asynchrone principal
from fastapi import FastAPI

# CORSMiddleware : middleware qui ajoute les headers CORS aux réponses HTTP
# CORS = Cross-Origin Resource Sharing : autorise le frontend (Angular :4300) à appeler ce service
from fastapi.middleware.cors import CORSMiddleware

# On importe l'objet "settings" qui lit la config depuis les variables d'environnement
from app.core.config import settings

# init_db() : fonction qui crée les tables SQL au démarrage si elles n'existent pas
from app.core.database import init_db

# Le routeur qui contient toutes les routes /battles/*
from app.routes.battle import router as battle_router


# =============================================================================
# LIFESPAN — Gestion du cycle de vie de l'application
# =============================================================================
# @asynccontextmanager transforme cette fonction en gestionnaire de contexte async
# FastAPI exécute tout ce qui est AVANT le "yield" au démarrage
# et tout ce qui est APRÈS le "yield" à l'arrêt
@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP : créer les tables en base de données
    # Si les tables existent déjà, SQLAlchemy ne les recrée pas (CREATE TABLE IF NOT EXISTS)
    await init_db()
    
    yield  # <-- ici l'app tourne et répond aux requêtes
    
    # SHUTDOWN : rien à faire ici pour battle_service
    # (kafka producer est géré dans kafka_service.py)


# =============================================================================
# CRÉATION DE L'APPLICATION FASTAPI
# =============================================================================
app = FastAPI(
    title=settings.PROJECT_NAME,  # Nom affiché dans la doc Swagger (/docs)
    version="1.0.0",
    docs_url="/docs",             # URL de la documentation interactive Swagger UI
    lifespan=lifespan,            # On passe notre gestionnaire de cycle de vie
)


# =============================================================================
# CORS MIDDLEWARE
# =============================================================================
# Sans ce middleware, le navigateur bloquerait les requêtes du frontend Angular
# vers ce service (politique Same-Origin)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # En prod, on mettrait l'URL exacte du frontend
    allow_credentials=True,       # Autorise les cookies/tokens dans les requêtes cross-origin
    allow_methods=["*"],          # Autorise tous les verbes HTTP : GET, POST, PUT, DELETE...
    allow_headers=["*"],          # Autorise tous les headers, notamment "Authorization" pour le JWT
)


# =============================================================================
# ENREGISTREMENT DES ROUTES
# =============================================================================
# prefix="/api/battle" : toutes les routes du routeur seront préfixées
# Ex: @router.get("/battles") devient accessible sur /api/battle/battles
# C'est ce chemin que nginx proxifie dans gateway/nginx.conf :
#   location /api/battle { proxy_pass http://battle_service/api/battle; }
app.include_router(battle_router, prefix="/api/battle")


# =============================================================================
# ROUTE DE SANTÉ (HEALTH CHECK)
# =============================================================================
# Route GET /health utilisée par Docker/K8s pour vérifier que le service est vivant
# Docker Compose et K8s peuvent redémarrer automatiquement si ce endpoint échoue
@app.get("/health", tags=["health"])
async def health():
    # Réponse simple : le service est up et s'identifie
    return {"status": "ok", "service": "battle"}

# =============================================================================
# POURQUOI ASYNC ?
# =============================================================================
# Toutes les fonctions sont "async def" car on fait des I/O :
#   - requêtes vers PostgreSQL (asyncpg)
#   - envoi d'events à Kafka (aiokafka)
# Le mode async permet de traiter plusieurs requêtes en parallèle SANS threads
# C'est la grande force de FastAPI + Python async
