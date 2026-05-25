# =============================================================================
# GATEWAY — Dockerfile
# =============================================================================
# RÔLE : Construire l'image Docker du reverse proxy Nginx.
#
# POURQUOI NGINX EN CONTENEUR ?
# En développement, on pourrait installer Nginx directement sur la machine.
# En conteneur Docker, Nginx est :
# - Isolé (pas de conflit avec d'autres Nginx)
# - Portable (même config partout)
# - Orchestrable (K8s peut le scaler)
# =============================================================================

# nginx:alpine = image officielle Nginx basée sur Alpine Linux
# Alpine = distribution Linux ultra-légère (~5Mo vs ~200Mo pour Ubuntu)
# Avantage : image plus petite = moins de surface d'attaque, téléchargement plus rapide
FROM nginx:alpine

# Copie notre config Nginx personnalisée par-dessus la config par défaut
# /etc/nginx/nginx.conf = emplacement standard de la config principale Nginx
COPY nginx.conf /etc/nginx/nginx.conf

# Documente que ce conteneur écoute sur le port 80 (HTTP)
# EXPOSE est indicatif, le vrai mapping est dans docker-compose.yml (ports: 80:80)
EXPOSE 80

# Lance Nginx en avant-plan (daemon off)
# Par défaut Nginx se met en arrière-plan (daemon), ce qui ferait croire à Docker
# que le processus est terminé → le conteneur s'arrêterait immédiatement
CMD ["nginx", "-g", "daemon off;"]
