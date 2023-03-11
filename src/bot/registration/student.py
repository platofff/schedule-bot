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
            return await msg.api.send_text(msg.ctx, 'Факультет не найден! Выберите один из списка:\n- ' +
                                           '\n- '.join([f['code'] for f in faculties.values()]))
        tmp = db[msg.sid]
        tmp.faculty = faculty_id
        db[msg.sid] = tmp
        await msg.api.send_text(msg.ctx, 'Принято. На каком курсе вы обучаетесь (1-6)?', 'reset_btn')

    async def fill_year(self, msg: Message):
        tmp = db[msg.sid]
        try:
            tmp.year = int(msg.text)
        except (ValueError, AssertionError):
            return await msg.api.send_text(msg.ctx, 'Номер курса должен быть от 1 до 6!')
        db[msg.sid] = tmp
        await msg.api.send_text(msg.ctx, 'OK. Теперь напишите название своей группы (например "РПИа")', 'reset_btn')

    async def fill_group(self, msg: Message):
        tmp = db[msg.sid]
        groups = [x[0] for x in await schedule_api_rq(
            f'faculties/{tmp.faculty}/years/{tmp.year}/groups')]
        if msg.text not in groups:
            return await msg.api.send_text(msg.ctx, 'Выберите свою группу из списка:\n- ' + '\n- '.join(groups))
        tmp.group = msg.text
        db[msg.sid] = tmp
        await msg.api.send_text(msg.ctx, 'Бот настроен. Теперь вам доступны команды, указанные на кнопках клавиатуры.',
                                'set')
