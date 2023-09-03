import asyncio

from redis import asyncio as redis

from src.misc.redis_pool import redis_pool


async def clear_typing_caches():
    async with redis.Redis(connection_pool=redis_pool) as conn:
        await asyncio.gather(*(conn.delete(key) for key in await conn.keys('typing_cache:*')))