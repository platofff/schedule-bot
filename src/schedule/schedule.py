import re
from datetime import datetime, time
from functools import singledispatch
from math import floor
from bisect import bisect_left
from types import SimpleNamespace
from typing import Type

from src.bot.entities import Student, Lecturer
from src.misc.dates import utc_timestamp_ms, js_weekday
from src.schedule.api import request
from src.schedule.class_ import Class


@singledispatch
async def get_user(_, __) -> dict:
    raise NotImplementedError('Not implemented')


@get_user.register
async def _(user: Student, class_type: Type[Class]) -> SimpleNamespace:
    schedule = await request(f'faculties/{user.faculty}/years/{user.year}/groups/{user.group}/schedule', v=2)
    return await Schedule.process(SimpleNamespace(**schedule), class_type)


@get_user.register
async def _(user: Lecturer, class_type: Type[Class]) -> SimpleNamespace:
    schedule = await request(f'lecturers/{user.name}/schedule', v=2)
    return await Schedule.process(SimpleNamespace(**schedule), class_type)


class Schedule:
    @staticmethod
    async def _get_now(schedule: SimpleNamespace, ci: dict, class_type: Type[Class]) -> Class:
        res = {'week': None, 'day': None, 'class': None}
        d = utc_timestamp_ms()
        res['week'] = 1 if floor((d - schedule.mfws) / 604_800_000) % 2 == 0 else 2
        dt = datetime.now()
        res['day'] = js_weekday(dt)
        for i, _ci in ci.items():
            h, m = tuple(map(int, _ci['end'].split(':')))
            t = time(h, m)
            dt_t = datetime.combine(dt.date(), t)
            if dt <= dt_t:
                res['class'] = i
                break
        else:
            res['class'] = 9
        return class_type(res, ci)

    @staticmethod
    def _get_closest(schedule: SimpleNamespace, now: Class) -> Class:
        res = bisect_left(schedule.classes, now, 0)
        if res == len(schedule.classes):
            res = 0
        return schedule.classes[res]

    @staticmethod
    async def process(schedule: SimpleNamespace, class_type: Type[Class]) -> SimpleNamespace:
        for x in schedule.classes:
            x['discipline'] = re.sub(' \(.*.\)$', '', x['discipline'])
        ci = await request('class-intervals')
        schedule.classes = [class_type(x, ci) for x in schedule.classes]
        dt = datetime.now()
        schedule.classes = list(filter(lambda x: x.discipline != '-' and x.dates[-1] >= dt, schedule.classes))
        now = await Schedule._get_now(schedule, ci, class_type)
        closest = Schedule._get_closest(schedule, now)
        schedule.__dict__.update({
            'now': now,
            'closest': closest
        })
        return schedule

    @staticmethod
    async def get(user, class_type: Type[Class]) -> dict:
        return await get_user(user, class_type)
