import asyncio
import logging
from os import getenv

from src.gpt.keys import OpenAIKeysManager
from src.misc.clear_typing_caches import clear_typing_caches

logging.basicConfig(level=logging.INFO if getenv('DEBUG') is None else logging.DEBUG)

from src import db
from src.bot.bot import Bot
from src.bot_api.telegram import TelegramBotAPI
from src.bot_api.vk import VkBotAPI

async def main():
    apis = []
    #openai.api_key = os.environ["OPENAI_KEY"]
    vk_token = getenv('VK_BOT_TOKEN')
    tg_token = getenv('TG_BOT_TOKEN')
    if vk_token:
        apis.append(VkBotAPI(vk_token))
    if tg_token:
        apis.append(TelegramBotAPI(tg_token))
    await asyncio.gather(db.init(), OpenAIKeysManager.load_keys(), clear_typing_caches())
    bot = Bot(apis)
    await bot.run()

loop = asyncio.new_event_loop()
try:
    loop.run_until_complete(main())
finally:
    loop.close()
