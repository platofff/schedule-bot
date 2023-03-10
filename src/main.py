from os import getenv
import asyncio

from src.bot.bot import Bot
from src.bot_api.telegram import TelegramBotAPI
from src.bot_api.vk import VkBotAPI


async def main():
    apis = []
    vk_token = getenv('VK_BOT_TOKEN')
    tg_token = getenv('TG_BOT_TOKEN')
    if vk_token:
        apis.append(VkBotAPI(vk_token))
    if tg_token:
        apis.append(TelegramBotAPI(tg_token))
    bot = Bot(apis)
    await bot.run()

loop = asyncio.new_event_loop()
try:
    loop.run_until_complete(main())
finally:
    loop.close()
