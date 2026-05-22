# 📘 FICHE 5 : API GATEWAY

> **Source** : API Gateways.pdf (03/12/2025)

---

## 🎯 QU'EST-CE QU'UNE API GATEWAY ?

Une **API Gateway** est un **point d'entrée unique** pour toutes les requêtes vers vos microservices.

### Analogie
Imagine un hôtel :
- **Sans Gateway** : Les clients frappent directement aux portes des chambres
- **Avec Gateway** : Les clients passent par la réception (gateway) qui les redirige

```
❌ SANS API GATEWAY
┌─────────┐     ┌──────────────┐
│Frontend │────▶│ UserService  │
└─────────┘  │  └──────────────┘
             │  ┌──────────────┐
             ├─▶│ OrderService │
             │  └──────────────┘
             │  ┌──────────────┐
             └─▶│ProductService│
                └──────────────┘

✅ AVEC API GATEWAY
┌─────────┐     ┌─────────────┐     ┌──────────────┐
│Frontend │────▶│ API GATEWAY │────▶│ UserService  │
└─────────┘     └─────────────┘  │  └──────────────┘
                                 │  ┌──────────────┐
                                 ├─▶│ OrderService │
                                 │  └──────────────┘
                                 │  ┌──────────────┐
                                 └─▶│ProductService│
                                    └──────────────┘
```

---

## 🔑 RÔLES DE L'API GATEWAY

### 1. **Routage (Reverse Proxy)**
Redirige les requêtes vers le bon service.

```python
# TP5 - Gateway routing
@app.get("/users")
async def get_users():
    # Redirige vers user-service:8001
    response = requests.get("http://user-service:8001/users")
    return response.json()

@app.get("/orders/{user}")
async def get_orders(user: str):
    # Redirige vers order-service:8002
    response = requests.get(f"http://order-service:8002/orders/{user}")
    return response.json()
```

### 2. **Sécurité et Authentification**
Vérifie les API Keys ou JWT avant de laisser passer.

```python
from fastapi import Header, HTTPException

API_KEY = "secret-api-key-123"

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return x_api_key

@app.get("/users", dependencies=[Depends(verify_api_key)])
async def get_users():
    # Seules les requêtes avec la bonne API Key passent
    response = requests.get("http://user-service:8001/users")
    return response.json()
```

**Usage :**
```bash
# ❌ Sans API Key → 403 Forbidden
curl http://localhost:8000/users

# ✅ Avec API Key → 200 OK
curl -H "X-API-Key: secret-api-key-123" http://localhost:8000/users
```

### 3. **Rate Limiting**
Limite le nombre de requêtes par client.

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/users")
@limiter.limit("10/minute")  # Max 10 requêtes par minute
async def get_users():
    return {"users": [...]}
```

### 4. **Caching**
Met en cache les réponses pour améliorer les performances.

```python
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379)

@app.get("/users")
async def get_users():
    # Vérifier le cache
    cached = redis_client.get("users_list")
    if cached:
        return json.loads(cached)
    
    # Sinon, appeler le service
    response = requests.get("http://user-service:8001/users")
    data = response.json()
    
    # Mettre en cache pour 60 secondes
    redis_client.setex("users_list", 60, json.dumps(data))
    
    return data
```

### 5. **Agrégation de données**
Combine les réponses de plusieurs services.

```python
@app.get("/profile/{user}")
async def get_profile(user: str):
    # Appeler 2 services en parallèle
    user_data = requests.get(f"http://user-service:8001/users/{user}").json()
    orders_data = requests.get(f"http://order-service:8002/orders/{user}").json()
    
    # Agréger les données
    return {
        "user": user_data,
        "orders": orders_data,
        "total_orders": len(orders_data)
    }
```

### 6. **Load Balancing**
Distribue les requêtes entre plusieurs instances d'un service.

```python
import random

USER_SERVICE_INSTANCES = [
    "http://user-service-1:8001",
    "http://user-service-2:8001",
    "http://user-service-3:8001"
]

@app.get("/users")
async def get_users():
    # Choisir une instance aléatoire (round-robin simple)
    instance = random.choice(USER_SERVICE_INSTANCES)
    response = requests.get(f"{instance}/users")
    return response.json()
```

### 7. **Transformation de protocole**
Convertir entre différents formats (REST → gRPC, HTTP → WebSocket...)

### 8. **Logging et Monitoring**
Centraliser les logs de toutes les requêtes.

```python
import time
import logging

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Logger la requête
    logging.info(f"Request: {request.method} {request.url}")
    
    response = await call_next(request)
    
    # Logger le temps de traitement
    process_time = time.time() - start_time
    logging.info(f"Response: {response.status_code} - {process_time:.2f}s")
    
    return response
```

---

## 📦 EXEMPLE COMPLET : TP5

### Architecture

```
Frontend (Angular)
      │
      ▼
┌─────────────────┐
│  API Gateway    │ (port 8000)
│  - Sécurité     │
│  - Cache        │
│  - Agrégation   │
└─────────────────┘
      │
      ├─────────────────────┬─────────────────────┐
      ▼                     ▼                     ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ UserService │     │OrderService │     │ ItemService │
│  port 8001  │     │  port 8002  │     │  port 8003  │
└─────────────┘     └─────────────┘     └─────────────┘
```

### Code Gateway (main.py)

```python
from fastapi import FastAPI, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import requests
import redis
import json

app = FastAPI(title="API Gateway")

# CORS pour le frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis cache
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

# Sécurité
API_KEY = "secret-api-key-123"

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")

