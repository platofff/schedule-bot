from src.bot.entities import Message
from src.db import db
from src.schedule.api import request as schedule_api_rq


class LecturerRegistration:
    async def fill_name(self, msg: Message):
        res = await schedule_api_rq(f'lecturers/{msg.text}')
        if len(res) == 1:
            tmp = db[msg.sid]
            tmp.name = res[0]
            db[msg.sid] = tmp
            await msg.api.send_text(msg.ctx,
                                    'Бот настроен. Теперь вам доступны команды, указанные на кнопках клавиатуры.',
                                    'set')
        else:
            await msg.api.send_text(msg.ctx, 'Преподаватель не найден!')
