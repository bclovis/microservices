# =============================================================================
# BATTLE SERVICE — core/database.py
# Configuration de la connexion asynchrone à PostgreSQL via SQLAlchemy
# =============================================================================

# SQLAlchemy Async : bibliothèque ORM (Object-Relational Mapping)
# ORM = on manipule des objets Python au lieu d'écrire du SQL brut
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# DeclarativeBase : classe de base dont héritent tous nos modèles SQLAlchemy
# Chaque classe Python qui hérite de Base correspond à une table SQL
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


# =============================================================================
# MOTEUR DE BASE DE DONNÉES (ENGINE)
# =============================================================================
# create_async_engine crée la connexion "pool" vers PostgreSQL
# - settings.DATABASE_URL : l'URL de connexion (ex: postgresql+asyncpg://...)
# - echo=settings.DEBUG : si True, toutes les requêtes SQL sont affichées dans les logs
# - future=True : utilise l'API SQLAlchemy 2.0 (plus moderne)
engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG, future=True)


# =============================================================================
# FABRIQUE DE SESSIONS
# =============================================================================
# async_sessionmaker crée des sessions de base de données à la demande
# Une session = une "transaction" avec la BDD
# - bind=engine : utilise notre engine configuré
# - class_=AsyncSession : sessions asynchrones (non-bloquantes)
# - expire_on_commit=False : après un commit, les objets restent accessibles
#   sans refaire une requête SQL (important en async !)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# =============================================================================
# CLASSE DE BASE DES MODÈLES
# =============================================================================
# Tous les modèles (Battle, BattleTurn) héritent de Base
# SQLAlchemy utilise Base.metadata pour connaître toutes les tables à créer
class Base(DeclarativeBase):
    pass


# =============================================================================
# CRÉATION DES TABLES AU DÉMARRAGE
# =============================================================================
async def init_db() -> None:
    # engine.begin() ouvre une connexion et une transaction
    async with engine.begin() as conn:
        # Base.metadata.create_all : crée toutes les tables définies dans les modèles
        # run_sync() est nécessaire car create_all n'est pas async nativement
        # Si une table existe déjà → elle est ignorée (CREATE TABLE IF NOT EXISTS)
        await conn.run_sync(Base.metadata.create_all)


# =============================================================================
# DÉPENDANCE FASTAPI : GET_DB
# =============================================================================
# Fonction génératrice (yield) utilisée comme dépendance FastAPI
# Pattern classique : inject une session dans chaque route qui en a besoin
# 
# Utilisation dans une route :
#   @router.post("/")
#   async def create(db: AsyncSession = Depends(get_db)):
#       db.add(...)
#       await db.commit()
async def get_db():
    # "async with" garantit que la session est fermée même en cas d'exception
    async with AsyncSessionLocal() as session:
        yield session  # FastAPI injecte cette session dans la fonction de route

# =============================================================================
# POURQUOI ASYNC ?
# =============================================================================
# asyncpg (driver PostgreSQL async) permet d'envoyer des requêtes SQL sans bloquer
# le thread principal. FastAPI peut ainsi traiter d'AUTRES requêtes HTTP pendant
# qu'on attend la réponse de PostgreSQL.
# Résultat : bien meilleure performance sous charge sans avoir besoin de threads.
