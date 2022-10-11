import asyncio
import logging

from src.bot import Bot
from src.telegram import TelegramBotAPI
from src.vk import VkBotAPI


async def main():
    apis = [VkBotAPI(), TelegramBotAPI()]
    bot = Bot(apis)
    await asyncio.sleep(float('+inf'))

loop = asyncio.new_event_loop()
try:
    loop.run_until_complete(main())
finally:
    loop.close()
