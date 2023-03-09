from src.bot.entities import Message
from src.db import db
from src.schedule.api import request as schedule_api_rq


class StudentRegistration:
    async def fill_faculty(self, msg: Message):
        faculty = msg.text.upper()
        faculties = await schedule_api_rq('faculties')
        faculty_id = None
        for id_, data in faculties.items():
            if data['code'] == faculty:
                faculty_id = id_
                break
        if faculty_id is None:
            return await msg.api.send_text(msg.ctx, 'Факультет не найден! Выбери один из списка:\n- ' +
                                           '\n- '.join([f['code'] for f in faculties.values()]))
        tmp = db[msg.sid]
        tmp.faculty = faculty_id
        db[msg.sid] = tmp
        await msg.api.send_text(msg.ctx, 'Принято. На каком курсе ты обучаешься (1-6)?')

    async def fill_year(self, msg: Message):
        tmp = db[msg.sid]
        try:
            tmp.year = int(msg.text)
        except (ValueError, AssertionError):
            return await msg.api.send_text(msg.ctx, 'Номер курса должен быть от 1 до 6!')
        db[msg.sid] = tmp
        groups = await schedule_api_rq(
            f'faculties/{tmp.faculty}/years/{tmp.year}/groups')
        await msg.api.send_text(msg.ctx, 'Выбери свою группу из списка:\n- ' + '\n- '.join([x[0] for x in groups]))

    async def fill_group(self, msg: Message):
        tmp = db[msg.sid]
        groups = [x[0] for x in await schedule_api_rq(
            f'faculties/{tmp.faculty}/years/{tmp.year}/groups')]
        if msg.text not in groups:
            return await msg.api.send_text('Выбери свою группу из списка:\n- ' + '\n- '.join(groups))
        tmp.group = msg.text
        db[msg.sid] = tmp
        await msg.api.send_text(msg.ctx, 'Бот настроен. Теперь тебе доступны команды, указанные на кнопках клавиатуры.',
                                'set')
