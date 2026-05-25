# =============================================================================
# POKEDEX SERVICE — routes/pokedex.py
# Routes HTTP de l'API Pokédex
# =============================================================================
# RÔLE DU FICHIER :
# Définit tous les endpoints REST du Pokédex Service.
# Ces routes sont appelées par le frontend Angular pour afficher les Pokémon,
# permettre la recherche, et tirer les équipes aléatoires.
#
# ROUTES EXPOSÉES (après /api/pokedex) :
#   GET /api/pokedex                    → liste paginée des Pokémon
#   GET /api/pokedex/search?name=draca  → recherche par nom
#   GET /api/pokedex/random/{count}     → N Pokémon aléatoires (mode hasard)
#   GET /api/pokedex/types              → liste des types
#   GET /api/pokedex/types/{type}/chart → résistances d'un type
#   GET /api/pokedex/{id}               → données d'un Pokémon par ID/nom
# =============================================================================

from typing import Optional
from fastapi import APIRouter, Query
from app.services.pokeapi_service import (
    get_pokemon, get_random_pokemon, get_type_chart,
    list_pokemon, list_types, search_pokemon
)

# prefix="/api/pokedex" : toutes les routes sont sous ce préfixe
# Correspond à la règle nginx : location /api/pokedex { proxy_pass http://pokedex_service/api/pokedex; }
router = APIRouter(prefix="/api/pokedex", tags=["pokedex"])


# GET /api/pokedex?offset=0&limit=20
# Pagination : offset = position de départ, limit = nombre d'éléments
# Query(20, le=100) : valeur par défaut 20, maximum autorisé 100
@router.get("")
async def pokedex_list(offset: int = 0, limit: int = Query(20, le=100)):
    return await list_pokemon(offset, limit)


# GET /api/pokedex/search?name=char
# Recherche insensible à la casse dans toute la liste des Pokémon
@router.get("/search")
async def search(name: Optional[str] = None):
    return await search_pokemon(name)


# GET /api/pokedex/random/6
# Retourne 6 Pokémon aléatoires avec toutes leurs données (types, stats, image...)
# Utilisé quand un joueur choisit le mode "hasard"
@router.get("/random/{count}")
async def random_pokemon(count: int):
    return await get_random_pokemon(count)


# GET /api/pokedex/types
# Retourne la liste de tous les types depuis PokeAPI
@router.get("/types")
async def types():
    return await list_types()


# GET /api/pokedex/types/feu/chart
# Retourne les données complètes du type Feu (faiblesses, résistances, immunités)
# NB : battle_engine.py utilise son propre TYPE_CHART en dur,
#      cette route est pour l'affichage frontend
@router.get("/types/{type_name}/chart")
async def type_chart(type_name: str):
    return await get_type_chart(type_name)


# GET /api/pokedex/dracaufeu  ou  GET /api/pokedex/6
# IMPORTANT : cette route doit être APRÈS /search, /random, /types
# sinon FastAPI intercepterait /api/pokedex/search comme pokemon_id="search"
# L'ordre des routes dans le fichier compte !
@router.get("/{pokemon_id}")
async def pokemon_detail(pokemon_id: str):
    return await get_pokemon(pokemon_id)
