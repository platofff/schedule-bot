import asyncio
import logging
from typing import Callable, Union, List, Coroutine

from vkbottle import Bot, Keyboard as VkKeyboard, KeyboardButtonColor, Text
from vkbottle.bot import rules, Message as VkMessage

from src.bot.entities import Message
from src.bot_api.abstract import AbstractBotAPI, CommonMessages, Keyboard
from src.db import db
from src.schedule.class_ import Class


class VkBotAPI(AbstractBotAPI):
    _text_handlers: List[Callable[[Message], Coroutine]] = []

    @staticmethod
    def _keyboard_adapter(k: Keyboard) -> str:
        res = VkKeyboard(one_time=False, inline=False)
        last_row = len(k) - 1
        for i, row in enumerate(k):
            for btn in row:
                res.add(Text(btn.text), color=KeyboardButtonColor[btn.color])
            if i != last_row:
                res.row()
        return res.get_json()

    def __init__(self, token: str):
        AbstractBotAPI.__init__(self)
        logging.getLogger('vkbottle').setLevel(logging.INFO)
        self._bot = Bot(token=token)
        self._bot.labeler.message_view.replace_mention = True

        @self._bot.on.chat_message(rules.ChatActionRule('chat_invite_user'))
        async def handler2(message: VkMessage):
            my_name = await self._bot.api.groups.get_by_id()
            if self._user_id(message) not in db.keys():
                m = CommonMessages.START + '\n'
            else:
                m = ''
            await message.answer(f'{CommonMessages.HELLO}\n'
                                 f'{m}'
                                 f'Для обращения к боту используйте @{my_name[0].screen_name}')

        @self._bot.on.message()
        async def handler(message: VkMessage):
            for h in self._text_handlers:
                asyncio.create_task(h(Message(self, message, message.text, self._user_id(message))))

        self.task = asyncio.create_task(self._bot.run_polling())

    def add_text_handler(self, fn: Callable[[Message], Coroutine]):
        self._text_handlers.append(fn)

    async def send_text(self, ctx: VkMessage, text: str, keyboard: Union[Keyboard, None] = None):
        await ctx.answer(text, keyboard=self._keyboards[keyboard])

    class ClassType(Class):
        def _bold_text(self, text: str) -> str:
            def bc():
                for char in text:
                    if char.isdigit():
                        yield chr(ord(char) + 120764)
                    else:
                        yield char

            return ''.join(bc())

    def _user_id(self, ctx: VkMessage) -> str:
        return f'vk{ctx.peer_id}'
