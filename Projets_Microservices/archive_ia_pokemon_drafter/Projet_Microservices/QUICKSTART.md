# Quick Start Guide - Pokemon Drafter

## 🚀 Démarrage Rapide

### Option 1: Développement Local (Docker Compose)

```bash
# 1. Cloner le projet
git clone https://github.com/bclovis/Projet_Microservices.git
cd Projet_Microservices

# 2. Démarrer l'environnement
make dev-up

# 3. Accéder à l'application
# Frontend Red:  http://localhost:4201
# Frontend Blue: http://localhost:4202
# API Gateway:   http://localhost:8080

# 4. Arrêter l'environnement
make dev-down
```

### Option 2: Production Kubernetes

```bash
# 1. Prérequis
# - Docker installé
# - Kubernetes (minikube) démarré
# - kubectl configuré

# 2. Configurer DNS local
sudo nano /etc/hosts
# Ajouter:
# 127.0.0.1 pokemon-drafter.local
# 127.0.0.1 red.pokemon-drafter.local
# 127.0.0.1 blue.pokemon-drafter.local

# 3. Build et déployer
make setup

# Ou étape par étape:
make build   # Construire images Docker
make deploy  # Déployer sur Kubernetes

# 4. Vérifier le statut
make status

# 5. Accéder à l'application
# http://pokemon-drafter.local
# http://red.pokemon-drafter.local
# http://blue.pokemon-drafter.local
```

## 📋 Commandes Principales

### Makefile
```bash
make help         # Afficher toutes les commandes
make dev-up       # Démarrer environnement dev
make dev-down     # Arrêter environnement dev
make build        # Construire images Docker
make deploy       # Déployer Kubernetes
make clean        # Nettoyer déploiement
make test         # Lancer tous les tests
make status       # Voir statut du déploiement
make logs         # Voir les logs
```

### Scripts
```bash
./build-images.sh   # Construire toutes les images
./deploy.sh         # Déployer sur Kubernetes
./cleanup.sh        # Nettoyer le déploiement
```

### Docker Compose
```bash
docker-compose up -d              # Démarrer
docker-compose down               # Arrêter
docker-compose logs -f            # Logs temps réel
docker-compose ps                 # Voir les services
docker-compose restart <service>  # Redémarrer un service
```

### Kubernetes
```bash
# Pods
kubectl get pods -n pokemon-drafter
kubectl logs <pod-name> -n pokemon-drafter
kubectl describe pod <pod-name> -n pokemon-drafter

# Services
kubectl get services -n pokemon-drafter
kubectl get deployments -n pokemon-drafter

# Database
kubectl exec -it deployment/database -n pokemon-drafter -- psql -U pokemon_user -d pokemon_db
```

## 🔑 Comptes de Test

### Utilisateurs Rouge
| Pseudo | Email | Mot de passe |
|--------|-------|--------------|
| red_player1 | red1@pokemon.com | RedPass123! |
| red_player2 | red2@pokemon.com | RedPass123! |

### Utilisateurs Bleu
| Pseudo | Email | Mot de passe |
|--------|-------|--------------|
| blue_player1 | blue1@pokemon.com | BluePass123! |
| blue_player2 | blue2@pokemon.com | BluePass123! |

### Admin
| Pseudo | Email | Mot de passe |
|--------|-------|--------------|
| admin | admin@pokemon.com | AdminPass123! |

## 📊 Ports des Services

### Développement (Docker Compose)
| Service | Port |
|---------|------|
| Frontend Red | 4201 |
| Frontend Blue | 4202 |
| Backend Red | 8001 |
| Backend Blue | 8002 |
| Recommendation | 8004 |
| Encryption | 8003 |
| API Gateway | 8080 |
| PostgreSQL | 5432 |
| Redis | 6379 |
| Kafka | 9092 |

### Production (Kubernetes)
Accès via API Gateway:
- Port NodePort: 30080
- DNS: pokemon-drafter.local

## 🏗️ Structure du Projet

