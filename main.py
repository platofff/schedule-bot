import os
import shelve
import atexit
import re
import logging
from datetime import date
from pathlib import Path

import aiohttp
from vkbottle.bot import Bot, Message
from vkbottle import Keyboard, KeyboardButtonColor, Text
from cache import AsyncTTL

logging.getLogger('vkbottle').setLevel(logging.INFO)
Path('db').mkdir(exist_ok=True)
db = shelve.open(os.path.join('db', 'db'), writeback=True)
atexit.register(db.close)

bot = Bot(token=os.getenv('VK_BOT_TOKEN'))
class_intervals = None
weekdays = {1: 'понедельник',
            2: 'вторник',
            3: 'среду',
            4: 'четверг',
            5: 'пятницу',
            6: 'субботу'}


def bold_chars(s: str) -> str:
    def bc():
        for char in s:
            if char.isdigit():
                yield chr(ord(char) + 120764)
            else:
                yield char

    return ''.join(bc())


@AsyncTTL(time_to_live=60, maxsize=4096)
async def api_rq(call: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://schedule.npi-tu.ru/api/v1/{call}') as resp:
            res = await resp.json(content_type=None)
    if call.endswith('schedule'):
        for i in range(len(res['classes'])):
            res['classes'][i]['discipline'] = re.sub(' \(.*.\)$', '', res['classes'][i]['discipline'])
    return res


@bot.on.message()
async def handler(message: Message):
    sid = str(message.from_id)
    if sid not in db:
        faculty = message.text.upper()
        faculties = await api_rq('faculties')
        faculty_id = None
        for id_, data in faculties.items():
            if data['code'] == faculty:
                faculty_id = id_
                break
        if faculty_id is None:
            return await message.answer('Факультет не найден! Выбери один из списка:\n- ' +
                                        '\n- '.join([f['code'] for f in faculties.values()]))
        db[sid] = {'faculty': faculty_id, 'year': None, 'group': None}
        return await message.answer('Принято. На каком курсе ты обучаешься (1-6)?')
    if db[sid]['year'] is None:
        try:
            year = int(message.text)
            assert 1 <= year <= 6
        except (ValueError, AssertionError):
            return await message.answer('Номер курса должен быть от 1 до 6!')
        db[sid]['year'] = year
        groups = await api_rq(f'faculties/{db[sid]["faculty"]}/years/{db[sid]["year"]}/groups')
        return await message.answer('Выбери свою группу из списка:\n- ' + '\n- '.join([x[0] for x in groups]))

    keyboard = Keyboard(one_time=False, inline=False)
    keyboard.add(Text('Пара'), color=KeyboardButtonColor.POSITIVE)
    keyboard.row()
    keyboard.add(Text('Пары сегодня'), color=KeyboardButtonColor.PRIMARY)
    keyboard.add(Text('Пары завтра'), color=KeyboardButtonColor.SECONDARY)
    keyboard.add(Text('Сброс'), color=KeyboardButtonColor.NEGATIVE)

    if db[sid]['group'] is None:
        groups = [x[0] for x in await api_rq(f'faculties/{db[sid]["faculty"]}/years/{db[sid]["year"]}/groups')]
        if message.text not in groups:
            return await message.answer('Выбери свою группу из списка:\n- ' + '\n- '.join(groups))
        db[sid]['group'] = message.text
        return await message.answer('Бот настроен. Тепорь тебе доступны команды...TODO', keyboard=keyboard.get_json())

    schedule = await api_rq(
        f'faculties/{db[sid]["faculty"]}/years/{db[sid]["year"]}/groups/{db[sid]["group"]}/schedule')

    schedule['now']['day'] = 1

    if message.text == 'Пара':
        now = ''
        next_ = ''
        if 'class' not in schedule['now']:
            return await message.answer('Пары закончились. Пора отдыхать 😼')
        for class_ in sorted(schedule['classes'], key=lambda x: x['class']):
            if class_['week'] == schedule['now']['week'] and class_['day'] == schedule['now']['day']:
                interval = class_intervals[str(class_["class"])]
                if class_['class'] == schedule['now']['class']:
                    now = f'🟢 {interval["start"]}–{interval["end"]} {bold_chars(class_["auditorium"])}\n' \
                          f'{class_["discipline"]}\n{class_["lecturer"]}'
                elif class_['class'] > schedule['now']['class']:
                    next_ = f'\n\n🔵 {interval["start"]}–{interval["end"]} {bold_chars(class_["auditorium"])}\n' \
                            f'{class_["discipline"]}\n{class_["lecturer"]}'
                    break
        if now == '' and next_ == '':
            return await message.answer('Пары закончились. Пора отдыхать 😼')
        return await message.answer(now + next_)

    async def get_classes(day, all_next=False):
        dayn = []
        for class_ in schedule['classes']:
            if class_['week'] == schedule['now']['week'] and class_['day'] == day:
                interval = class_intervals[str(class_["class"])]
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
                             f'{state} {interval["start"]}–{interval["end"]} {bold_chars(class_["auditorium"])}\n'
                             f'{class_["discipline"]}\n{class_["lecturer"]}'))
        return await message.answer('\n\n'.join([x[1] for x in sorted(dayn, key=lambda x: x[0])]))

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

    print(today, isoweekday)

    if message.text == 'Пары сегодня':
        if not_today:
            await message.answer(f'Сегодня пар нет! 😼 Вот расписание на {weekdays[today]}:')
        return await get_classes(today)

    if message.text == 'Пары завтра':
        if tomorrow != isoweekday + 1:
            await message.answer(f'Завтра пар нет! 😼 Вот расписание на {weekdays[tomorrow]}:')
        return await get_classes(tomorrow, True)

    if message.text == 'Сброс':
        del db[sid]
        return await message.answer('Настройки сброшены. Для настройки отправь мне название факультета',
                                    keyboard='{"buttons":[],"one_time":true}')


async def main():
    global class_intervals
    class_intervals = await api_rq('class-intervals')


bot.loop_wrapper.add_task(main())
bot.run_forever()
