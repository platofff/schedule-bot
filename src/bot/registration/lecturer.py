from src.bot.entities import Message, Lecturer
from src.bot.registration.abstract import AbstractRegistration
from src.bot_api.abstract import Keyboards
from src.db import db
from src.schedule.api import request as schedule_api_rq


class LecturerRegistration(AbstractRegistration):
    USER_TYPE = Lecturer

    @staticmethod
    async def start(msg: Message):
        await msg.api.send_text(msg.ctx,
                                'Отлично. Теперь напишите мне свою фамилию и инициалы в формате "Иванов И И".',
                                Keyboards.RESET)
    @staticmethod
    async def fill_name(msg: Message):
        res = await schedule_api_rq(f'lecturers/{msg.text}')
        if len(res) == 1:
            tmp = db[msg.sid]
            tmp.name = res[0]
            db[msg.sid] = tmp
            await msg.api.send_text(msg.ctx,
                                    'Бот настроен. Теперь вам доступны команды, указанные на кнопках клавиатуры.',
                                    Keyboards.DEFAULT)
        else:
            await msg.api.send_text(msg.ctx, 'Преподаватель не найден!', Keyboards.RESET)

    FIELD_SETTERS = {
        'name': fill_name
    }
