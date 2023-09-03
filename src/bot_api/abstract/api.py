import asyncio
from abc import ABC, abstractmethod
from dataclasses import fields
from typing import Callable, Any, Union, Coroutine, Dict

from redis import asyncio as redis

from src.bot_api.abstract.keyboards import Keyboard, Keyboards
from src.misc.redis_pool import redis_pool


class AbstractBotAPI(ABC):
    task: asyncio.Task
    _TYPING_DELAY: int
    _typing_tasks: Dict[int, asyncio.Task] = {}

    @abstractmethod
    def __init__(self):
        self._keyboards: Dict[Union[Keyboard, None], Any] = {None: None}
        for field in fields(Keyboards):
            value = field.default
            self._keyboards[value] = self._keyboard_adapter(value)

    @abstractmethod
    def add_text_handler(self, fn: Callable[[Any], Coroutine]):
        pass

    @abstractmethod
    async def send_text(self, ctx: Any, text: str, keyboard: Union[Keyboard, None] = None):
        pass

    @abstractmethod
    async def get_username(self, ctx: Any) -> str:
        pass

    async def _typing_task(self, chat_id: Any, key: str):
        async with (redis.Redis(connection_pool=redis_pool) as conn):
            while True:
                if await conn.get(key) is None: return
                await self._set_typing_activity(chat_id)
                await asyncio.sleep(self._TYPING_DELAY)

    async def set_typing_state(self, ctx: Any, typing: bool):
        key = f'typing_cache:{self._internal_chat_id(ctx)}'
        async with (redis.Redis(connection_pool=redis_pool) as conn):
            current = await conn.get(key)
            if typing:
                if current is None:
                    self._typing_tasks.update({ctx.peer_id: asyncio.get_event_loop()\
                                              .create_task(self._typing_task(self._internal_chat_id(ctx), key))})
                await conn.incrby(key, 1)
            else:
                if int(current) <= 1:
                    await conn.delete(key)
                else:
                    await conn.incrby(key, -1)

    @staticmethod
    @abstractmethod
    def _keyboard_adapter(k: Keyboard) -> Any:
        pass

    @staticmethod
    @abstractmethod
    def _internal_chat_id(ctx: Any) -> Any:
        pass

    @abstractmethod
    async def _set_typing_activity(self, user_id: str):
        pass