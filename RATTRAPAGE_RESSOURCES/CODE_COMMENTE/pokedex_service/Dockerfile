# =============================================================================
# POKEDEX SERVICE — Dockerfile
# =============================================================================
# RÔLE : Empaquette le Pokédex Service Python dans une image Docker autonome.
# Port exposé : 8004
# Même structure que le Chat Service Dockerfile, port différent.
# =============================================================================

FROM python:3.12-slim

WORKDIR /app

# requirements.txt en premier pour maximiser le cache Docker
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app

EXPOSE 8004

# app.main:app = le module app/main.py, variable app (instance FastAPI)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8004"]
