import asyncio
import logging
from typing import Callable, Union, List, Coroutine, Awaitable

from aiocache import cached
from vkbottle import Bot, Keyboard as VkKeyboard, KeyboardButtonColor, Text
from vkbottle.bot import rules, Message as VkMessage

from src.bot.entities import Message, User
from src.bot_api.abstract import AbstractBotAPI, CommonMessages, Keyboard
from src.misc.cache import cache_params


class VkBotAPI(AbstractBotAPI):
    _text_handlers: List[Callable[[Message], Coroutine]] = []
    _TYPING_DELAY = 3

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
            if await User.get(self._user_id(message), with_children=True) is None:
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

        self.task = asyncio.get_event_loop().create_task(self._bot.run_polling())

    def add_text_handler(self, fn: Callable[[Message], Coroutine]):
        self._text_handlers.append(fn)

    def send_text(self, ctx: VkMessage, text: str, keyboard: Union[Keyboard, None] = None) -> Coroutine:
        return ctx.answer(text, keyboard=self._keyboards[keyboard])

    @cached(**cache_params, namespace='vk_get_username', ttl=3600, key_builder=lambda _, __, from_id: str(from_id))
    async def _get_username(self, from_id: int) -> str:
        user = (await self._bot.api.users.get([from_id]))[0]
        return f'{user.first_name} {user.last_name}'

    def get_username(self, ctx: VkMessage) -> Awaitable[str]:
        return self._get_username(ctx.from_id)

    @staticmethod
    def _user_id(ctx: VkMessage) -> str:
        return f'vk{ctx.peer_id}'

    @staticmethod
    def _internal_chat_id(ctx: VkMessage) -> int:
        return ctx.peer_id

    async def _set_typing_activity(self, peer_id: int):
        await self._bot.api.messages.set_activity(peer_id=peer_id, type='typing')
