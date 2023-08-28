from src.bot.entities import Message, Lecturer
from src.bot.registration.abstract import AbstractRegistration
from src.bot_api.abstract import Keyboards
from src.schedule.api import request as schedule_api_rq


class LecturerRegistration(AbstractRegistration):
    USER_TYPE = Lecturer

    @staticmethod
    async def start(msg: Message):
        await msg.api.send_text(msg.ctx,
                                'Отлично. Теперь напишите мне свою фамилию и инициалы в формате "Иванов И И".',
                                Keyboards.RESET)
    @staticmethod
    async def set_name(msg: Message, user: Lecturer):
        res = await schedule_api_rq(f'lecturers/{msg.text}')
        if len(res) > 0:
            await user.set({Lecturer.name: msg.text})
            await msg.api.send_text(msg.ctx,
                                    'Бот настроен. Теперь вам доступны команды, указанные на кнопках клавиатуры.',
                                    Keyboards.DEFAULT)
        else:
            await msg.api.send_text(msg.ctx, 'Преподаватель не найден!', Keyboards.RESET)

    FIELD_SETTERS = {
        'name': set_name
    }
