# Architecture Pokemon Drafter

## Vue d'ensemble

L'application Pokemon Drafter est construite sur une architecture microservices complète avec séparation des préoccupations et isolation des équipes.

## Schéma d'architecture

```
                                    ┌─────────────────┐
                                    │   Users/Clients │
                                    └────────┬────────┘
                                             │
                                    ┌────────▼────────┐
                                    │  API Gateway    │
                                    │    (Nginx)      │
                                    └────────┬────────┘
                                             │
                         ┌───────────────────┼───────────────────┐
                         │                   │                   │
                ┌────────▼────────┐ ┌────────▼────────┐ ┌────────▼────────┐
                │  Frontend Red   │ │ Frontend Blue   │ │ Identity Provider│
                │   (Angular)     │ │   (Angular)     │ │   (Keycloak)    │
                └────────┬────────┘ └────────┬────────┘ └─────────────────┘
                         │                   │
                ┌────────▼────────┐ ┌────────▼────────┐
                │  Backend Red    │ │  Backend Blue   │
                │   (FastAPI)     │ │   (FastAPI)     │
                └────────┬────────┘ └────────┬────────┘
                         │                   │
                         │    ┌──────────────┼──────────────┐
                         │    │              │              │
                ┌────────▼────▼──┐  ┌────────▼────┐ ┌──────▼──────┐
                │   PostgreSQL   │  │   Redis     │ │    Kafka    │
                │   (Database)   │  │   (Cache)   │ │  (Broker)   │
                └────────────────┘  └─────────────┘ └──────┬──────┘
                                                            │
                         ┌──────────────────────────────────┤
                         │                                  │
                ┌────────▼────────┐              ┌──────────▼────────┐
                │ Recommendation  │              │   Encryption      │
                │    Engine       │              │    Service        │
                └─────────────────┘              └───────────────────┘
```

## Services

### 1. API Gateway (Nginx)
- **Rôle**: Point d'entrée unique, routage des requêtes
- **Port**: 80
- **Responsabilités**:
  - Routage basé sur le sous-domaine (red/blue)
  - Load balancing
  - SSL termination (si configuré)

### 2. Identity Provider (Keycloak)
- **Rôle**: Gestion de l'authentification et des tokens JWT
- **Port**: 8080
- **Responsabilités**:
  - Authentification des utilisateurs
  - Génération de tokens JWT
  - Gestion des sessions

### 3. Frontend Red/Blue (Angular)
- **Rôle**: Interface utilisateur pour chaque équipe
- **Ports**: 80 (dans les conteneurs)
- **Responsabilités**:
  - Affichage de l'interface utilisateur
  - Gestion des équipes
  - Interface de duel
  - Chat temps réel
  - Tests unitaires (Jasmine/Karma)

### 4. Backend Red/Blue (FastAPI)
- **Rôle**: API REST pour chaque équipe
- **Ports**: 8000
- **Responsabilités**:
  - Gestion des équipes
  - Logique de duel
  - Calcul d'avantages (formule F(A) et F(B))
  - Communication inter-backend via chiffrement
  - Appels à PokeAPI avec cache

### 5. Database (PostgreSQL)
- **Rôle**: Stockage persistant
- **Port**: 5432
- **Responsabilités**:
  - Stockage utilisateurs
  - Stockage équipes
  - Historique des duels
  - Logs système
  - Cache Pokemon
  - Messages chat

### 6. Cache Service (Redis)
- **Rôle**: Cache des données PokeAPI
- **Port**: 6379
- **Responsabilités**:
  - Cache des données Pokemon
  - Réduction des appels API
  - Performance améliorée

### 7. Message Broker (Kafka)
- **Rôle**: Communication asynchrone temps réel
- **Ports**: 9092 (client), 9093 (controller)
- **Responsabilités**:
  - Messages de duel
  - Messages de chat
  - Notifications temps réel
  - Communication inter-backend

### 8. Recommendation Engine
- **Rôle**: Calcul de recommandations
- **Port**: 8000
- **Responsabilités**:
  - Analyse de composition d'équipe
  - Calcul de couverture de types
  - Recommandations de Pokemon
  - Analyse de faiblesses

### 9. Encryption Service
- **Rôle**: Chiffrement des communications inter-backend
- **Port**: 8000
- **Responsabilités**:
  - Chiffrement des données
  - Déchiffrement des données
  - Gestion des clés

## Flux de données

### Authentification
1. User → Frontend → Identity Provider
2. Identity Provider génère JWT
3. Frontend stocke le token
4. Toutes les requêtes incluent le token

### Création d'équipe
1. Frontend → Backend (avec JWT)
2. Backend valide le token
3. Backend stocke dans Database
4. Backend retourne confirmation

### Duel
1. Red Player crée duel → Backend Red
2. Backend Red chiffre les données → Encryption Service
3. Backend Red envoie message → Kafka
4. Backend Blue reçoit → déchiffre → traite
5. Tour de jeu:
   - Les deux joueurs soumettent actions
   - Backend calcule F(A) et F(B)
   - Détermine le vainqueur du tour
   - Met à jour état via Kafka
   - Frontends reçoivent mise à jour

### Recommandation
1. Frontend → Backend → Recommendation Engine
2. Recommendation Engine analyse l'équipe
3. Retourne suggestions basées sur:
   - Couverture de types manquante
   - Compensation de faiblesses
   - Diversité de types

## Sécurité

- **Authentification**: JWT tokens via Keycloak
- **Communication inter-backend**: Chiffrée avec clés privées
- **Isolation**: Backends Red/Blue ne communiquent pas directement
- **Validation**: Toutes les entrées validées côté backend

## Persistance

- **Database**: Volume persistant Kubernetes
- **Configuration**: PersistentVolume + PersistentVolumeClaim
- **Backup**: Recommandé d'utiliser pg_dump régulièrement

## Scalabilité

- **Horizontal**: Tous les services peuvent être répliqués
- **Load Balancing**: Géré par Kubernetes Services
- **Cache**: Redis réduit la charge sur PokeAPI
- **Async**: Kafka permet la communication non-bloquante

## Monitoring et Logs

- **Logs centralisés**: Table system_logs dans PostgreSQL
- **Interface admin**: Accès aux logs via frontend
- **Kubernetes**: kubectl logs pour debugging

## Variables d'environnement (snake_case)

Toutes les variables sont en snake_case:
- `database_url`
- `redis_url`
- `kafka_broker`
- `pokeapi_base_url`
- `encryption_service_url`
- `team_color`
