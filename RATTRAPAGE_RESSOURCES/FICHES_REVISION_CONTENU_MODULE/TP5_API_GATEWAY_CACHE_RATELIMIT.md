# FICHE TP5 — API Gateway : Cache, Rate Limiting, Agrégation

> **Séance :** 3 décembre | **Niveau :** Intermédiaire+  
> **Objectif TP :** Construire une API Gateway FastAPI qui centralise l'accès à 3 microservices, avec authentification par clé API (middleware), cache 10 minutes, rate limiting 1 req/20s, et endpoints d'agrégation

---

## 1. CONTEXTE DU TP — Ce qui était demandé

**Consigne exacte :**
1. Construire 3 microservices FastAPI : `orders`, `users`, et `gateway` sur des ports différents
2. La gateway expose :
   - `GET /users` → liste des utilisateurs
   - `GET /orders/{user}` → commandes d'un utilisateur
   - `GET /items` → liste d'objets (stockés localement dans la gateway)
3. Middleware sur la gateway : bloquer derrière une clé API (`X-API-Key`)
4. `GET /poubelle` → liste des users + items (agrégation)
5. `GET /profile/{user}` → un utilisateur + ses commandes (agrégation)
6. Cache avec expiration 10 minutes
7. Rate limiting : 1 requête toutes les 20 secondes

---

## 2. ARCHITECTURE DU TP5

```
[Client]
   │
   │ X-API-Key: secret-api-key-123
   ↓
[Gateway :8000]   ← Point d'entrée unique
   │
   ├─→ GET /users ──────────────────→ [Users Service :8001]
   │
   ├─→ GET /orders/{user} ──────────→ [Orders Service :8002]
   │
   └─→ GET /items (données locales dans la gateway)
```

**Ports :**
- Gateway : `http://localhost:8000`
- Users Service : `http://localhost:8001`
- Orders Service : `http://localhost:8002`

---

## 3. users/main.py et orders/main.py — Microservices simples

```python
# users/main.py — Service Users (port 8001)
from fastapi import FastAPI

app = FastAPI(title="Users Service")

USERS = [
    {"id": 1, "name": "Alice", "email": "alice@example.com"},
    {"id": 2, "name": "Bob", "email": "bob@example.com"},
    {"id": 3, "name": "Charlie", "email": "charlie@example.com"},
]

@app.get("/users")
def get_users():
    return {"users": USERS}

@app.get("/users/{name}")
def get_user(name: str):
    user = next((u for u in USERS if u["name"] == name), None)
    if not user:
        return {"error": "User not found"}
    return {"user": user}
```

```python
# orders/main.py — Service Orders (port 8002)
from fastapi import FastAPI

app = FastAPI(title="Orders Service")

ORDERS = {
    "Alice": [
        {"id": 1, "product": "Laptop", "amount": 999},
        {"id": 2, "product": "Mouse", "amount": 29},
    ],
    "Bob": [
        {"id": 3, "product": "Desk", "amount": 350},
    ],
    "Charlie": []
}

@app.get("/orders/{user}")
def get_orders(user: str):
    orders = ORDERS.get(user, [])
    return {"user": user, "orders": orders}
```

---

## 4. gateway/main.py — La Gateway Complète

### 4.1 — Configuration et variables

```python
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx
from datetime import datetime, timedelta

app = FastAPI(title="API Gateway")

# URLs des microservices backend
USERS_SERVICE = "http://localhost:8001"
ORDERS_SERVICE = "http://localhost:8002"

# Clé API (en production : variable d'environnement !)
API_KEY = "secret-api-key-123"

# ===== SYSTÈME DE CACHE =====
cache = {}                          # Dictionnaire en mémoire
CACHE_DURATION = timedelta(minutes=10)

# ===== RATE LIMITING =====
rate_limit_store = {}               # {ip: datetime_derniere_requete}
RATE_LIMIT_SECONDS = 20             # 1 requête toutes les 20 secondes

# Données locales (stockées dans la gateway elle-même)
ITEMS = [
    {"id": 1, "name": "Laptop", "category": "Electronics"},
    {"id": 2, "name": "Mouse", "category": "Electronics"},
    {"id": 3, "name": "Desk", "category": "Furniture"},
]
```

### 4.2 — Fonctions de cache

```python
def get_from_cache(key: str):
    """
    Récupère une valeur du cache si elle n'a pas expiré.
    Retourne None si absent ou expiré.
    """
    if key in cache:
        entry = cache[key]
        if datetime.now() < entry["expires_at"]:
            print(f"[CACHE HIT] {key}")
            return entry["data"]
        else:
            print(f"[CACHE EXPIRED] {key}")
            del cache[key]
    print(f"[CACHE MISS] {key}")
    return None

def set_in_cache(key: str, data):
    """Stocke une valeur avec une date d'expiration."""
    cache[key] = {
        "data": data,
        "expires_at": datetime.now() + CACHE_DURATION
    }
    print(f"[CACHE SET] {key} expire dans 10 min")
```

