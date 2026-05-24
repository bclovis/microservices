# S4 — API Gateways : Théorie + TP5 complet

> Cours de Lalanne Raphaël — Séance du 3 décembre  
> Source : `API Gateways (1).pdf`  
> Code : `TP5/`

---

## 1. Définition et rôle d'une API Gateway

> **"Une passerelle API (API Gateway) est un composant essentiel de la conception des systèmes, notamment dans les architectures de microservices et les applications web modernes. Elle sert de point d'entrée centralisé pour la gestion et le routage des requêtes des clients vers les microservices ou services backend appropriés au sein du système."**
> — Lalanne Raphaël

En résumé : **l'API Gateway est un proxy inverse** (reverse proxy) entre les clients et les microservices.

### Schéma du cours
```
Client ←→ API Gateway ──→ Microservice 1
                      ──→ Microservice 2
                      ──→ Microservice 3
```

**L'API Gateway gère :**
- Authentication (qui peut accéder ?)
- Caching (réponses mises en cache)
- Rate limiting (limiter le nombre de requêtes)
- Monitoring (logs, métriques)

---

## 2. Fonctionnalités d'une API Gateway

### Du cours (slide 4 et 5) :

1. **Routage** : Achemine les requêtes vers le microservice approprié (ex: requêtes sur /users → service Users)
2. **Authentification** : Vérifie les credentials avant de transmettre au service
3. **Rate limiting** : Limite le nombre de requêtes par IP / par token
4. **Cache** : Évite des appels répétés aux microservices pour les mêmes données
5. **Standardisation des erreurs** : Les réponses d'erreur sont standardisées par la gateway
6. **Agrégation** : Peut combiner les réponses de plusieurs services en une seule réponse

### Exemple e-commerce (cours) :
```
Application Web
      ↓
  API Gateway
   /   |   \
Users Products Shopping Cart
```

Tous les appels passent par la gateway. Le client n'a pas besoin de connaître les adresses des microservices.

---

## 3. Sans Gateway vs Avec Gateway

| Aspect | Sans Gateway | Avec Gateway |
|--------|-------------|-------------|
| **Adresses** | Client connaît toutes les adresses services | Client ne connaît qu'une adresse |
| **Auth** | Chaque service gère son auth | Gateway centralise l'auth |
| **CORS** | Chaque service gère CORS | Gateway gère CORS |
| **Rate limiting** | À implémenter dans chaque service | Fait une seule fois |
| **Monitoring** | Logs éparpillés | Point de log central |
| **Agrégation** | Impossible / côté client | Facile côté gateway |
| **Sécurité** | Surface d'attaque étendue | Services cachés derrière la gateway |

---

## 4. Exercice TP5 — Ce qui était demandé (slides)

**Construire 3 microservices FastAPI :**
1. `users` : `GET /users` → liste d'utilisateurs
2. `orders` : `GET /orders/{user}` → commandes d'un utilisateur
3. `gateway` : point d'entrée centralisé

**La gateway doit :**
1. Exposer : `GET /users`, `GET /orders/{user}`, `GET /items`
2. Bloquer l'accès derrière une **clé d'API** (middleware)
3. Implémenter `GET /poubelle` (agrégation users + items)
4. Implémenter `GET /profile/{user}` (agrégation user + orders)
5. Implémenter un **cache de 10 minutes**
6. Implémenter un **rate limit de 1 requête toutes les 20 secondes**

---

## 5. Architecture TP5

```
┌─────────────────────────────────────────────┐
│  CLIENT                                      │
│  Header: X-API-Key: secret-api-key-123       │
└──────────────────────┬──────────────────────┘
                       │
         ┌─────────────▼─────────────┐
         │      API GATEWAY           │
         │      localhost:8000        │
         │                            │
         │  Middlewares:              │
         │  1. verify_api_key         │
         │  2. rate_limiter           │
         │                            │
         │  Cache (10 min)            │
         │  Routes:                   │
         │  GET /users                │
         │  GET /orders/{user}        │
         │  GET /items                │
         │  GET /poubelle (agrégation)│
         │  GET /profile/{user}       │
         └────────────┬──────────────┘
                      │
          ┌───────────┴───────────┐
          │                       │
   ┌──────▼──────┐       ┌───────▼──────┐
   │  users      │       │  orders      │
   │  :8001      │       │  :8002       │
   └─────────────┘       └──────────────┘
```

---

## 6. Code complet du TP5

### TP5/users/main.py (simple — pas de BDD)
```python
from fastapi import FastAPI

app = FastAPI(title="Users Service")

# Données en dur - pas de BDD (comme demandé dans le sujet)
USERS = [
    {"id": 1, "name": "Alice", "email": "alice@example.com"},
    {"id": 2, "name": "Bob", "email": "bob@example.com"},
    {"id": 3, "name": "Charlie", "email": "charlie@example.com"},
]

@app.get("/")
def root():
    return {"service": "users", "status": "running"}

@app.get("/users")
def get_users():
    """Retourne la liste de tous les utilisateurs"""
    return {"users": USERS}
```

