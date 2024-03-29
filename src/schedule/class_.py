import datetime
from abc import ABC
from dataclasses import dataclass, asdict
from typing import Dict, Union


@dataclass
class ClassInterval:
    start: str
    end: str


@dataclass
class ComparableClass:
    date: datetime.date
    class_: int

    def __lt__(self, other):
        if self.date < other.date:
            return True
        if self.date > other.date:
            return False
        return self.class_ < other.class_

@dataclass
class BaseClass(ComparableClass):
    week: int
    day: int
    interval: ClassInterval

@dataclass
class Class(ABC, BaseClass):
    discipline: str
    type: str
    auditorium: str
    groups: str

    def simplified(self) -> Dict[str, Union[int, str]]:
        result = asdict(self)
        del result['week']
        return result

    def __str__(self):
        r = f'{self.interval.start}–{self.interval.end} {self.auditorium}\n' \
            f'{self.discipline} ({self.type})'
        return r

@dataclass
class StudentClass(Class):
    lecturer: str
    def __str__(self):
        r = Class.__str__(self)
        r += f'\n{self.lecturer}'
        return r
@dataclass
class LecturerClass(Class):
    def __str__(self):
        r = Class.__str__(self)
        r += f'\n{self.groups}'
        return r
