import re
from datetime import datetime, time
from functools import singledispatchmethod
from math import floor
from bisect import bisect_left
from typing import Type, Union, List

from src.bot.entities import Student, Lecturer
from src.misc.dates import utc_timestamp_ms, js_weekday
from src.schedule.api import request
from src.schedule.class_ import Class


class Schedule:
    async def get_now(self) -> Class:
        res = {'week': None, 'day': None, 'class': None}
        d = utc_timestamp_ms()
        res['week'] = 1 if floor((d - self.mfws) / 604_800_000) % 2 == 0 else 2
        dt = datetime.now()
        res['day'] = js_weekday(dt)
        for i, _ci in self.ci.items():
            h, m = tuple(map(int, _ci['end'].split(':')))
            t = time(h, m)
            dt_t = datetime.combine(dt.date(), t)
            if dt <= dt_t:
                res['class'] = i
                break
        else:
            res['class'] = 9
        return self.class_type(res, self.ci)

    def get_closest(self, now: Class) -> Class:
        res = bisect_left(self.classes, now, 0)
        if res == len(self.classes):
            res = 0
        return self.classes[res]

    async def _process(self):
        for x in self.classes:
            x['discipline'] = re.sub(' \(.*.\)$', '', x['discipline'])
        self.ci = await request('class-intervals')
        self.classes = [self.class_type(x, self.ci) for x in self.classes]
        dt = datetime.now()
        self.classes = list(filter(lambda x: x.discipline != '-' and x.dates[-1] >= dt, self.classes))
        self.now = await self.get_now()

    @singledispatchmethod
    async def _fetch(self, _, __):
        raise NotImplementedError('Not implemented')

    @_fetch.register
    async def _(self, user: Student):
        schedule = await request(f'faculties/{user.faculty}/years/{user.year}/groups/{user.group}/schedule', v=2)
        self.__dict__.update(schedule)

    @_fetch.register
    async def _(self, user: Lecturer):
        schedule = await request(f'lecturers/{user.name}/schedule', v=2)
        self.__dict__.update(schedule)

    class_type: Type[Class]
    classes: List[Union[dict, Class]]
    now: Class
    mfws: int

    @classmethod
    async def create(cls, user: Union[Student, Lecturer], class_type: Type[Class]):
        self = Schedule()
        self.class_type = class_type
        await self._fetch(user)
        await self._process()
        return self
