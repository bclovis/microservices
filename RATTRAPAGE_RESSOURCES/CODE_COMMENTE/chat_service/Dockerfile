# =============================================================================
# CHAT SERVICE — Dockerfile
# =============================================================================
# RÔLE : Empaquette le Chat Service Python dans une image Docker autonome.
# Port exposé : 8005 (chaque service a son propre port pour éviter les conflits)
# =============================================================================

# Image de base Python 3.12 minimaliste (sans outils de développement)
FROM python:3.12-slim

# Dossier de travail dans le container
WORKDIR /app

# COPIER requirements.txt EN PREMIER (avant le code source)
# Docker met en cache chaque layer. Si requirements.txt ne change pas,
# "pip install" n'est pas réexécuté même si le code change.
# Cette optimisation accélère considérablement les rebuilds.
COPY requirements.txt .

# Installe les dépendances Python
# --no-cache-dir : ne garde pas le cache pip dans l'image (réduit la taille)
RUN pip install --no-cache-dir -r requirements.txt

# Copie le code source de l'application
COPY ./app ./app

# Documente le port d'écoute (informatif)
EXPOSE 8005

# Lance uvicorn au démarrage du container
# app.main:app = le module app.main, la variable "app" (instance FastAPI)
# --host 0.0.0.0 = écoute sur toutes les interfaces (nécessaire en container)
# --port 8005 = port du Chat Service (conventionnel, doit correspondre à docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8005"]
