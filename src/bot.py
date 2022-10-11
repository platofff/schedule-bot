import asyncio
import re
from pathlib import Path
import os
import shelve
from datetime import date
from typing import Iterable, Any

from cache import AsyncTTL
from vkbottle.http import aiohttp

from src.abstract import AbstractBotAPI
from src.misc import async_partial


class Bot:
    _weekdays = {1: 'понедельник',
                 2: 'вторник',
                 3: 'среду',
                 4: 'четверг',
                 5: 'пятницу',
                 6: 'субботу'}

    def __init__(self, apis: Iterable[AbstractBotAPI]):
        Path('db').mkdir(exist_ok=True)
        self._db = shelve.open(os.path.join('db', 'db'), writeback=True)
        asyncio.get_event_loop().create_task(self._get_class_intervals())
        for api in apis:
            api.add_text_handler(async_partial(self._handler, api))

    def __del__(self):
        self._db.close()

    async def _get_class_intervals(self):
        self._class_intervals = await self._schedule_api_rq('class-intervals')

    @AsyncTTL(time_to_live=60, maxsize=4096)
    async def _schedule_api_rq(self, call: str) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://schedule.npi-tu.ru/api/v1/{call}') as resp:
                res = await resp.json(content_type=None)
        if call.endswith('schedule'):
            for i in range(len(res['classes'])):
                res['classes'][i]['discipline'] = re.sub(' \(.*.\)$', '', res['classes'][i]['discipline'])
        return res

    async def _handler(self, api: AbstractBotAPI, ctx: Any, text: str):
        if text == '/start':
            return await api.send_text(ctx, 'Вас приветствует чат-бот расписания ЮРГПУ (НПИ). '
                                            'Чтобы начать, выберите, для кого вы хотите получать расписание', 'role')
        sid = api.user_id(ctx)
        if sid not in self._db:
            if text == 'Студент':
                self._db[sid] = {'role': 1, 'faculty': None, 'year': None, 'group': None}
                return await api.send_text(ctx, 'Отлично. Теперь отправь мне название своего факультета', 'clear')
            elif text == 'Преподаватель':
                self._db[sid] = {'role': 0, 'name': None}
                return await api.send_text(ctx, 'Отлично. Теперь напишите мне свою фамилию и инициалы в формате "Иванов И И".', 'clear')
            else:
                return await api.send_text(ctx, 'Введите "Преподаватель" или "Студент"!', 'role')
        if self._db[sid]['role'] == 1:
            if self._db[sid]['faculty'] is None:
                faculty = text.upper()
                faculties = await self._schedule_api_rq('faculties')
                faculty_id = None
                for id_, data in faculties.items():
                    if data['code'] == faculty:
                        faculty_id = id_
                        break
                if faculty_id is None:
                    return await api.send_text(ctx, 'Факультет не найден! Выбери один из списка:\n- ' +
                                               '\n- '.join([f['code'] for f in faculties.values()]))
                self._db[sid]['faculty'] = faculty_id
                return await api.send_text(ctx, 'Принято. На каком курсе ты обучаешься (1-6)?')
            if self._db[sid]['year'] is None:
                try:
                    year = int(text)
                    assert 1 <= year <= 6
                except (ValueError, AssertionError):
                    return await api.send_text(ctx, 'Номер курса должен быть от 1 до 6!')
                self._db[sid]['year'] = year
                groups = await self._schedule_api_rq(
                    f'faculties/{self._db[sid]["faculty"]}/years/{self._db[sid]["year"]}/groups')
                return await api.send_text(ctx, 'Выбери свою группу из списка:\n- ' + '\n- '.join([x[0] for x in groups]))

            if self._db[sid]['group'] is None:
                groups = [x[0] for x in await self._schedule_api_rq(f'faculties/{self._db[sid]["faculty"]}/years/{self._db[sid]["year"]}/groups')]
                if text not in groups:
                    return await api.send_text('Выбери свою группу из списка:\n- ' + '\n- '.join(groups))
                self._db[sid]['group'] = text
                return await api.send_text(ctx, 'Бот настроен. Теперь тебе доступны команды, указанные на кнопках клавиатуры.', 'set')
            schedule = await self._schedule_api_rq(
                f'faculties/{self._db[sid]["faculty"]}/years/{self._db[sid]["year"]}/groups/{self._db[sid]["group"]}/schedule')
        else:
            if self._db[sid]['name'] is None:
                res = await self._schedule_api_rq(f'lecturers/{text}')
                if len(res) == 1:
                    self._db[sid]['name'] = res[0]
                    return await api.send_text(ctx, 'Бот настроен. Теперь вам доступны команды, указанные на кнопках клавиатуры.', 'set')
                else:
                    return await api.send_text(ctx, 'Преподаватель не найден!')
            schedule = await self._schedule_api_rq(f'lecturers/{self._db[sid]["name"]}/schedule')

        for class_ in schedule['classes']:
            if 'lecturer' not in class_.keys():
                class_.update({'lecturer': ''})
            else:
                class_["lecturer"] = '\n' + class_["lecturer"].strip()

        if text == 'Пара':
            now = ''
            next_ = ''
            if 'class' not in schedule['now']:
                return await api.send_text(ctx, 'Пары закончились. Пора отдыхать 😼')
            for class_ in sorted(schedule['classes'], key=lambda x: x['class']):
                if class_['week'] == schedule['now']['week'] and class_['day'] == schedule['now']['day']:
                    interval = self._class_intervals[str(class_["class"])]
                    if class_['class'] == schedule['now']['class']:
                        now = f'🟢 {interval["start"]}–{interval["end"]} {api.bold_text(class_["auditorium"])}\n' \
                              f'{class_["discipline"]}{class_["lecturer"]}'
                    elif class_['class'] > schedule['now']['class']:
                        next_ = f'\n\n🔵 {interval["start"]}–{interval["end"]} {api.bold_text(class_["auditorium"])}\n' \
                                f'{class_["discipline"]}{class_["lecturer"]}'
                        break
            if now == '' and next_ == '':
                return await api.send_text(ctx, 'Пары закончились. Пора отдыхать 😼')
            return await api.send_text(ctx, now + next_)

        async def get_classes(day, all_next=False) -> str:
            dayn = []
            for class_ in schedule['classes']:
                if class_['week'] == schedule['now']['week'] and class_['day'] == day:
                    interval = self._class_intervals[str(class_["class"])]
                    if all_next:
                        state = '🔵'
                    elif 'class' not in schedule['now']:
                        state = '⚪'
                    elif class_['class'] < schedule['now']['class']:
                        state = '⚪'
                    elif class_['class'] == schedule['now']['class']:
                        state = '🟢'
                    else:
                        state = '🔵'
                    dayn.append((class_['class'],
                                 f'{state} {interval["start"]}–{interval["end"]} {api.bold_text(class_["auditorium"])}\n'
                                 f'{class_["discipline"]}{class_["lecturer"]}'))
            return '\n\n'.join([x[1] for x in sorted(dayn, key=lambda x: x[0])])

        active_days = list(sorted(set([c['day'] for c in schedule['classes']])))
        today = None
        tomorrow = None
        not_today = False
        isoweekday = date.today().isoweekday()
        for day in active_days:
            if day >= schedule['now']['day']:
                if today is None:
                    today = day
                    continue
                tomorrow = day
                break
        if tomorrow is None:
            tomorrow = active_days[0]

        if today != isoweekday:
            not_today = True
            tomorrow = today

        if text == 'Пары сегодня':
            if not_today:
                await api.send_text(ctx, f'Сегодня пар нет! 😼 Вот расписание на {self._weekdays[today]}:')
            res = await get_classes(today)
            if res != '':
                return await api.send_text(ctx, res)
            return await api.send_text('Сегодня пар нет!')

        if text == 'Пары завтра':
            while True:
                res = await get_classes(tomorrow, True)
                if res == '':
                    try:
                        tomorrow = active_days[active_days.index(tomorrow) + 1]
                    except IndexError:
                        tomorrow = active_days[0]
                        break
                else:
                    break
            if tomorrow != isoweekday + 1:
                await api.send_text(ctx, f'Завтра пар нет! 😼 Вот расписание на {self._weekdays[tomorrow]}:')
            return await api.send_text(ctx, res)

        if text == 'Сброс':
            del self._db[sid]
            await api.send_text(ctx, 'Настройки сброшены. Для настройки отправь мне "Преподаватель" или "Студент"', 'role')
