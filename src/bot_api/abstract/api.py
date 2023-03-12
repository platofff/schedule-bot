import asyncio
from abc import ABC, abstractmethod
from typing import Callable, Any, Union, Coroutine

from src.bot_api.abstract.keyboards import Keyboard, keyboards
from src.schedule.class_ import Class


class AbstractBotAPI(ABC):
    task: asyncio.Task
    _keyboards: dict

    @abstractmethod
    def __init__(self):
        self._keyboards = {k: self._keyboard_adapter(v) for k, v in keyboards.items()}

    @abstractmethod
    def add_text_handler(self, fn: Callable[[Any], Coroutine]):
        pass

    @abstractmethod
    async def send_text(self, ctx: Any, text: str, keyboard: Union[str, None] = None):
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
