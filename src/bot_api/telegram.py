import asyncio
import logging
from typing import Callable, Union, List, Coroutine

from aiogram import Bot, Dispatcher
from aiogram.types import Message as TgMessage, ReplyKeyboardMarkup, KeyboardButton

from src.bot.entities import Message, User
from src.bot_api.abstract import AbstractBotAPI, CommonMessages, Keyboard


class TelegramBotAPI(AbstractBotAPI):
    _text_handlers: List[Callable[[Message], Coroutine]] = []

    @staticmethod
    def _keyboard_adapter(k: Keyboard) -> ReplyKeyboardMarkup:
        res = ReplyKeyboardMarkup(one_time_keyboard=False, resize_keyboard=True)
        for row in k:
            res.row(*map(lambda x: KeyboardButton(x.text), row))
        return res

    def __init__(self, token: str):
        AbstractBotAPI.__init__(self)
        logging.getLogger('aiogram').setLevel(logging.INFO)
        self._bot = Bot(token)
        self._dp = Dispatcher(self._bot)

        @self._dp.message_handler()
        async def handle(message: TgMessage):
            if message.text == '/start':
                if await User.get(self._user_id(message), with_children=True) is None:
                    await message.answer(CommonMessages.HELLO)
                text = 'Сброс'
            else:
                text = message.text
            for h in self._text_handlers:
                asyncio.create_task(h(Message(self, message, text, self._user_id(message))))

        self.task = asyncio.get_event_loop().create_task(self._dp.start_polling())

    def add_text_handler(self, fn: Callable[[Message], Coroutine]):
        self._text_handlers.append(fn)

    async def send_text(self, ctx: TgMessage, text: str, keyboard: Union[Keyboard, None] = None):
        await ctx.answer(text, parse_mode='HTML', reply_markup=self._keyboards[keyboard])

    async def get_username(self, ctx: TgMessage) -> str:
        return f'{ctx.from_user.first_name} {ctx.from_user.last_name}'.strip()

    @staticmethod
    def _user_id(ctx: TgMessage) -> str:
        return f'tg{ctx.from_user}'
