# =============================================================================
# POKEDEX SERVICE — core/cache.py
# Cache Redis : système de mise en cache des données de l'API PokeAPI
# =============================================================================
# RÔLE DU FICHIER :
# Le Pokédex Service fait des appels HTTP vers https://pokeapi.co/api/v2
# Chaque appel externe = latence de 100-500ms + limite de débit de l'API publique.
# Redis est utilisé comme cache : on stocke les réponses JSON dans Redis
# avec un TTL de 24h. La prochaine fois qu'on demande le même Pokémon → réponse
# instantanée depuis Redis, sans appel HTTP.
#
# PATTERN : Cache-Aside (ou Lazy Loading)
# 1. Cherche dans Redis
# 2. Si trouvé (cache hit) → retourne directement
# 3. Si non trouvé (cache miss) → appel API externe → stocke dans Redis → retourne
# =============================================================================

import json               # Pour sérialiser/désérialiser les données Python ↔ JSON string
from typing import Any, Optional
import redis.asyncio as aioredis  # Client Redis asynchrone (compatible asyncio)
from app.core.config import settings


# Singleton Redis (même pattern que Kafka producer)
# Une seule connexion au pool Redis pour toute l'application
_redis: aioredis.Redis | None = None


# =============================================================================
# FONCTION : get_redis — Accès au singleton Redis
# =============================================================================
def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        # from_url crée un pool de connexions vers Redis
        # settings.REDIS_URL = "redis://redis:6379/0"
        # /0 = base de données Redis numéro 0 (Redis supporte 16 bases par défaut)
        # decode_responses=True : les réponses Redis sont des str Python (pas des bytes)
        _redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


# =============================================================================
# FONCTION : cache_get — Lire depuis le cache Redis
# =============================================================================
async def cache_get(key: str) -> Optional[Any]:
    r = get_redis()
    # r.get(key) : retourne la valeur stockée ou None si la clé n'existe pas / expirée
    data = await r.get(key)
    # Si la clé existe : on désérialise le JSON string → dict Python
    # Si None : on retourne None (cache miss)
    return json.loads(data) if data else None


# =============================================================================
# FONCTION : cache_set — Écrire dans le cache Redis avec expiration
# =============================================================================
async def cache_set(key: str, value: Any, ttl: int = settings.POKEAPI_CACHE_TTL) -> None:
    r = get_redis()
    # setex = SET with EXpiry
    # key : clé de cache (ex: "pokedex:pokemon:dracaufeu")
    # ttl : Time To Live en secondes (86400 = 24 heures)
    # json.dumps(value) : convertit le dict Python → string JSON pour le stockage
    # Après ttl secondes, Redis supprime automatiquement la clé
    await r.setex(key, ttl, json.dumps(value))


# =============================================================================
# FONCTION : close_redis — Fermer proprement la connexion Redis
# =============================================================================
async def close_redis() -> None:
    global _redis
    if _redis:
        await _redis.aclose()  # Ferme le pool de connexions
        _redis = None


# =============================================================================
# EXEMPLES DE CLÉS REDIS UTILISÉES DANS CE SERVICE
# =============================================================================
# "pokedex:list:0:20"          → liste paginée des Pokémon (offset=0, limit=20)
# "pokedex:pokemon:dracaufeu"  → données complètes du Pokémon Dracaufeu
# "pokedex:pokemon:6"          → même chose par ID
# "pokedex:all"                → liste complète (~1000 Pokémon) pour la recherche
# "pokedex:types"              → liste de tous les types
# "pokedex:type:feu"           → chart du type Feu (depuis PokeAPI)
#
# POURQUOI UN TTL DE 24H ?
# Les données de PokeAPI ne changent pratiquement jamais (Pokémon officiels).
# Un TTL de 24h évite de saturer l'API externe tout en gardant des données fraîches.
