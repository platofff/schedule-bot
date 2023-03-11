from abc import ABC, abstractmethod

from src.bot.entities import Message
from src.schedule.schedule import Schedule


class AbstractCommand(ABC):
    @classmethod
    @abstractmethod
    async def run(cls, msg: Message, s: Schedule):
        pass
