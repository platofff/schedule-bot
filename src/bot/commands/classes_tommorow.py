from src.bot.commands.classes_today import Command as BaseCommand
from src.schedule.class_ import Class

triggers = {'пары завтра'}


class Command(BaseCommand):
    _label = 'Завтра'

    @staticmethod
    def _get_class(now: Class) -> Class:
        if now.day == 6:
            now.day = 0
        else:
            now.day += 1
        now.class_ = 0
        return now