### TP5/orders/main.py (simple — pas de BDD)
```python
from fastapi import FastAPI

app = FastAPI(title="Orders Service")

ORDERS = {
    "Alice": [
        {"id": 101, "product": "Laptop", "price": 1200},
        {"id": 102, "product": "Mouse", "price": 25},
    ],
    "Bob": [
        {"id": 201, "product": "Keyboard", "price": 75},
    ],
    "Charlie": [
        {"id": 301, "product": "Monitor", "price": 300},
        {"id": 302, "product": "Webcam", "price": 80},
        {"id": 303, "product": "Headset", "price": 60},
    ],
}

@app.get("/")
def root():
    return {"service": "orders", "status": "running"}

@app.get("/orders/{user}")
def get_orders(user: str):
    """Retourne les commandes d'un utilisateur spécifique"""
    return {"user": user, "orders": ORDERS.get(user, [])}
```

### TP5/gateway/main.py — COMPLET et ANNOTÉ
```python
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx                        # ← bibliothèque pour les appels HTTP asynchrones
from datetime import datetime, timedelta

app = FastAPI(title="API Gateway")

# URLs des microservices (en production, utiliser variables d'environnement)
USERS_SERVICE = "http://localhost:8001"
ORDERS_SERVICE = "http://localhost:8002"

# Clé API pour l'authentification (en production → variable d'env / Secret K8s)
API_KEY = "secret-api-key-123"

# ===== SYSTÈME DE CACHE EN MÉMOIRE =====
cache = {}
CACHE_DURATION = timedelta(minutes=10)  # Expire après 10 minutes

def get_from_cache(key: str):
    """Retourne les données du cache si elles existent et sont valides"""
    if key in cache:
        entry = cache[key]
        if datetime.now() < entry["expires_at"]:
            print(f"[CACHE HIT] {key}")
            return entry["data"]       # ← Données valides
        else:
            del cache[key]             # ← Expire, on supprime
    print(f"[CACHE MISS] {key}")
    return None                        # ← Pas en cache

def set_in_cache(key: str, data):
    """Stocke dans le cache avec date d'expiration"""
    cache[key] = {
        "data": data,
        "expires_at": datetime.now() + CACHE_DURATION
    }

# ===== MIDDLEWARE 1 : AUTHENTIFICATION PAR CLÉ API =====
@app.middleware("http")
async def verify_api_key(request: Request, call_next):
    """
    Vérifie la présence et la validité du header X-API-Key
    TOUTES les requêtes (sauf /) sont bloquées sans bonne clé
    """
    if request.url.path == "/":      # Route racine libre d'accès
        return await call_next(request)
    
    api_key = request.headers.get("X-API-Key")  # Récupérer le header
    
    if api_key != API_KEY:
        return JSONResponse(
            status_code=401,
            content={"error": "Unauthorized", "message": "Invalid or missing API key"}
        )
    
    return await call_next(request)  # Passer au middleware/route suivant

# ===== MIDDLEWARE 2 : RATE LIMITING =====
rate_limit_store = {}          # {ip: datetime_derniere_requete}
RATE_LIMIT_SECONDS = 20        # 1 requête toutes les 20 secondes

@app.middleware("http")
async def rate_limiter(request: Request, call_next):
    """
    Limite à 1 requête toutes les 20 secondes par IP
    """
    if request.url.path == "/":
        return await call_next(request)
    
    client_ip = request.client.host
    current_time = datetime.now()
    
    if client_ip in rate_limit_store:
        elapsed = (current_time - rate_limit_store[client_ip]).total_seconds()
        
        if elapsed < RATE_LIMIT_SECONDS:
            wait_time = RATE_LIMIT_SECONDS - elapsed
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "message": f"Rate limit exceeded. Please wait {wait_time:.1f} seconds."
                }
            )
    
    rate_limit_store[client_ip] = current_time  # Mettre à jour le timestamp
    return await call_next(request)

# ===== DONNÉES LOCALES =====
ITEMS = [
    {"id": 1, "name": "Laptop", "category": "Electronics"},
    {"id": 2, "name": "Mouse", "category": "Electronics"},
    {"id": 3, "name": "Desk", "category": "Furniture"},
    {"id": 4, "name": "Chair", "category": "Furniture"},
]

# ===== ROUTES =====

@app.get("/")
def root():
    return {"service": "API Gateway", "status": "running"}

@app.get("/items")
def get_items():
    """Items stockés localement dans la gateway"""
    return {"items": ITEMS}

@app.get("/users")
async def get_users():
    """Proxy vers users-service avec cache"""
    cached = get_from_cache("users")
    if cached is not None:
        return cached
    
    # httpx = bibliothèque async pour appels HTTP entre services
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{USERS_SERVICE}/users")
        data = response.json()
    
    set_in_cache("users", data)
    return data

@app.get("/orders/{user}")
async def get_orders(user: str):
    """Proxy vers orders-service avec cache"""
    cache_key = f"orders_{user}"   # Cache par utilisateur
    cached = get_from_cache(cache_key)
    if cached is not None:
        return cached
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{ORDERS_SERVICE}/orders/{user}")
        data = response.json()
    
    set_in_cache(cache_key, data)
    return data

@app.get("/poubelle")
async def get_poubelle():
    """
    AGRÉGATION : combine users + items en une seule réponse
    """
    async with httpx.AsyncClient() as client:
        users_response = await client.get(f"{USERS_SERVICE}/users")
        users_data = users_response.json()
    
    return {
        "users": users_data.get("users", []),
        "items": ITEMS
    }

@app.get("/profile/{user}")
async def get_profile(user: str):
    """
    AGRÉGATION : combine infos user + ses commandes
    """
    async with httpx.AsyncClient() as client:
        # Appels aux 2 microservices
        users_response = await client.get(f"{USERS_SERVICE}/users")
        orders_response = await client.get(f"{ORDERS_SERVICE}/orders/{user}")
        
        users_data = users_response.json()
        orders_data = orders_response.json()
    
    # Trouver l'utilisateur dans la liste
    user_info = None
    for u in users_data.get("users", []):
        if u["name"] == user:
            user_info = u
            break
    
    return {
        "user": user_info,
        "orders": orders_data.get("orders", [])
    }
```

