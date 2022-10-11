import asyncio
import logging
import os
from typing import Callable, Union

from vkbottle import Bot, Keyboard, KeyboardButtonColor, Text
from vkbottle.bot import Message

from abstract import AbstractBotAPI


class VkBotAPI(AbstractBotAPI):
    _text_handlers = []
    _keyboard = Keyboard(one_time=False, inline=False)
    _role_keyboard = Keyboard(one_time=False, inline=False)

    def __init__(self):
        logging.getLogger('vkbottle').setLevel(logging.INFO)
        self._bot = Bot(token=os.getenv('VK_BOT_TOKEN'))

        @self._bot.on.message()
        async def handle(message: Message):
            for h in self._text_handlers:
                asyncio.create_task(h(message, message.text))

        self._keyboard.add(Text('Пара'), color=KeyboardButtonColor.POSITIVE)
        self._keyboard.add(Text('Пары сегодня'), color=KeyboardButtonColor.PRIMARY)
        self._keyboard.row()
        self._keyboard.add(Text('Пары завтра'), color=KeyboardButtonColor.SECONDARY)
        self._keyboard.add(Text('Сброс'), color=KeyboardButtonColor.NEGATIVE)

        self._role_keyboard.add(Text('Преподаватель'), color=KeyboardButtonColor.PRIMARY)
        self._role_keyboard.add(Text('Студент'), color=KeyboardButtonColor.POSITIVE)

        asyncio.create_task(self._bot.run_polling())

    def add_text_handler(self, fn: Callable[[Message, str], None]):
        self._text_handlers.append(fn)

    async def send_text(self, ctx: Message, text: str, keyboard: Union[str, None] = None):
        if keyboard is None:
            pass
        elif keyboard == 'set':
            keyboard = self._keyboard
        elif keyboard == 'role':
            keyboard = self._role_keyboard
        elif keyboard == 'clear':
            keyboard = '{"buttons":[],"one_time":true}'
        await ctx.answer(text, keyboard=keyboard)

    def bold_text(self, text: str) -> str:
        def bc():
            for char in text:
                if char.isdigit():
                    yield chr(ord(char) + 120764)
                else:
                    yield char

        return ''.join(bc())

    def user_id(self, ctx: Message) -> str:
        return f'vk{ctx.peer_id}'
