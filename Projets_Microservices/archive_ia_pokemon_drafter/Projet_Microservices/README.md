# Pokemon Drafter - Projet Microservices

## Description
Application de duel Pokemon basée sur un système de pierre-papier-ciseaux amélioré avec calcul d'avantages de types.

## Architecture

### Services
- **API Gateway** : Point d'entrée unique (Nginx)
- **Identity Provider** : Authentification JWT (Keycloak)
- **Frontend Rouge** : Interface Angular pour équipe rouge
- **Frontend Bleu** : Interface Angular pour équipe bleue
- **Backend Rouge** : API FastAPI pour équipe rouge
- **Backend Bleu** : API FastAPI pour équipe bleue
- **Database** : PostgreSQL avec persistence
- **Cache Service** : Redis pour cache PokeAPI
- **Message Broker** : Kafka pour communication temps réel
- **Recommendation Engine** : Service Python pour recommandations
- **Encryption Service** : Service de chiffrement inter-backend

## Prérequis
- Docker
- Kubernetes (minikube recommandé)
- kubectl

## Configuration DNS Local
Ajouter dans `/etc/hosts`:
```
127.0.0.1 pokemon-drafter.local
127.0.0.1 red.pokemon-drafter.local
127.0.0.1 blue.pokemon-drafter.local
127.0.0.1 auth.pokemon-drafter.local
```

## Déploiement

### 1. Créer le namespace
```bash
kubectl create namespace pokemon-drafter
```

### 2. Déployer l'application
```bash
kubectl apply -f k8s/ -n pokemon-drafter
```

### 3. Vérifier le déploiement
```bash
kubectl get pods -n pokemon-drafter
kubectl get services -n pokemon-drafter
```

## Utilisateurs de test

### Utilisateurs Rouge
- **Pseudo**: red_player1
  - **Email**: red1@pokemon.com
  - **Password**: RedPass123!
  
- **Pseudo**: red_player2
  - **Email**: red2@pokemon.com
  - **Password**: RedPass123!

### Utilisateurs Bleu
- **Pseudo**: blue_player1
  - **Email**: blue1@pokemon.com
  - **Password**: BluePass123!
  
- **Pseudo**: blue_player2
  - **Email**: blue2@pokemon.com
  - **Password**: BluePass123!

### Admin
- **Pseudo**: admin
  - **Email**: admin@pokemon.com
  - **Password**: AdminPass123!

## Accès aux services
- **Application**: http://pokemon-drafter.local
- **Frontend Rouge**: http://red.pokemon-drafter.local
- **Frontend Bleu**: http://blue.pokemon-drafter.local
- **API Gateway**: http://pokemon-drafter.local/api

## Variables d'environnement importantes

Toutes les variables sont en **snake_case** comme demandé.

## Calcul d'avantage type

La formule utilisée pour calculer l'avantage entre deux Pokemon A (type WX) et B (type YZ):

```
F(A) = 1*(W/Y)*(W/Z) + 1*(X/Y)*(X/Z)
F(B) = 1*(Y/W)*(Y/X) + 1*(Z/W)*(Z/X)
```

Le Pokemon avec le F le plus élevé remporte le tour.

## Structure du projet
```
.
├── api-gateway/          # Nginx reverse proxy
├── identity-provider/    # Keycloak pour auth
├── frontend-red/         # Angular app équipe rouge
├── frontend-blue/        # Angular app équipe bleue
├── backend-red/          # FastAPI équipe rouge
├── backend-blue/         # FastAPI équipe bleue
├── database/             # PostgreSQL
├── cache-service/        # Redis
├── kafka/                # Message broker
├── recommendation/       # Engine de recommandation
├── encryption/           # Service de chiffrement
├── k8s/                  # Fichiers Kubernetes
└── docs/                 # Documentation
```

## Tests
Les tests frontend sont disponibles pour chaque composant Angular:
```bash
cd frontend-red && npm test
cd frontend-blue && npm test
```

## Logs
Les logs de tous les services sont accessibles via l'interface admin sur la page principale.

## Développement

### Backend
```bash
cd backend-red
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend-red
npm install
ng serve
```

## Contributeurs
- Membre 1
- Membre 2
- Membre 3
- Membre 4

## Licence
Projet académique ICC
