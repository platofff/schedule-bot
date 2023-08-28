from src.bot.commands._abstract import AbstractCommand
from src.bot.entities import Message, User
from src.bot_api.abstract import Keyboards

triggers = {'сброс'}


class Command(AbstractCommand):

    @classmethod
    async def run(cls, msg: Message, user: User):
        await user.delete()
        await msg.api.send_text(msg.ctx, 'Для настройки отправьте мне "Преподаватель" или "Студент"',
                                Keyboards.START)
