import aiohttp
from asyncache import cached
from cachetools import TTLCache


@cached(TTLCache(4096, 60))
async def request(call: str, v: int = 1) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://schedule.npi-tu.ru/api/v{v}/{call}') as resp:
            res = await resp.json(content_type=None)
    return res
