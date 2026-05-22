import json
from typing import Any, Optional
import redis.asyncio as aioredis
from app.core.config import settings

_redis: aioredis.Redis | None = None

def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis

async def cache_get(key: str) -> Optional[Any]:
    r = get_redis()
    data = await r.get(key)
    return json.loads(data) if data else None

async def cache_set(key: str, value: Any, ttl: int = settings.POKEAPI_CACHE_TTL) -> None:
    r = get_redis()
    await r.setex(key, ttl, json.dumps(value))

async def close_redis() -> None:
    global _redis
    if _redis:
        await _redis.aclose()
        _redis = None