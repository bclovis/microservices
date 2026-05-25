from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx
from datetime import datetime, timedelta

app = FastAPI(title="API Gateway")

# URLs des microservices
USERS_SERVICE = "http://localhost:8001"
ORDERS_SERVICE = "http://localhost:8002"

# Clé API pour l'authentification
API_KEY = "secret-api-key-123"

# ===== SYSTÈME DE CACHE =====
# Cache en mémoire avec expiration
cache = {}
CACHE_DURATION = timedelta(minutes=10)  # 10 minutes

# ===== RATE LIMITING =====
# Dictionnaire pour stocker le dernier temps de requête par IP
# Format : {"ip_address": datetime_derniere_requete}
rate_limit_store = {}
RATE_LIMIT_SECONDS = 20  # 1 requête toutes les 20 secondes

def get_from_cache(key: str):
    """
    Récupère une valeur du cache si elle existe et n'a pas expiré
    
    Returns:
        Les données si en cache et valides, None sinon
    """
    if key in cache:
        entry = cache[key]
        # Vérifier si le cache n'a pas expiré
        if datetime.now() < entry["expires_at"]:
            print(f"[CACHE HIT] Récupération depuis le cache : {key}")
            return entry["data"]
        else:
            # Cache expiré, on le supprime
            print(f"[CACHE EXPIRED] Cache expiré pour : {key}")
            del cache[key]
    
    print(f"[CACHE MISS] Pas de cache pour : {key}")
    return None

def set_in_cache(key: str, data):
    """
    Stocke une valeur dans le cache avec une date d'expiration
    """
    cache[key] = {
        "data": data,
        "expires_at": datetime.now() + CACHE_DURATION
    }
    print(f"[CACHE SET] Mise en cache : {key} (expire dans 10 min)")


# ===== MIDDLEWARE D'AUTHENTIFICATION =====
@app.middleware("http")
async def verify_api_key(request: Request, call_next):
    """
    Middleware qui vérifie la clé API sur TOUTES les requêtes
    
    Fonctionnement :
    1. Récupère le header X-API-Key de la requête
    2. Compare avec la clé attendue
    3. Si mauvaise clé ou absente → erreur 401
    4. Si bonne clé → la requête continue normalement
    """
    # On permet l'accès à la racine sans clé (pour vérifier que le service fonctionne)
    if request.url.path == "/":
        response = await call_next(request)
        return response
    
    # Récupérer la clé API depuis les headers
    api_key = request.headers.get("X-API-Key")
    
    # Vérifier si la clé est correcte
    if api_key != API_KEY:
        return JSONResponse(
            status_code=401,
            content={"error": "Unauthorized", "message": "Invalid or missing API key"}
        )
    
    # Si tout est OK, on continue vers la route demandée
    response = await call_next(request)
    return response

# ===== MIDDLEWARE DE RATE LIMITING =====
@app.middleware("http")
async def rate_limiter(request: Request, call_next):
    """
    Middleware de limitation du débit (Rate Limiting)
    
    Limite : 1 requête toutes les 20 secondes par adresse IP
    
    Fonctionnement :
    1. Récupère l'IP du client
    2. Vérifie quand il a fait sa dernière requête
    3. Si < 20 secondes → bloqué avec erreur 429
    4. Si >= 20 secondes → OK, on met à jour le timestamp
    """
    # On exclut la racine du rate limiting
    if request.url.path == "/":
        response = await call_next(request)
        return response
    
    # Récupérer l'IP du client
    client_ip = request.client.host
    
    # Vérifier le rate limiting
    current_time = datetime.now()
    
    if client_ip in rate_limit_store:
        last_request_time = rate_limit_store[client_ip]
        time_elapsed = (current_time - last_request_time).total_seconds()
        
        if time_elapsed < RATE_LIMIT_SECONDS:
            # Trop de requêtes ! On bloque
            wait_time = RATE_LIMIT_SECONDS - time_elapsed
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "message": f"Rate limit exceeded. Please wait {wait_time:.1f} seconds."
                }
            )
    
    # Mettre à jour le timestamp de la dernière requête
    rate_limit_store[client_ip] = current_time
    
    # Continuer vers la route
    response = await call_next(request)
    return response


# Données des items stockées dans la gateway
ITEMS = [
    {"id": 1, "name": "Laptop", "category": "Electronics"},
    {"id": 2, "name": "Mouse", "category": "Electronics"},
    {"id": 3, "name": "Desk", "category": "Furniture"},
    {"id": 4, "name": "Chair", "category": "Furniture"},
]

@app.get("/")
def root():
    return {"service": "API Gateway", "status": "running"}

@app.get("/items")
def get_items():
    """Retourne la liste des items (stockés localement dans la gateway)"""
    return {"items": ITEMS}

@app.get("/users")
async def get_users():
    """
    Route vers le service Users avec CACHE
    
    1. Vérifie si les users sont en cache
    2. Si oui → retourne depuis le cache
    3. Si non → appelle le microservice et met en cache
    """
    cache_key = "users"
    
    # Essayer de récupérer depuis le cache
    cached_data = get_from_cache(cache_key)
    if cached_data is not None:
        return cached_data
    
    # Pas en cache → appeler le microservice
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{USERS_SERVICE}/users")
        data = response.json()
    
    # Stocker en cache pour les prochaines requêtes
    set_in_cache(cache_key, data)
    
    return data

@app.get("/orders/{user}")
async def get_orders(user: str):
    """
    Route vers le service Orders avec CACHE
    Le cache est spécifique à chaque utilisateur
    """
    cache_key = f"orders_{user}"
    
    # Essayer de récupérer depuis le cache
    cached_data = get_from_cache(cache_key)
    if cached_data is not None:
        return cached_data
    
    # Pas en cache → appeler le microservice
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{ORDERS_SERVICE}/orders/{user}")
        data = response.json()
    
    # Stocker en cache
    set_in_cache(cache_key, data)
    
    return data

# ===== ENDPOINTS D'AGRÉGATION =====

@app.get("/poubelle")
async def get_poubelle():
    """
    Agrégation de données : Users + Items
    
    Combine les données de 2 sources :
    - Liste des users (depuis le microservice users)
    - Liste des items (stockés localement)
    
    Retourne le tout dans une seule réponse
    """
    # Récupérer les users depuis le microservice
    async with httpx.AsyncClient() as client:
        users_response = await client.get(f"{USERS_SERVICE}/users")
        users_data = users_response.json()
    
    # Combiner avec les items locaux
    return {
        "users": users_data.get("users", []),
        "items": ITEMS
    }

@app.get("/profile/{user}")
async def get_profile(user: str):
    """
    Agrégation de données : User + ses commandes
    
    Combine les données pour un utilisateur spécifique :
    - Informations de l'utilisateur (depuis le microservice users)
    - Ses commandes (depuis le microservice orders)
    
    Retourne le profil complet de l'utilisateur
    """
    async with httpx.AsyncClient() as client:
        # Appels parallèles aux 2 microservices
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
    
    # Construire le profil
    return {
        "user": user_info,
        "orders": orders_data.get("orders", [])
    }
