from abc import ABC, abstractmethod
from types import SimpleNamespace

from src.bot.entities import Message


class AbstractCommand(ABC):
    @classmethod
    @abstractmethod
    async def run(cls, msg: Message, s: SimpleNamespace):
        pass