---

## 7. Lancer et tester le TP5

### Démarrer les services
```bash
# Terminal 1 — Users service (port 8001)
cd TP5/users
uvicorn main:app --reload --port 8001

# Terminal 2 — Orders service (port 8002)
cd TP5/orders
uvicorn main:app --reload --port 8002

# Terminal 3 — Gateway (port 8000)
cd TP5/gateway
uvicorn main:app --reload --port 8000
```

### Tester avec curl
```bash
# ❌ Sans clé API → 401
curl http://localhost:8000/users

# ✅ Avec clé API
curl -H "X-API-Key: secret-api-key-123" http://localhost:8000/users

# Tester le cache (2ème requête = CACHE HIT dans les logs)
curl -H "X-API-Key: secret-api-key-123" http://localhost:8000/users

# Tester le rate limit (2 requêtes rapides)
curl -H "X-API-Key: secret-api-key-123" http://localhost:8000/users
curl -H "X-API-Key: secret-api-key-123" http://localhost:8000/users
# → 2ème requête : {"error": "Too Many Requests", ...}

# Agrégation
curl -H "X-API-Key: secret-api-key-123" http://localhost:8000/poubelle
curl -H "X-API-Key: secret-api-key-123" http://localhost:8000/profile/Alice
```

---

## 8. Notion importante : httpx

**`httpx`** = bibliothèque Python pour faire des appels HTTP, alternative asynchrone à `requests`.

```python
import httpx

# Synchrone (simple)
response = httpx.get("http://service/endpoint")
data = response.json()

# Asynchrone (recommandé avec FastAPI)
async with httpx.AsyncClient() as client:
    response = await client.get("http://service/endpoint")
    data = response.json()
```

**Pourquoi async ?**
→ FastAPI est asynchrone. Si on utilise `requests` (synchrone) dans une route async, on bloque le serveur. Avec `httpx.AsyncClient()`, le serveur peut traiter d'autres requêtes pendant l'attente de la réponse.

---

## 9. Questions d'oral probables

**Q: Qu'est-ce qu'une API Gateway et pourquoi l'utiliser ?**  
R: Point d'entrée centralisé (proxy inverse) qui gère : routage, authentification, rate limiting, cache, monitoring et agrégation. Le client ne connaît qu'une adresse. Les services backend sont cachés.

**Q: Comment fonctionne le cache dans le TP5 ?**  
R: Dictionnaire Python `cache = {}` avec une clé (ex: "users") et une valeur contenant les données + une date d'expiration (`expires_at`). Avant d'appeler le microservice, on vérifie si les données sont en cache et non expirées.

**Q: Comment fonctionne le rate limiting dans le TP5 ?**  
R: Dictionnaire `rate_limit_store = {ip: datetime}`. À chaque requête, on calcule le temps écoulé depuis la dernière requête de cette IP. Si < 20 secondes → 429 Too Many Requests.

**Q: Pourquoi utiliser httpx plutôt que requests pour les appels entre services ?**  
R: `httpx.AsyncClient()` est asynchrone et compatible avec FastAPI. `requests` est synchrone et bloquerait le serveur.

**Q: Qu'est-ce que l'agrégation dans une API Gateway ?**  
R: La gateway appelle plusieurs microservices et combine leurs réponses en une seule. Exemple : `/profile/{user}` appelle à la fois users-service et orders-service, et retourne le tout dans une seule réponse JSON.

**Q: Quelle est la différence entre middleware et route dans FastAPI ?**  
R: Un middleware s'exécute avant/après TOUTES les routes. Une route s'exécute seulement pour un path spécifique. Les middlewares sont idéaux pour l'auth et le rate limiting qui doivent s'appliquer globalement.
