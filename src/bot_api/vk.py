import asyncio
import logging
from typing import Callable, Union, List, Coroutine

from vkbottle import Bot, Keyboard, KeyboardButtonColor, Text
from vkbottle.bot import rules, Message as VkMessage
from src.bot.entities import Message
from src.bot_api.abstract import AbstractBotAPI
from src.db import db
from src.schedule.class_ import Class


class VkBotAPI(AbstractBotAPI):
    _text_handlers: List[Callable[[Message], Coroutine]] = []
    _keyboards = {
        'set': Keyboard(one_time=False, inline=False)
        .add(Text('Пара'), color=KeyboardButtonColor.POSITIVE)
        .add(Text('Пары сегодня'), color=KeyboardButtonColor.PRIMARY)
        .row()
        .add(Text('Пары завтра'), color=KeyboardButtonColor.SECONDARY)
        .add(Text('Сброс'), color=KeyboardButtonColor.NEGATIVE).get_json(),

        'role': Keyboard(one_time=False, inline=False)
        .add(Text('Преподаватель'), color=KeyboardButtonColor.PRIMARY)
        .add(Text('Студент'), color=KeyboardButtonColor.POSITIVE).get_json(),

        'reset_btn': Keyboard(one_time=False, inline=False)
        .add(Text('Сброс'), color=KeyboardButtonColor.NEGATIVE).get_json(),

        'clear': '{"buttons":[],"one_time":true}',

        None: None
    }

    _role_keyboard = Keyboard(one_time=False, inline=False)

    def __init__(self, token: str):
        logging.getLogger('vkbottle').setLevel(logging.INFO)
        self._bot = Bot(token=token)
        self._bot.labeler.message_view.replace_mention = True

        @self._bot.on.chat_message(rules.ChatActionRule('chat_invite_user'))
        async def handler2(message: VkMessage):
            my_name = await self._bot.api.groups.get_by_id()
            if self._user_id(message) not in db.keys():
                m = 'Чтобы продолжить, отправьте мне "Студент" или "Преподаватель"\n'
            else:
                m = ''
            await message.answer('Вас приветствует чат-бот "Расписание НПИ" 😉\n'
                                 f'{m}'
                                 f'Для обращения к боту используйте @{my_name[0].screen_name}')

        @self._bot.on.message()
        async def handler(message: VkMessage):
            for h in self._text_handlers:
                asyncio.create_task(h(Message(self, message, message.text, self._user_id(message))))

        self.task = asyncio.create_task(self._bot.run_polling())

    def add_text_handler(self, fn: Callable[[Message], Coroutine]):
        self._text_handlers.append(fn)

    async def send_text(self, ctx: VkMessage, text: str, keyboard: Union[str, None] = None):
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
