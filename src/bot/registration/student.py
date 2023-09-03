from pydantic import ValidationError

from src.bot.entities import Message, Student
from src.bot.registration.abstract import AbstractRegistration
from src.bot_api.abstract import Keyboards
from src.schedule.api import request as schedule_api_rq


class StudentRegistration(AbstractRegistration):
    USER_TYPE = Student

    @staticmethod
    async def start(msg: Message):
        await msg.api.send_text(msg.ctx, 'Отлично. Теперь отправьте мне название своего факультета',
                                Keyboards.RESET)

    @staticmethod
    async def set_faculty(msg: Message, user: Student):
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
        user.faculty = faculty_id
        await user.save()
        await msg.api.send_text(msg.ctx, f'Принято. На каком курсе вы обучаетесь?', Keyboards.RESET)

    @staticmethod
    async def set_year(msg: Message, user: Student):
        try:
            user.year = int(msg.text)
        except (ValueError, ValidationError):
            fi = Student.__fields__['year'].field_info # not working, TODO
            return await msg.api.send_text(msg.ctx, f'Номер курса должен быть от {fi.ge} до {fi.le}!')
        await user.save()
        await msg.api.send_text(msg.ctx, 'OK. Теперь напишите название своей группы (например "РПИа")',
                                Keyboards.RESET)

    @staticmethod
    async def set_group(msg: Message, user: Student):
        groups = [x[0] for x in await schedule_api_rq(
            f'faculties/{user.faculty}/years/{user.year}/groups')]
        if msg.text not in groups:
            return await msg.api.send_text(msg.ctx, 'Выберите свою группу из списка:\n- ' + '\n- '.join(groups))
        user.group = msg.text
        await user.save()
        await msg.api.send_text(msg.ctx,
                            'Бот настроен. Теперь вам доступны команды, указанные на кнопках клавиатуры.',
                                Keyboards.DEFAULT)

    FIELD_SETTERS = {
        'faculty': set_faculty,
        'year': set_year,
        'group': set_group
    }
