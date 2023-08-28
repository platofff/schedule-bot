from dataclasses import dataclass
from typing import Any, Optional

from beanie import Document, Indexed
from pydantic import Field, conint

from src.bot_api.abstract import AbstractBotAPI


@dataclass
class Message:
    api: AbstractBotAPI
    ctx: Any
    text: str
    from_id: str


class User(Document):
    id: str = Field(default_factory=str)
    username: Optional[str] = Field(default=None, exclude=True, repr=False)
    schedule: Optional[Any] = Field(default=None, exclude=True, repr=False)

    class Settings:
        name = 'users'
        is_root = True

class Student(User):
    faculty: Optional[str]
    year: Optional[conint(ge=1, le=6)]
    group: Optional[str]

    def __hash__(self):
        return hash((self.id, self.faculty, self.year, self.group))

class Lecturer(User):
    name: Optional[str]

    def __hash__(self):
        return hash((self.id, self.name))
