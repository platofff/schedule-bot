import asyncio
import logging
import os
from typing import Callable, Union

from aiogram import Bot, Dispatcher
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

from src.abstract import AbstractBotAPI


class TelegramBotAPI(AbstractBotAPI):
    _text_handlers = []
    _keyboard = ReplyKeyboardMarkup(one_time_keyboard=False, resize_keyboard=True)
    _role_keyboard = ReplyKeyboardMarkup(one_time_keyboard=False, resize_keyboard=True)

    def __init__(self):
        logging.getLogger('aiogram').setLevel(logging.INFO)
        self._bot = Bot(os.getenv('TG_BOT_TOKEN'))
        self._dp = Dispatcher(self._bot)

        @self._dp.message_handler()
        async def handle(message: Message):
            for h in self._text_handlers:
                asyncio.create_task(h(message, message.text))

        asyncio.get_event_loop().create_task(self._dp.start_polling())

        self._keyboard_markup = self._keyboard.row(KeyboardButton('Пара'), KeyboardButton('Пары сегодня'))\
                                              .row(KeyboardButton('Пары завтра'), KeyboardButton('Сброс'))
        self._role_keyboard_markup = self._role_keyboard.row(KeyboardButton('Преподаватель'), KeyboardButton('Студент'))

    def add_text_handler(self, fn: Callable[[Message, str], None]):
        self._text_handlers.append(fn)

    async def send_text(self, ctx: Message, text: str, keyboard: Union[str, None] = None):
        if keyboard is None:
            reply_markup = None
        elif keyboard == 'set':
            reply_markup = self._keyboard_markup
        elif keyboard == 'role':
            reply_markup = self._role_keyboard_markup
        else:
            reply_markup = ReplyKeyboardRemove()
        await ctx.answer(text, parse_mode='HTML', reply_markup=reply_markup)

    def bold_text(self, text: str) -> str:
        return f'<b>{text}</b>'

    def user_id(self, ctx: Message) -> str:
        return f'tg{ctx.from_user}'
