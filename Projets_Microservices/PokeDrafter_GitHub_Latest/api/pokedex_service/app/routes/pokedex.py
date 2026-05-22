from typing import Optional
from fastapi import APIRouter, Query
from app.services.pokeapi_service import get_pokemon, get_random_pokemon, get_type_chart, list_pokemon, list_types, search_pokemon

router = APIRouter(prefix="/api/pokedex", tags=["pokedex"])

@router.get("")
async def pokedex_list(offset: int = 0, limit: int = Query(20, le=100)):
    return await list_pokemon(offset, limit)

@router.get("/search")
async def search(name: Optional[str] = None):
    return await search_pokemon(name)

@router.get("/random/{count}")
async def random_pokemon(count: int):         
    return await get_random_pokemon(count)

@router.get("/types")
async def types():
    return await list_types()

@router.get("/types/{type_name}/chart")
async def type_chart(type_name: str):
    return await get_type_chart(type_name)

@router.get("/{pokemon_id}")
async def pokemon_detail(pokemon_id: str):
    return await get_pokemon(pokemon_id)