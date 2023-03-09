import asyncio
from abc import ABC, abstractmethod
from typing import Callable, Any, Union, Coroutine

from src.schedule.class_ import Class


class AbstractBotAPI(ABC):
    task: asyncio.Task

    @abstractmethod
    def __init__(self, token: str):
        pass

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
