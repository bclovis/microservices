import random
from typing import Optional
import httpx
from app.core.cache import cache_get, cache_set
from app.core.config import settings

BASE = settings.POKEAPI_BASE_URL

async def _fetch(url: str) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.json()

async def _cached_fetch(key: str, url: str) -> dict:
    hit = await cache_get(key)
    if hit:
        return hit
    data = await _fetch(url)
    await cache_set(key, data)
    return data

async def list_pokemon(offset: int = 0, limit: int = 20) -> dict:
    return await _cached_fetch(f"pokedex:list:{offset}:{limit}", f"{BASE}/pokemon?offset={offset}&limit={limit}")

async def get_pokemon(pokemon_id: int | str) -> dict:
    return await _cached_fetch(f"pokedex:pokemon:{pokemon_id}", f"{BASE}/pokemon/{pokemon_id}")

async def search_pokemon(name: Optional[str] = None) -> list[dict]:
    all_data = await _cached_fetch("pokedex:all", f"{BASE}/pokemon?limit=10000")
    results = all_data.get("results", [])
    if name:
        results = [p for p in results if name.lower() in p["name"].lower()]
    return results[:50]

async def get_random_pokemon(count: int = 6) -> list[dict]:
    all_data = await _cached_fetch("pokedex:all", f"{BASE}/pokemon?limit=898")
    pool = all_data.get("results", [])
    chosen = random.sample(pool, min(count, len(pool)))
    details = []
    for p in chosen:
        pid = p["url"].rstrip("/").split("/")[-1]
        details.append(await get_pokemon(pid))
    return details

async def list_types() -> dict:
    return await _cached_fetch("pokedex:types", f"{BASE}/type")

async def get_type_chart(type_name: str) -> dict:
    return await _cached_fetch(f"pokedex:type:{type_name}", f"{BASE}/type/{type_name}")