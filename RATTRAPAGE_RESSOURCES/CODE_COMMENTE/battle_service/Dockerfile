# =============================================================================
# BATTLE SERVICE — Dockerfile
# Instructions pour construire l'image Docker du Battle Service
# =============================================================================
# RÔLE DU FICHIER :
# Le Dockerfile décrit comment "packager" l'application Python dans une image Docker.
# C'est une suite d'instructions qui s'exécutent de haut en bas lors du "docker build".
# Chaque instruction crée un LAYER (couche) dans l'image finale.
# =============================================================================

# FROM python:3.12-slim
# ─────────────────────
# Image de base officielle Python 3.12 en version "slim"
# slim = version allégée de Debian, sans les outils de développement (gcc, make, etc.)
# Avantage : image plus petite (~200MB vs ~900MB pour python:3.12)
# python:3.12 = version LTS stable avec toutes les dernières fonctionnalités async

FROM python:3.12-slim

# WORKDIR /app
# ─────────────
# Définit le répertoire de travail à l'intérieur du container
# Toutes les commandes suivantes (COPY, RUN, CMD) s'exécutent depuis /app
# Crée le répertoire s'il n'existe pas
WORKDIR /app

# COPY requirements.txt .
# ────────────────────────
# Copie SEULEMENT requirements.txt (pas tout le code) d'abord
# POURQUOI ? Optimisation du cache Docker :
# Si le code source change mais pas requirements.txt → Docker réutilise le layer pip
# Si on copiait tout d'un coup, n'importe quel changement de code relancerait pip install
COPY requirements.txt .

# RUN pip install --no-cache-dir -r requirements.txt
# ──────────────────────────────────────────────────
# Installe toutes les dépendances Python listées dans requirements.txt
# --no-cache-dir : ne garde pas le cache pip dans l'image → image plus légère
# Packages installés pour battle_service :
#   fastapi==0.111.0           → framework web
#   uvicorn[standard]==0.30.0  → serveur ASGI
#   pydantic==2.7.0            → validation des données
#   pydantic-settings==2.3.0   → lecture des variables d'environnement
#   sqlalchemy[asyncio]==2.0.31 → ORM async
#   asyncpg==0.29.0            → driver PostgreSQL async
#   aiokafka==0.10.0           → client Kafka async
#   python-jose[cryptography]  → gestion JWT
#   httpx==0.27.0              → client HTTP async
RUN pip install --no-cache-dir -r requirements.txt

# COPY ./app ./app
# ─────────────────
# Copie le dossier "app/" (le code source) dans /app/app/ du container
# On copie le code APRÈS les dépendances pour profiter du cache Docker
# Structure finale dans le container : /app/app/main.py, /app/app/routes/..., etc.
COPY ./app ./app

# EXPOSE 8003
# ────────────
# Déclare que le container écoute sur le port 8003
# C'est DOCUMENTAIRE uniquement : ça n'ouvre pas le port automatiquement
# Le vrai mapping de port se fait dans docker-compose.yml (ports: "8003:8000")
# ATTENTION : uvicorn tourne sur 8003 DANS le container, mais docker-compose
# mappe ce port interne sur 8003 côté hôte (d'où les ports: "8003:8000" → bug connu)
EXPOSE 8003

# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]
# ────────────────────────────────────────────────────────────────────────
# Commande lancée quand le container démarre
# uvicorn = serveur ASGI (Asynchronous Server Gateway Interface)
# app.main:app = module "app.main", objet "app" (notre instance FastAPI)
# --host 0.0.0.0 = écoute sur TOUTES les interfaces réseau du container
#   (pas juste localhost, sinon inaccessible depuis l'extérieur du container)
# --port 8003 = port d'écoute du serveur
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]

# =============================================================================
# POURQUOI PAS "--reload" EN PROD ?
# =============================================================================
# En développement on ajouterait "--reload" pour recharger automatiquement
# le code à chaque modification. En prod/Docker, on ne veut pas ça :
# - Sécurité : on ne devrait pas modifier le code dans le container
# - Performance : le mode reload surveille le filesystem = CPU inutile
