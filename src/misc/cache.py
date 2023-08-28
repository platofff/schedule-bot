from os import environ

import redis.asyncio as redis
from aiocache import Cache
from aiocache.serializers import PickleSerializer

cache_params = {
    'cache': Cache.REDIS,
    'serializer': PickleSerializer(),
    'endpoint': environ['REDIS_HOST'],
    'port': environ['REDIS_PORT']
}