### 4.3 — Middleware d'authentification (clé API)

```python
@app.middleware("http")
async def verify_api_key(request: Request, call_next):
    """
    Exécuté sur TOUTES les requêtes (sauf /).
    Vérifie le header X-API-Key.
    """
    if request.url.path == "/":          # Page racine : pas besoin de clé
        return await call_next(request)
    
    api_key = request.headers.get("X-API-Key")
    
    if api_key != API_KEY:
        return JSONResponse(
            status_code=401,
            content={"error": "Unauthorized", "message": "Invalid or missing API key"}
        )
    
    return await call_next(request)     # Clé correcte → continuer
```

### 4.4 — Middleware de Rate Limiting

```python
@app.middleware("http")
async def rate_limiter(request: Request, call_next):
    """
    Limite : 1 requête toutes les 20 secondes par adresse IP.
    """
    if request.url.path == "/":
        return await call_next(request)
    
    client_ip = request.client.host    # IP du client
    current_time = datetime.now()
    
    if client_ip in rate_limit_store:
        last_request_time = rate_limit_store[client_ip]
        time_elapsed = (current_time - last_request_time).total_seconds()
        
        if time_elapsed < RATE_LIMIT_SECONDS:
            wait_time = RATE_LIMIT_SECONDS - time_elapsed
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "message": f"Attendez encore {wait_time:.1f} secondes"
                }
            )
    
    rate_limit_store[client_ip] = current_time   # Mettre à jour le timestamp
    return await call_next(request)
```

**Ordre des middlewares :**
> FastAPI applique les middlewares dans **l'ordre inverse** de leur déclaration. Le dernier déclaré est exécuté en premier. Dans ce TP, `rate_limiter` est déclaré après `verify_api_key`, donc `rate_limiter` s'exécute en premier (vérifie le rate limit), puis `verify_api_key`.

### 4.5 — Routes de proxy avec cache

```python
@app.get("/users")
async def get_users():
    """Proxy vers le service Users, avec cache 10 min"""
    cache_key = "users"
    
    # 1. Chercher en cache
    cached_data = get_from_cache(cache_key)
    if cached_data is not None:
        return cached_data
    
    # 2. Appeler le microservice backend avec httpx
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{USERS_SERVICE}/users")
        data = response.json()
    
    # 3. Stocker en cache
    set_in_cache(cache_key, data)
    return data

@app.get("/orders/{user}")
async def get_orders(user: str):
    """Cache spécifique par utilisateur"""
    cache_key = f"orders_{user}"          # Clé unique par user
    
    cached_data = get_from_cache(cache_key)
    if cached_data is not None:
        return cached_data
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{ORDERS_SERVICE}/orders/{user}")
        data = response.json()
    
    set_in_cache(cache_key, data)
    return data

@app.get("/items")
def get_items():
    """Items stockés localement, pas besoin de proxy"""
    return {"items": ITEMS}
```

### 4.6 — Endpoints d'agrégation

```python
@app.get("/poubelle")
async def get_poubelle():
    """
    Agrégation : Users + Items depuis deux sources différentes.
    Combine les données en une seule réponse.
    """
    async with httpx.AsyncClient() as client:
        users_response = await client.get(f"{USERS_SERVICE}/users")
        users_data = users_response.json()
    
    return {
        "users": users_data.get("users", []),
        "items": ITEMS                           # Données locales
    }

@app.get("/profile/{user}")
async def get_profile(user: str):
    """
    Agrégation : Infos user + ses commandes.
    Appels parallèles aux deux microservices.
    """
    async with httpx.AsyncClient() as client:
        # On fait les deux appels dans le même context (séquentiels ici, optimisable)
        users_response = await client.get(f"{USERS_SERVICE}/users")
        orders_response = await client.get(f"{ORDERS_SERVICE}/orders/{user}")
        
        users_data = users_response.json()
        orders_data = orders_response.json()
    
    # Trouver les infos de l'utilisateur dans la liste
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

## 5. httpx — Client HTTP async

```python
import httpx

# Appel simple GET
async with httpx.AsyncClient() as client:
    response = await client.get("http://service/endpoint")
    data = response.json()

# Appel avec headers
async with httpx.AsyncClient() as client:
    response = await client.get(
        "http://service/endpoint",
        headers={"Authorization": "Bearer token"},
        timeout=5.0   # Timeout 5 secondes
    )