```
Projet_Microservices/
├── api-gateway/          # Nginx reverse proxy
├── backend-red/          # FastAPI équipe rouge
├── backend-blue/         # FastAPI équipe bleue
├── frontend-red/         # Angular équipe rouge
├── frontend-blue/        # Angular équipe bleue
├── database/             # Schéma PostgreSQL
├── recommendation/       # Engine de recommandation
├── encryption/           # Service de chiffrement
├── k8s/                  # Fichiers Kubernetes
├── docs/                 # Documentation
├── docker-compose.yml    # Config développement
├── Makefile             # Commandes utiles
└── README.md            # Documentation principale
```

## 🧪 Tests

### Frontend
```bash
cd frontend-red
npm test              # Tests unitaires
npm test -- --watch   # Mode watch
```

### Backend
```bash
cd backend-red
pytest                # Tous les tests
pytest -v            # Verbose
pytest tests/test_specific.py  # Test spécifique
```

## 🐛 Troubleshooting

### "Cannot connect to database"
```bash
# Vérifier que PostgreSQL est lancé
docker-compose ps database
# Redémarrer si nécessaire
docker-compose restart database
```

### "Port already in use"
```bash
# Trouver le process utilisant le port
lsof -i :8080
# Tuer le process
kill -9 <PID>
```

### "Image not found" (Kubernetes)
```bash
# Rebuild les images
make build
# Si minikube, utiliser le Docker de minikube
eval $(minikube docker-env)
make build
```

### "Pods not starting"
```bash
# Voir les détails
kubectl describe pod <pod-name> -n pokemon-drafter
# Voir les events
kubectl get events -n pokemon-drafter
```

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [README.md](../README.md) | Vue d'ensemble et installation |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Schéma d'architecture détaillé |
| [GUIDE_DEVELOPPEMENT.md](GUIDE_DEVELOPPEMENT.md) | Guide pour développeurs |
| [RAPPORT_ANALYSE.md](RAPPORT_ANALYSE.md) | Analyse des choix techniques |
| [CGU.md](CGU.md) | Conditions d'utilisation |
| [CONTACTS.md](CONTACTS.md) | Contacts et support |

## 🎮 Workflow de Jeu

1. **Créer un compte** (Rouge ou Bleu)
2. **Créer une équipe** (max 6 Pokemon)
3. **Choisir un mode**:
   - Hasard: équipes aléatoires
   - Construit: utiliser une équipe créée
   - Pioche: draft de Pokemon
4. **Lancer un duel** contre un adversaire
5. **Jouer**: choisir Pokemon à chaque tour
6. **Gagner des points**: +10 victoire, -10 défaite

## 🔧 Développement

### Backend
```bash
cd backend-red
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

### Frontend
```bash
cd frontend-red
npm install
ng serve --port 4201
```

## 🌐 URLs Importantes

### Développement
- API Docs Red: http://localhost:8001/docs
- API Docs Blue: http://localhost:8002/docs
- Recommendation API: http://localhost:8004/docs

### Production
- App principale: http://pokemon-drafter.local
- Red Team: http://red.pokemon-drafter.local
- Blue Team: http://blue.pokemon-drafter.local

## ✅ Checklist Déploiement

- [ ] Docker installé et fonctionnel
- [ ] Kubernetes (minikube) démarré
- [ ] kubectl configuré
- [ ] DNS configuré dans /etc/hosts
- [ ] Images Docker construites (`make build`)
- [ ] Déploiement effectué (`make deploy`)
- [ ] Pods en état Running (`make status`)
- [ ] Services accessibles via navigateur

## 🎯 Fonctionnalités Principales

✅ Authentification JWT
✅ Équipes Red/Blue séparées
✅ CRUD équipes Pokemon
✅ Recommandation Pokemon
✅ Duels en temps réel
✅ Chat global et par équipe
✅ Historique des parties
✅ Calcul d'avantages de types
✅ Cache PokeAPI
✅ Logs centralisés
✅ Tests frontend

## 📞 Support

- **GitHub Issues**: https://github.com/bclovis/Projet_Microservices/issues
- **Email**: support@pokemon-drafter.local
- **Documentation**: Dossier `docs/`

---

**Projet académique ICC - 2026**

Bonne chance et amusez-vous bien ! 🎮
