# TP5 - API Gateway

## Architecture
- **users** (port 8001) : Gestion des utilisateurs
- **orders** (port 8002) : Gestion des commandes  
- **gateway** (port 8000) : Point d'entrée unique avec sécurité et cache

## Installation
```bash
pip install -r requirements.txt
```

## Lancement
```bash
# Terminal 1 - Users service
uvicorn users.main:app --port 8001

# Terminal 2 - Orders service
uvicorn orders.main:app --port 8002

# Terminal 3 - Gateway
uvicorn gateway.main:app --port 8000
```

## API Key
Clé d'API à utiliser : `secret-api-key-123`

Header à ajouter : `X-API-Key: secret-api-key-123`

## Endpoints disponibles
- `GET /users` - Liste des utilisateurs
- `GET /orders/{user}` - Commandes d'un utilisateur
- `GET /items` - Liste des items
- `GET /poubelle` - Users + Items (agrégation)
- `GET /profile/{user}` - User + ses commandes (agrégation)
