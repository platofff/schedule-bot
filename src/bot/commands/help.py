from typing import Union
from urllib.parse import urlencode

from src.bot.commands._abstract import AbstractCommand
from src.bot.entities import Message, Lecturer, Student
from src.db import db

triggers = {'start', 'help', 'помощь'}


class Command(AbstractCommand):
    @staticmethod
    def _get_url(user: Union[Lecturer, Student]):
        if type(user) is Lecturer:
            params = {'for': 'lecturer', 'lecturer': user.name}
        else:
            params = {'for': 'student', 'faculty': user.faculty, 'year': user.year, 'group': user.group}

        return f'https://schedule.npi-tu.ru/schedule.html?{urlencode(params)}'

    @classmethod
    async def run(cls, msg: Message, _):
        user = db[msg.sid]
        await msg.api.send_text(msg.ctx, f'Полное расписание: {cls._get_url(user)}\n'
                                         'Список команд:'
                                         '\n\n'
                                         '- пара\n'
                                         '- пары сегодня\n'
                                         '- пары завтра\n'
                                         '- сброс')
