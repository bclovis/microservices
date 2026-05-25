# =============================================================================
# POKEDEX SERVICE — services/pokeapi_service.py
# Client PokeAPI avec cache Redis
# =============================================================================
# RÔLE DU FICHIER :
# Ce service est un "proxy intelligent" vers l'API publique https://pokeapi.co
# Il intercepte chaque requête, vérifie si la réponse est dans Redis,
# et ne fait l'appel HTTP externe QUE si nécessaire.
#
# POURQUOI UN SERVICE POKEDEX SÉPARÉ ?
# Plusieurs autres services (battle, team) ont besoin des données Pokémon.
# Au lieu que chacun appelle directement PokeAPI, on centralise :
# - Cohérence : toujours les mêmes données
# - Performance : cache partagé
# - Résilience : si PokeAPI est down, le cache sert les données
# =============================================================================

import random    # Pour la sélection aléatoire de Pokémon (mode "hasard")
from typing import Optional
import httpx     # Client HTTP asynchrone (l'équivalent de "requests" mais async)
from app.core.cache import cache_get, cache_set
from app.core.config import settings

# URL de base de l'API publique Pokémon
BASE = settings.POKEAPI_BASE_URL  # "https://pokeapi.co/api/v2"


# =============================================================================
# FONCTION : _fetch — Appel HTTP vers PokeAPI (privée, préfixe _)
# =============================================================================
async def _fetch(url: str) -> dict:
    # httpx.AsyncClient : client HTTP async avec timeout de 10 secondes
    # "async with" : ferme automatiquement la connexion après l'usage
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url)
        # raise_for_status() : lève une exception si le statut HTTP est >= 400
        # Ex: 404 Not Found → HTTPStatusError → FastAPI retourne 500 ou 404
        resp.raise_for_status()
        return resp.json()  # Désérialise le JSON de la réponse → dict Python


# =============================================================================
# FONCTION : _cached_fetch — Appel avec cache (privée)
# =============================================================================
# Pattern Cache-Aside :
# 1. Cherche dans Redis avec la clé
# 2. Cache hit → retourne directement (pas d'appel HTTP)
# 3. Cache miss → appelle PokeAPI → stocke dans Redis → retourne
async def _cached_fetch(key: str, url: str) -> dict:
    hit = await cache_get(key)  # Cherche dans Redis
    if hit:
        return hit              # Cache HIT : retour instantané (< 1ms)
    # Cache MISS : appel HTTP vers PokeAPI (~200-500ms)
    data = await _fetch(url)
    await cache_set(key, data)  # Stocke dans Redis pour les prochains appels (TTL 24h)
    return data


# =============================================================================
# FONCTIONS PUBLIQUES — Appelées par les routes
# =============================================================================

# Pagination de la liste des Pokémon
# Clé Redis : "pokedex:list:0:20" pour offset=0, limit=20
async def list_pokemon(offset: int = 0, limit: int = 20) -> dict:
    return await _cached_fetch(
        f"pokedex:list:{offset}:{limit}",
        f"{BASE}/pokemon?offset={offset}&limit={limit}"
    )


# Données d'un Pokémon par ID ou nom
# pokemon_id peut être un int (6) ou une str ("dracaufeu")
# PokeAPI accepte les deux formats
async def get_pokemon(pokemon_id: int | str) -> dict:
    return await _cached_fetch(
        f"pokedex:pokemon:{pokemon_id}",
        f"{BASE}/pokemon/{pokemon_id}"
    )


# Recherche de Pokémon par nom (filtre local)
# On charge TOUTE la liste (~10000 Pokémon noms/URLs) et on filtre en mémoire
# Efficace car la liste complète est en cache Redis
async def search_pokemon(name: Optional[str] = None) -> list[dict]:
    # "pokedex:all" = liste complète de tous les Pokémon (noms + URLs)
    all_data = await _cached_fetch("pokedex:all", f"{BASE}/pokemon?limit=10000")
    results = all_data.get("results", [])
    if name:
        # Filtre insensible à la casse : "draca" trouve "dracaufeu", "dracarys"...
        results = [p for p in results if name.lower() in p["name"].lower()]
    return results[:50]  # Limite à 50 résultats maximum


# Sélection aléatoire de N Pokémon avec leurs données complètes
# Utilisé pour le mode "hasard" où les équipes sont tirées au sort
async def get_random_pokemon(count: int = 6) -> list[dict]:
    # On charge les 898 premiers (Gen 1 à 8, pas les formes alternatives)
    all_data = await _cached_fetch("pokedex:all", f"{BASE}/pokemon?limit=898")
    pool = all_data.get("results", [])
    
    # random.sample : tire count éléments SANS remise (pas de doublon)
    # min(count, len(pool)) = sécurité si on demande plus que disponible
    chosen = random.sample(pool, min(count, len(pool)))
    
    details = []
    for p in chosen:
        # L'URL PokeAPI a la forme : "https://pokeapi.co/api/v2/pokemon/6/"
        # On extrait l'ID depuis l'URL en prenant le dernier segment
        pid = p["url"].rstrip("/").split("/")[-1]
        details.append(await get_pokemon(pid))  # Chargé depuis le cache si possible
    return details


# Liste de tous les types Pokémon
async def list_types() -> dict:
    return await _cached_fetch("pokedex:types", f"{BASE}/type")


# Données d'un type spécifique (résistances, faiblesses...)
# Note : battle_engine.py utilise son propre TYPE_CHART hardcodé
# Cette route est exposée pour que le frontend puisse afficher des infos
async def get_type_chart(type_name: str) -> dict:
    return await _cached_fetch(
        f"pokedex:type:{type_name}",
        f"{BASE}/type/{type_name}"
    )

# =============================================================================
# POURQUOI HTTPX ET PAS REQUESTS ?
# =============================================================================
# requests est SYNCHRONE : pendant l'appel HTTP, Python attend et ne peut rien faire
# httpx.AsyncClient est ASYNC : pendant l'attente réseau, FastAPI peut traiter
# d'autres requêtes. Avec requests, un seul appel à PokeAPI bloquerait tout le serveur.
