import datetime
import logging
from abc import ABC
from bisect import bisect_left
from dataclasses import field, dataclass
from time import strptime
from typing import List, Type, Union

from src.bot.commands._abstract import AbstractCommand
from src.bot.entities import Message, User
from src.gpt import get_gpt_response, GPTMessage
from src.gpt.gpt import GPTOutputFunction, GPTStringEnum, GPTIntegerEnum
from src.misc.class_status import ClassStatus
from src.misc.weekdays import WEEKDAYS
from src.schedule.class_ import Class
from src.schedule.schedule import Schedule, format_classes

triggers = None

@dataclass
class DaySchedule:
    date: datetime.date
    classes: List[Class]
    class_index: int

class ClassIndex(GPTIntegerEnum):
    possible_values = frozenset(range(0, 7))

class ScheduleFunction(GPTOutputFunction, ABC):
    @classmethod
    def format_result(cls, result: Union[DaySchedule, None]):
        if result is None:
            return 'Расписание не найдено!'

        now = datetime.datetime.now().date()
        if result.date == now:
            default_status = None
        elif result.date > now:
            default_status = ClassStatus.NEXT
        else:
            default_status = ClassStatus.PAST
        return f'''Расписание на {result.date.strftime('%d.%m.%Y')}, {WEEKDAYS[result.date.weekday()]}
{format_classes(result.classes, result.class_index, default_status)}'''


@dataclass
class DayScheduleFunction(ScheduleFunction):
    name: str = field(default='print_classes')
    classes: List[Class] = field(default=None)

    async def __call__(self,date: str = datetime.datetime.now().strftime('%Y-%m-%d'), offset: int = 0,
                       class_index: ClassIndex = 0) -> DaySchedule:
        """Prints classes from user's s for a date. 'date' or 'offset' should be specified

        Args:
            date: YYYY-MM-DD, default is today
            offset: offset in days: tomorrow is 1, yesterday is -1
            class_index: highlighted class index (1-6). 0 to not highlight
        """

        logging.info(f'Calling {self.name} with date={date}, offset={offset}, class_index={class_index}')

        delta = datetime.timedelta(days=offset)
        sdate = strptime(date, '%Y-%m-%d')
        date_ = datetime.datetime(sdate.tm_year, sdate.tm_mon, sdate.tm_mday)
        date_ += delta
        date = datetime.date(date_.year, date_.month, date_.day)

        classes = list(filter(lambda x: x.date == date, self.classes))

        if not classes:
            return DaySchedule(date, classes, 0)

        first = classes[0].class_
        last = classes[-1].class_

        if class_index != 0:
            if class_index < first:
                class_index = first
            elif class_index > last:
                class_index = last

        return DaySchedule(date, classes, class_index)


class SearchDirection(GPTStringEnum):
    possible_values = frozenset({'closest', 'latest'})

@dataclass
class SearchAndPrintFunction(ScheduleFunction):
    name: str = field(default='search_class')
    s: Schedule = field(default=None)
    ClassTypesEnum: Type[GPTStringEnum] = field(default=None)
    DisciplinesEnum: Type[GPTStringEnum] = field(default=None)

    async def __call__(self, direction: SearchDirection, discipline: DisciplinesEnum = None,
                       class_type: ClassTypesEnum = None) -> Union[None, DaySchedule]:
        """Prints closest or latest class by criteria

        Args:
            direction: search direction, closest or latest
            discipline: discipline name
            class_type: class type name
        """

        logging.info(f'Calling {self.name} with direction={direction}, discipline={discipline}, '
                     f'class_type={class_type}')

        start_idx = bisect_left(self.s.classes, self.s.now)
        if start_idx >= len(self.s.classes):
            return None

        search_range = range(start_idx, len(self.s.classes)) if direction == 'closest'\
            else range(start_idx, -1, -1)
        for i in search_range:
            c = self.s.classes[i]
            if (discipline is None or c.discipline == discipline) and \
                (class_type is None or c.type == class_type):
                classes = list(filter(lambda x: x.date == c.date, self.s.classes))
                return DaySchedule(c.date, classes, c.class_)

        return None

    def get_args_types(self):
        res = super().get_args_types()
        res['discipline'] = self.DisciplinesEnum
        res['class_type'] = self.ClassTypesEnum
        return res


class Command(AbstractCommand):
    @classmethod
    async def run(cls, msg: Message, user: User):
        s = user.schedule

        class DisciplinesEnum(GPTStringEnum):
            possible_values = frozenset(s.disciplines_set)

        class ClassTypesEnum(GPTStringEnum):
            possible_values = frozenset(s.class_types_set)

        now = datetime.datetime.now()

        text = await get_gpt_response([
            GPTMessage(role=GPTMessage.Role.SYSTEM, content=now.strftime(f'''University s application
Now is %Y-%m-%d %H:%M MSK, %A\n''') + f'User is {s.role} {user.username}'),
            GPTMessage(role=GPTMessage.Role.USER, content=msg.text)
        ], [
            DayScheduleFunction(classes=s.classes),
            SearchAndPrintFunction(s=s,
                                   DisciplinesEnum=DisciplinesEnum, ClassTypesEnum=ClassTypesEnum)
        ])

        await msg.api.send_text(msg.ctx, text)
