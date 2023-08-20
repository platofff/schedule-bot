import copy
import re
from bisect import bisect_left
from datetime import datetime, time
from functools import singledispatchmethod
from itertools import chain
from math import floor
from typing import Type, Union, List, Tuple, Callable

from asyncache import cached
from cachetools import TTLCache

from src.bot.entities import Student, Lecturer, User
from src.misc.dates import utc_timestamp_ms, js_weekday
from src.schedule.api import request
from src.schedule.class_ import Class, ClassInterval, BaseClass, StudentClass, LecturerClass

class Schedule:
    def get_interval(self, i: Union[int, str]) -> ClassInterval:
        return ClassInterval(self.ci[str(i)]['start'], self.ci[str(i)]['end'])

    def get_now(self) -> BaseClass:
        res = dict()
        d = utc_timestamp_ms()
        res['week'] = 1 if floor((d - self.mfws) / 604_800_000) % 2 == 0 else 2
        dt = datetime.now()
        res['day'] = js_weekday(dt)
        if res['day'] == 0:
            res['week'] = 1 if res['week'] == 2 else 1
        for i, _ci in self.ci.items():
            h, m = tuple(map(int, _ci['end'].split(':')))
            t = time(h, m)
            dt_t = datetime.combine(dt.date(), t)
            if dt <= dt_t:
                res['class_'] = i
                res['interval'] = self.get_interval(i)
                break
        else:
            res['interval'] = None
            res['class_'] = 9
        res['date'] = datetime.now().date()
        return BaseClass(**res)

    def get_closest(self, now: BaseClass) -> Class:
        res = bisect_left(self.classes, now, 0)
        if res == len(self.classes):
            res = 0
        return self.classes[res]

    async def _process(self, class_dicts):
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
            return (get_class(copy.copy(x), d) for d in x['dates'])

        print(class_dicts)
        self.classes = list(sorted(
            filter(lambda x: x.discipline != '-',
                   chain.from_iterable(
                       (process_classes(x) for x in class_dicts)
                   ))
        ))
        self.now = self.get_now()

    @singledispatchmethod
    async def _fetch(self, _, __) -> Tuple[Type[Class], dict]:
        raise NotImplementedError('Not implemented')

    @_fetch.register
    async def _(self, user: Student) -> Tuple[Type[Class], dict]:
        schedule = await request(f'faculties/{user.faculty}/years/{user.year}/groups/{user.group}/schedule', v=2)
        self.mfws = schedule['mfws']
        return StudentClass, schedule['classes']

    @_fetch.register
    async def _(self, user: Lecturer) -> Tuple[Type[Class], dict]:
        schedule = await request(f'lecturers/{user.name}/schedule', v=2)
        self.mfws = schedule['mfws']
        return LecturerClass, schedule['classes']

    class_type: Callable[[...], Class]
    classes: List[Class]
    now: BaseClass
    mfws: int

    @classmethod
    @cached(TTLCache(4096, 60))
    async def create(cls, user: User):
        self = Schedule()
        self.class_type, class_dicts = await self._fetch(user)
        await self._process(class_dicts)
        return self
