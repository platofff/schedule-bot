from abc import ABC, abstractmethod
from typing import Callable, Any, Union


class AbstractBotAPI(ABC):
    @abstractmethod
    def add_text_handler(self, fn: Callable[[Any, str], None]):
        pass

    @abstractmethod
    async def send_text(self, ctx: Any, text: str, keyboard: Union[str, None] = None):
        pass

    @abstractmethod
    def bold_text(self, text: str) -> str:
        pass

    @abstractmethod
    def user_id(self, ctx: Any) -> str:
        pass



