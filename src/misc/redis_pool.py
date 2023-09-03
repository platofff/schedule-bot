from os import environ

from redis import asyncio as redis

redis_pool = redis.ConnectionPool(host=environ['REDIS_HOST'], port=int(environ['REDIS_PORT']))
