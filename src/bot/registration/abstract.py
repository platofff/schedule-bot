from abc import ABC, abstractmethod
from typing import Callable, Coroutine, Dict, Type

from src.bot.entities import Message, User


class AbstractRegistration(ABC):
    USER_TYPE: Type[User]
    FIELD_SETTERS: Dict[str, Callable[[Message, User], Coroutine]]

    @staticmethod
    @abstractmethod
    async def start(msg: Message):
        pass
