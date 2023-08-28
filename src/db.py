from os import environ

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from src.bot.entities import User, Student, Lecturer


async def init():
    client = AsyncIOMotorClient(f'mongodb://{environ["MONGO_USER"]}:{environ["MONGO_PASSWORD"]}@'
                                f'{environ["MONGO_HOST"]}:{environ["MONGO_PORT"]}')
    await init_beanie(client.schedule_bot, document_models=[User, Student, Lecturer])
