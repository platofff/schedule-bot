import asyncio
from abc import ABC, abstractmethod
from dataclasses import fields
from typing import Callable, Any, Union, Coroutine, Dict

from src.bot_api.abstract.keyboards import Keyboard, Keyboards
from src.schedule.class_ import Class


class AbstractBotAPI(ABC):
    task: asyncio.Task
    _keyboards: Dict[Union[Keyboard, None], Any] = {None: None}

    @abstractmethod
    def __init__(self):
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
    def _user_id(self, ctx: Any) -> str:
        pass

    class ClassType(Class, ABC):
        pass

    @staticmethod
    @abstractmethod
    def _keyboard_adapter(k: Keyboard) -> Any:
        pass