# Routes avec redirection
@app.get("/users", dependencies=[Depends(verify_api_key)])
async def get_users():
    """Récupérer la liste des utilisateurs"""
    # Vérifier le cache
    cached = redis_client.get("users")
    if cached:
        return json.loads(cached)
    
    # Appeler le service
    response = requests.get("http://localhost:8001/users")
    data = response.json()
    
    # Mettre en cache 60s
    redis_client.setex("users", 60, json.dumps(data))
    
    return data

@app.get("/orders/{user}", dependencies=[Depends(verify_api_key)])
async def get_orders(user: str):
    """Récupérer les commandes d'un utilisateur"""
    response = requests.get(f"http://localhost:8002/orders/{user}")
    return response.json()

@app.get("/profile/{user}", dependencies=[Depends(verify_api_key)])
async def get_profile(user: str):
    """Agréger user + orders"""
    # Appeler les 2 services
    user_response = requests.get(f"http://localhost:8001/users/{user}")
    orders_response = requests.get(f"http://localhost:8002/orders/{user}")
    
    return {
        "user": user_response.json(),
        "orders": orders_response.json()
    }
```

---

## 🚀 SOLUTIONS DE GATEWAY

### 1. Custom Gateway (FastAPI/Flask)
**Avantages :**
✅ Contrôle total
✅ Logique métier custom
✅ Simple à développer

**Inconvénients :**
❌ Réinventer la roue
❌ Maintenance manuelle

### 2. Nginx
**Avantages :**
✅ Très performant
✅ Mature et stable
✅ Reverse proxy + load balancing

**Inconvénients :**
❌ Configuration complexe
❌ Pas de logique métier

### 3. Kong / Traefik / Envoy
**Avantages :**
✅ Fonctionnalités riches (plugins)
✅ Load balancing avancé
✅ Monitoring intégré

**Inconvénients :**
❌ Complexe à configurer
❌ Overhead

---

## ⚡ AVANTAGES DE L'API GATEWAY

1. **Point d'entrée unique** : Le frontend n'a qu'une seule URL
2. **Sécurité centralisée** : Authentification/autorisation en un seul endroit
3. **Simplification du frontend** : Pas besoin de gérer plusieurs endpoints
4. **Agrégation de données** : Combiner plusieurs services en une requête
5. **Cache centralisé** : Améliore les performances
6. **Rate limiting** : Protection contre les abus
7. **Monitoring centralisé** : Tous les logs au même endroit

---

## ⚠️ INCONVÉNIENTS

1. **Single Point of Failure** : Si la gateway tombe, tout tombe
   - **Solution** : Déployer plusieurs instances (load balancing)

2. **Goulot d'étranglement** : Toutes les requêtes passent par là
   - **Solution** : Scaler horizontalement

3. **Complexité supplémentaire** : Un composant de plus à gérer

---

## 🎤 QUESTIONS PROBABLES À L'ORAL

### Q1 : Qu'est-ce qu'une API Gateway ?
**Réponse type :**
> "Une API Gateway est un point d'entrée unique pour toutes les requêtes vers les microservices. Elle gère le routage, la sécurité, le cache, l'agrégation de données, et le rate limiting. Dans notre TP5, le frontend appelle uniquement la gateway (port 8000), et c'est elle qui redirige vers les services internes (users, orders, items)."

### Q2 : Quels sont les rôles de l'API Gateway ?
**Réponse type :**
> "Les principaux rôles sont : 1) Routage vers les bons services, 2) Sécurité (vérifier les API Keys ou JWT), 3) Cache pour améliorer les performances, 4) Agrégation de données de plusieurs services, 5) Rate limiting pour limiter les abus, 6) Load balancing entre plusieurs instances. Dans notre projet, on utilise aussi la gateway pour le CORS."

### Q3 : Pourquoi utiliser une API Gateway plutôt qu'appeler les services directement ?
**Réponse type :**
> "Ça simplifie le frontend qui n'a qu'une seule URL à connaître, ça centralise la sécurité (pas besoin de vérifier l'API Key dans chaque service), ça permet d'agréger les données (une seule requête frontend au lieu de plusieurs), et ça cache les détails d'implémentation (le frontend ne sait pas combien de services existent en backend)."

### Q4 : Quel est le principal risque de l'API Gateway ?
**Réponse type :**
> "C'est un Single Point of Failure : si la gateway tombe, tous les services deviennent inaccessibles même s'ils fonctionnent. La solution est de déployer plusieurs instances de la gateway avec un load balancer devant, comme on peut le faire avec Kubernetes (plusieurs replicas)."

### Q5 : Dans votre projet PokeDrafter, comment utilisez-vous la gateway ?
**Réponse type :**
> "On utilise Nginx comme reverse proxy. Le frontend Angular appelle uniquement la gateway (port 80), qui redirige vers auth_service, team_service, battle_service, pokedex_service, et chat_service selon l'URL. La gateway gère aussi le CORS pour autoriser les requêtes depuis le frontend, et vérifie les JWT pour les routes protégées."

---

## 💡 CONCEPTS CLÉS À RETENIR

1. **API Gateway** = point d'entrée unique
2. **Routage** = rediriger vers le bon service
3. **Sécurité** = vérifier API Key / JWT
4. **Cache** = améliorer les performances
5. **Agrégation** = combiner plusieurs services
6. **Rate limiting** = limiter les abus
7. **Single Point of Failure** = risque à mitiger

---

## ✅ AUTO-TEST

1. C'est quoi une API Gateway et pourquoi l'utiliser ?
2. Cite 5 rôles de l'API Gateway
3. Quel est le principal risque et comment le mitiger ?
4. Comment implémenter une sécurité simple avec API Key ?
5. Quelle est la différence entre Nginx et une gateway custom FastAPI ?

Si tu peux répondre → **✅ Fiche maîtrisée !**
