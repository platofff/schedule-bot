import copy
import re
from bisect import bisect_left
from dataclasses import dataclass
from datetime import datetime, time
from functools import singledispatchmethod
from itertools import chain
from math import floor
from typing import Type, Union, List, Tuple, Callable, Dict, Set

from aiocache import cached

from src.bot.entities import Student, Lecturer, User
from src.misc.cache import cache_params
from src.misc.class_status import ClassStatus
from src.misc.dates import utc_timestamp_ms, js_weekday
from src.schedule.api import request
from src.schedule.class_ import Class, ClassInterval, BaseClass, StudentClass, LecturerClass


def format_classes(classes: List[Class], current: int = 0, default_status: Union[str, None] = None):
    res = []

    c_status = ClassStatus.CURRENT
    if default_status is None:
        n_status = ClassStatus.NEXT
        p_status = ClassStatus.PAST
    else:
        n_status = default_status
        p_status = default_status

    for c in classes:
        if c.class_ > current:
            res.append(f'{n_status} {c}')
        elif c.class_ == current:
            res.append(f'{c_status} {c}')
        else:
            res.append(f'{p_status} {c}')
    return '\n\n'.join(res)

@dataclass
class ClassType:
    name: str
    color: str


class Schedule:
    def get_interval(self, i: Union[int, str]) -> ClassInterval:
        return ClassInterval(self.ci[str(i)]['start'], self.ci[str(i)]['end'])

    def _get_now(self) -> BaseClass:
        res = dict()
        d = utc_timestamp_ms()
        res['week'] = 1 if floor((d - self.mfws) / 604_800_000) % 2 == 0 else 2
        #dt = datetime.now()
        dt = datetime.now()
        res['day'] = js_weekday(dt)
        if res['day'] == 0:
            res['week'] = 1 if res['week'] == 2 else 1
        for i, _ci in self.ci.items():
            h, m = tuple(map(int, _ci['end'].split(':')))
            t = time(h, m)
            dt_t = datetime.combine(dt.date(), t)
            if dt <= dt_t:
                res['class_'] = int(i)
                res['interval'] = self.get_interval(i)
                break
        else:
            res['interval'] = None
            res['class_'] = 9
        res['date'] = dt.date()
        return BaseClass(**res)

    def get_closest(self, now: BaseClass) -> Class:
        res = bisect_left(self.classes, now, 0)
        if res == len(self.classes):
            res = 0
        return self.classes[res]

    async def _process(self):
        self.ci = await request('class-intervals')

        def get_class(x: dict, d: str) -> Class:
            del x['dates']
            x['date'] = datetime.strptime(d, '%Y-%m-%d').date()
            return self.class_type(**x)

        def process_classes(x):
            x['class_'] = x['class']
            del x['class']
            x['interval'] = self.get_interval(x['class_'])
            x['discipline'] = re.sub(' \(.*.\)$', '', x['discipline'])
            x['type'] = self.class_types[x['type']].name
            self.disciplines_set.add(x['discipline'])
            self.class_types_set.add(x['type'])
            return (get_class(copy.copy(x), d) for d in x['dates'])

        self.classes = list(sorted(
            filter(lambda x: x.discipline != '-',
                   chain.from_iterable(
                       (process_classes(x) for x in self.raw_classes)
                   ))
        ))
        self.now = self._get_now()

    async def _fetch_class_types(self): # TODO: move somewhere else
        self.class_types = {k: ClassType(**x) for k, x in (await request('class-types', v=1)).items()}

    @singledispatchmethod
    async def _fetch(self, _, __) -> Tuple[Type[Class], dict]:
        raise NotImplementedError('Not implemented')

    @_fetch.register
    async def _(self, user: Student) -> Tuple[Type[Class], dict]:
        schedule = await request(f'faculties/{user.faculty}/years/{user.year}/groups/{user.group}/schedule', v=2)
        self.mfws = schedule['mfws']
        self.role = 'student'
        return StudentClass, schedule['classes']

    @_fetch.register
    async def _(self, user: Lecturer) -> Tuple[Type[Class], dict]:
        schedule = await request(f'lecturers/{user.name}/schedule', v=2)
        self.mfws = schedule['mfws']
        self.role = 'lecturer'
        return LecturerClass, schedule['classes']

    class_type: Callable[[...], Class]
    classes: List[Class]
    now: BaseClass
    mfws: int
    raw_classes: List[dict]
    class_types: Dict[str, ClassType]
    disciplines_set: Set[str] = set()
    class_types_set: Set[str] = set()
    role: str

    @staticmethod
    @cached(**cache_params, namespace='schedule_create', ttl=60, key_builder=lambda _, user: user.json())
    async def create(user: User) -> 'Schedule':
        self = Schedule()
        self.class_type, self.raw_classes = await self._fetch(user)
        await self._fetch_class_types()
        await self._process()
        return self
