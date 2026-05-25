# ARCHITECTURE DU PROJET

## Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────────┐
│                           CLIENT                                │
│              (Navigateur / curl / test script)                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Header: X-API-Key: secret-api-key-123
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API GATEWAY (Port 8000)                    │
│─────────────────────────────────────────────────────────────────│
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         MIDDLEWARE 1 : Rate Limiting                     │  │
│  │   → Vérifie : 1 requête max toutes les 20 secondes     │  │
│  │   → Si dépassé : 429 Too Many Requests                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                          │                                      │
│                          ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         MIDDLEWARE 2 : API Key Authentication            │  │
│  │   → Vérifie : X-API-Key == secret-api-key-123          │  │
│  │   → Si invalide : 401 Unauthorized                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                          │                                      │
│                          ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              SYSTÈME DE CACHE                            │  │
│  │   → Durée : 10 minutes                                   │  │
│  │   → Stockage : En mémoire (dictionnaire Python)         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                          │                                      │
│                          ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    ROUTES                                │  │
│  │                                                           │  │
│  │  GET /users          → Service Users                     │  │
│  │  GET /orders/{user}  → Service Orders                    │  │
│  │  GET /items          → Données locales                   │  │
│  │  GET /poubelle       → Agrégation Users + Items         │  │
│  │  GET /profile/{user} → Agrégation User + Orders         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
         │                        │                     │
         │                        │                     │
         ▼                        ▼                     ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────┐
│  USERS SERVICE   │    │  ORDERS SERVICE  │    │    ITEMS     │
│   (Port 8001)    │    │   (Port 8002)    │    │  (En local)  │
│──────────────────│    │──────────────────│    │──────────────│
│                  │    │                  │    │              │
│ GET /users       │    │ GET /orders/{u}  │    │ Stockés dans │
│                  │    │                  │    │  la gateway  │
│ Données :        │    │ Données :        │    │              │
│ - Alice          │    │ - Alice: 2 cmd   │    │ - Laptop     │
│ - Bob            │    │ - Bob: 1 cmd     │    │ - Mouse      │
│ - Charlie        │    │ - Charlie: 3 cmd │    │ - Desk       │
│                  │    │                  │    │ - Chair      │
└──────────────────┘    └──────────────────┘    └──────────────┘
```

## Flux d'une requête : GET /users

```
1. CLIENT
   └─> Envoie requête GET /users avec header X-API-Key

2. GATEWAY - Middleware Rate Limiting
   └─> Vérifie dernière requête de cette IP
       ├─> < 20 sec ? → 429 Too Many Requests [FIN]
       └─> >= 20 sec ? → Continue ↓

3. GATEWAY - Middleware API Key
   └─> Vérifie header X-API-Key
       ├─> Invalide/absent ? → 401 Unauthorized [FIN]
       └─> Valide ? → Continue ↓

4. GATEWAY - Route /users
   └─> Vérifie le cache
       ├─> Trouvé et valide ?
       │   └─> Retourne depuis cache → [FIN]
       │
       └─> Pas trouvé ou expiré ?
           └─> Continue ↓

5. GATEWAY → USERS SERVICE
   └─> HTTP GET http://localhost:8001/users

6. USERS SERVICE
   └─> Retourne {"users": [...]}

7. GATEWAY
   └─> Stocke en cache avec expiration 10 min
   └─> Retourne au CLIENT
```

## Flux d'une requête d'agrégation : GET /profile/Alice

```
CLIENT
  │
  └─> GET /profile/Alice
       │
       ▼
    GATEWAY (middlewares passés)
       │
       ├──────────────────┬──────────────────┐
       │                  │                  │
       ▼                  ▼                  │
   GET /users       GET /orders/Alice       │
       │                  │                  │
       ▼                  ▼                  │
 USERS SERVICE      ORDERS SERVICE           │
       │                  │                  │
       └──────────────────┴──────────────────┘
                    │
                    ▼
              GATEWAY agrège
                    │
                    ▼
               {
                 "user": {...},
                 "orders": [...]
               }
                    │
                    ▼
                 CLIENT
```

## Structure des fichiers

```
TP5/
├── users/
│   └── main.py              # Service Users (port 8001)
│
├── orders/
│   └── main.py              # Service Orders (port 8002)
│
├── gateway/
│   └── main.py              # API Gateway (port 8000)
│                            # - Middlewares (auth, rate limit)
│                            # - Cache
│                            # - Routes et agrégation
│
├── requirements.txt         # Dépendances Python
├── README.md               # Instructions de base
├── EXPLICATIONS.md         # Documentation détaillée
├── ARCHITECTURE.md         # Ce fichier
├── CURL_COMMANDS.md        # Commandes de test
├── test_gateway.py         # Script de test automatisé
└── start_services.sh       # Script de lancement
```

## Technologies utilisées

```
┌─────────────────────────────────────────┐
│           FastAPI Framework             │
│  - Framework web Python moderne         │
│  - Async/await natif                    │
│  - Documentation auto (Swagger)         │
│  - Validation automatique               │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│            httpx Library                │
│  - Client HTTP asynchrone               │
│  - Appels entre microservices           │
│  - Compatible avec async/await          │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│            uvicorn Server               │
│  - Serveur ASGI pour FastAPI            │
│  - Haute performance                    │
│  - Support de l'asynchrone              │
└─────────────────────────────────────────┘
```

## Patterns implémentés

1. **API Gateway Pattern**
   - Point d'entrée unique pour tous les clients
   - Routage vers les microservices appropriés

2. **Backend for Frontend (BFF)**
   - Endpoints d'agrégation personnalisés (/poubelle, /profile)
   - Optimise les appels pour le client

3. **Cache-Aside Pattern**
   - Vérifier cache → Si absent → Charger → Mettre en cache
   - Expiration temporelle (TTL = 10 min)

4. **Rate Limiting**
   - Protection contre les abus
   - Limite par IP

5. **Middleware Pattern**
   - Logique transversale (auth, rate limit)
   - Exécution avant chaque route

## Codes de statut HTTP utilisés

| Code | Nom | Utilisation |
|------|-----|-------------|
| 200 | OK | Requête réussie |
| 401 | Unauthorized | API Key invalide ou manquante |
| 429 | Too Many Requests | Rate limit dépassé |
| 500 | Internal Server Error | Erreur serveur |

## Sécurité

```
┌─────────────────────────────────────────────┐
│         Niveau 1 : Rate Limiting            │
│  Protection contre le spam et les DDoS      │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│      Niveau 2 : Authentification            │
│  Vérification de la clé API                 │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│    Niveau 3 : Isolation des services        │
│  Les microservices ne sont accessibles      │
│  que par la gateway (pas depuis Internet)   │
└─────────────────────────────────────────────┘
```

## Performance

**Sans cache :**
```
Client → Gateway → Users Service
Temps : ~50-100ms par requête
```

**Avec cache :**
```
Client → Gateway (retourne depuis RAM)
Temps : ~1-5ms par requête
```

**Gain de performance : 10-100x plus rapide !**
