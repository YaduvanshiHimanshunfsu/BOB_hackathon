"""
api_gateway/redis_client.py
===========================
Async Redis connection pool and Stream operations for telemetry ingestion.
Uses Redis Streams (XADD/XREADGROUP) as a persistent, durable message broker.
"""

import json
import redis.asyncio as aioredis
from api_gateway.config import settings

# Lazy-initialized connection pool
_pool: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Get or create the async Redis connection pool."""
    global _pool
    if _pool is None:
        _pool = aioredis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            password=settings.redis_password or None,
            decode_responses=True,
            max_connections=20,
        )
    return _pool


async def push_to_stream(stream_key: str, data: dict) -> str:
    """
    Push a telemetry payload to a Redis Stream.

    Args:
        stream_key: Redis Stream key name
        data: Dictionary to store as stream entry

    Returns:
        Stream entry ID (e.g., '1718880000000-0')
    """
    redis = await get_redis()
    # Serialize nested objects to JSON strings for Redis flat key-value storage
    flat_data = {}
    for key, value in data.items():
        if isinstance(value, (dict, list)):
            flat_data[key] = json.dumps(value)
        else:
            flat_data[key] = str(value)

    entry_id = await redis.xadd(stream_key, flat_data)
    return entry_id


async def get_stream_length(stream_key: str) -> int:
    """Get the current number of entries in a Redis Stream."""
    redis = await get_redis()
    return await redis.xlen(stream_key)


async def get_latest_risk_score(user_id: str) -> dict | None:
    """Fetch the latest cached risk score for a user from Redis."""
    redis = await get_redis()
    data = await redis.hgetall(f"risk:{user_id}")
    return data if data else None


async def close_redis():
    """Gracefully close the Redis connection pool."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
