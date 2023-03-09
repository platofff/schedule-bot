from dataclasses import dataclass
from typing import Any, Union
from abc import ABC

from src.bot_api.abstract import AbstractBotAPI


@dataclass
class Message:
    api: AbstractBotAPI
    ctx: Any
    text: str
    sid: str


class User(ABC):
    pass


@dataclass
class Student(User):
    faculty: Union[None, str] = None
    _year: Union[None, int] = None

    @property
    def year(self) -> Union[int, None]:
        return self._year

    @year.setter
    def year(self, v: int) -> None:
        assert 1 <= v <= 6
        self._year = v

    group: Union[None, str] = None


@dataclass
class Lecturer(User):
    name: Union[None, str] = None
