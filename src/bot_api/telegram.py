import asyncio
import logging
from typing import Callable, Union, List, Coroutine

from aiogram import Bot, Dispatcher
from aiogram.types import Message as TgMessage, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

from src.bot.entities import Message
from src.bot_api.abstract import AbstractBotAPI
from src.schedule.class_ import Class


class TelegramBotAPI(AbstractBotAPI):
    _text_handlers: List[Callable[[Message], Coroutine]] = []
    _keyboards = {
        'set': ReplyKeyboardMarkup(one_time_keyboard=False, resize_keyboard=True)
        .row(KeyboardButton('Пара'), KeyboardButton('Пары сегодня'))
        .row(KeyboardButton('Пары завтра'), KeyboardButton('Сброс')),

        'role': ReplyKeyboardMarkup(one_time_keyboard=False, resize_keyboard=True)
        .row(KeyboardButton('Преподаватель'), KeyboardButton('Студент')),

        'reset_btn': ReplyKeyboardMarkup(one_time_keyboard=False, resize_keyboard=True)
        .row(KeyboardButton('Сброс')),

        'clear': ReplyKeyboardRemove(),
        None: None
    }

    def __init__(self, token: str):
        logging.getLogger('aiogram').setLevel(logging.INFO)
        self._bot = Bot(token)
        self._dp = Dispatcher(self._bot)

        @self._dp.message_handler()
        async def handle(message: TgMessage):
            text = message.text if message.text != '/start' else 'Сброс'
            for h in self._text_handlers:
                asyncio.create_task(h(Message(self, message, text, self._user_id(message))))

        self.task = asyncio.get_event_loop().create_task(self._dp.start_polling())

    def add_text_handler(self, fn: Callable[[Message], Coroutine]):
        self._text_handlers.append(fn)

    async def send_text(self, ctx: TgMessage, text: str, keyboard: Union[str, None] = None):
        await ctx.answer(text, parse_mode='HTML', reply_markup=self._keyboards[keyboard])

    class ClassType(Class):
        def _bold_text(self, text: str) -> str:
            return f'<b>{text}</b>'

    def _user_id(self, ctx: TgMessage) -> str:
        return f'tg{ctx.from_user}'
