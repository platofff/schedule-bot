import asyncio
from abc import ABC, abstractmethod
from dataclasses import fields
from typing import Callable, Any, Union, Coroutine, Dict

from src.bot_api.abstract.keyboards import Keyboard, Keyboards


class AbstractBotAPI(ABC):
    task: asyncio.Task

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

    @staticmethod
    @abstractmethod
    def _keyboard_adapter(k: Keyboard) -> Any:
        pass
