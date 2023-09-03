from typing import Tuple

from src.bot.entities import User

from redis import asyncio as redis

from src.misc.redis_pool import redis_pool

N_TOKENS = 5000
PERIOD_SEC = 900

async def get_remaining_tokens(user: User) -> Tuple[int, int]:
    key = f'remaining_tokens:{user.id}'
    async with redis.Redis(connection_pool=redis_pool) as conn:
        remaining = await conn.get(key)
        if remaining is None:
            return N_TOKENS, -1
        remaining = int(remaining)

        ttl = int(await conn.ttl(key))

        return remaining, ttl

async def decrease_remaining_tokens(user: User, number: int):
    key = f'remaining_tokens:{user.id}'
    async with redis.Redis(connection_pool=redis_pool) as conn:
        remaining = await conn.get(key)
        if remaining is None:
            await conn.set(key, N_TOKENS - number, ex=PERIOD_SEC)
        else:
            await conn.incrby(key, -number)
