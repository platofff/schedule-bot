from src.bot.commands._abstract import AbstractCommand
from src.bot.entities import Message
from src.db import db

triggers = {'сброс'}


class Command(AbstractCommand):

    @classmethod
    async def run(cls, msg: Message, _):
        del db[msg.sid]
        await msg.api.send_text(msg.ctx, 'Для настройки отправьте мне "Преподаватель" или "Студент"', 'role')