# Appel POST avec JSON
async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://service/endpoint",
        json={"key": "value"}
    )
```

**`async with httpx.AsyncClient()` :**
> Ouvre une connexion HTTP, exécute les requêtes, ferme proprement la connexion. Le `async with` garantit la fermeture même en cas d'erreur.

---

## 6. Lancer les 3 services

```bash
# Terminal 1 : Users Service (port 8001)
cd users
uvicorn main:app --port 8001 --reload

# Terminal 2 : Orders Service (port 8002)
cd orders
uvicorn main:app --port 8002 --reload

# Terminal 3 : Gateway (port 8000)
cd gateway
uvicorn main:app --port 8000 --reload

# Ou avec le script fourni
bash start_services.sh
```

---

## 7. COMMANDES CURL DE TEST

```bash
# Sans clé API → 401
curl "http://localhost:8000/users"

# Avec clé API → 200
curl -H "X-API-Key: secret-api-key-123" "http://localhost:8000/users"

# Commandes d'Alice
curl -H "X-API-Key: secret-api-key-123" "http://localhost:8000/orders/Alice"

# Items (locaux)
curl -H "X-API-Key: secret-api-key-123" "http://localhost:8000/items"

# Agrégation users + items
curl -H "X-API-Key: secret-api-key-123" "http://localhost:8000/poubelle"

# Profil complet
curl -H "X-API-Key: secret-api-key-123" "http://localhost:8000/profile/Alice"

# Test rate limiting (attendre moins de 20 sec)
curl -H "X-API-Key: secret-api-key-123" "http://localhost:8000/users"
# 2e requête immédiatement → 429
curl -H "X-API-Key: secret-api-key-123" "http://localhost:8000/users"
```

---

## 8. SCHÉMA DE FONCTIONNEMENT — Un appel complet

```
Client: GET /users + X-API-Key: secret-api-key-123
    ↓
[Gateway reçoit la requête]
    ↓
Middleware rate_limiter (1er exécuté)
    → IP non connue → OK, stocker timestamp
    ↓
Middleware verify_api_key
    → api_key == API_KEY → OK
    ↓
Route GET /users
    → get_from_cache("users") → None (cache vide)
    → httpx.get(USERS_SERVICE/users) → {"users": [...]}
    → set_in_cache("users", data)
    → return data
    ↓
Client reçoit {"users": [...]}

----

2e appel dans les 10 minutes :
    ↓
Middleware rate_limiter → time_elapsed < 20s → 429 Too Many Requests
```

---

## 9. QUESTIONS D'ORAL POSSIBLES SUR CE TP

**Q : Qu'est-ce qu'une API Gateway et pourquoi en utiliser une ?**
> Point d'entrée unique pour tous les microservices. Avantages : (1) Le client n'a pas besoin de connaître l'adresse de chaque service, (2) On centralise les préoccupations transversales : auth, rate limiting, cache, logs, (3) On peut rediriger sans que le client s'en aperçoive.

**Q : Qu'est-ce que le rate limiting et pourquoi est-ce important ?**
> Limiter le nombre de requêtes par client/IP sur une période. Protège contre : (1) les attaques DDoS, (2) les abus d'API, (3) la surcharge des backends. Dans le TP : 1 req/20s par IP → si dépassé → 429 Too Many Requests.

**Q : Pourquoi mettre en cache les réponses ?**
> Éviter d'appeler les microservices à chaque requête. Si `/users` est appelé 100 fois en 10 minutes, le service users n'est appelé qu'une seule fois → réduction de la latence et de la charge. Cache simple en mémoire (dict Python) dans ce TP — en production : Redis.

**Q : Qu'est-ce que `httpx` et pourquoi pas `requests` ?**
> `httpx` est un client HTTP **async** (compatible avec `async/await`). `requests` est synchrone → bloquerait le thread FastAPI. Avec `httpx.AsyncClient()`, la gateway peut traiter d'autres requêtes pendant qu'elle attend une réponse d'un microservice.

**Q : Pourquoi `async with httpx.AsyncClient()` plutôt que créer le client une seule fois ?**
> Chaque `async with` crée un client avec sa propre connexion et la ferme proprement. Partager un client global fonctionne aussi (et est plus efficace), mais nécessite une gestion du cycle de vie (`lifespan`). Pour la simplicité du TP, `async with` est préféré.

**Q : Comment fonctionne le middleware en FastAPI ?**
> Un middleware est une fonction qui enveloppe **chaque requête**. Structure : `request → traitement → call_next(request) → réponse`. `call_next` appelle la route (ou le middleware suivant). Si on retourne avant `call_next`, la requête est bloquée (ex: 401 ou 429).
