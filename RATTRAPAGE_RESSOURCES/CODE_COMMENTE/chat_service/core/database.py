# =============================================================================
# CHAT SERVICE — core/database.py
# Connexion asynchrone à PostgreSQL (base chat_db)
# =============================================================================
# RÔLE DU FICHIER :
# Identique à battle_service/core/database.py mais pour la base chat_db.
# Gère la connexion SQLAlchemy async vers PostgreSQL pour persister les messages.
# =============================================================================

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# Moteur de connexion async (pool de connexions PostgreSQL)
engine = create_async_engine(
    settings.DATABASE_URL,   # "postgresql+asyncpg://..."
    echo=settings.DEBUG,     # True = affiche toutes les requêtes SQL (debug uniquement)
    future=True              # Active le mode SQLAlchemy 2.0 (API moderne)
)

# Factory de sessions (AsyncSession = session pour exécuter des requêtes async)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False   # Les objets restent utilisables après commit (pas de rechargement auto)
)


# Classe de base pour tous les modèles SQLAlchemy du chat service
class Base(DeclarativeBase):
    pass


# Crée toutes les tables définies dans les modèles (si elles n'existent pas)
async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)  # run_sync car create_all est synchrone


# Dépendance FastAPI : fournit une session DB à chaque requête et la ferme automatiquement
# Utilisé avec Depends(get_db) dans les routes
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
        # Le "async with" ferme la session automatiquement à la fin de la requête
