from abc import ABC, abstractmethod

from src.bot.entities import Message, User
from src.schedule.schedule import Schedule


class AbstractCommand(ABC):
    @classmethod
    @abstractmethod
    async def run(cls, msg: Message, user: User):
        pass
