from types import SimpleNamespace

from src.bot.commands._abstract import AbstractCommand
from src.misc.class_status import ClassStatus
from src.bot.entities import Message
from src.misc.weekdays import weekdays
from src.schedule.class_ import Class

triggers = {'пары сегодня'}


class Command(AbstractCommand):
    _label = 'Сегодня'

    @staticmethod
    def _get_class(now: Class) -> Class:
        return now

    @classmethod
    async def run(cls, msg: Message, s: SimpleNamespace):
        res = []
        target = cls._get_class(s.now)
        if any(c.week == target.week and c.day == target.day for c in s.classes):
            target = s.now
            current = True
        else:
            target = s.closest
            res.append(f'{cls._label} пар нет! 😼 Вот расписание на {weekdays[target.day]}:')
            current = False

        for c in sorted(filter(lambda c: c.week == target.week and
                               c.day == target.day,
                               s.classes)):
            if c.class_ > target.class_ or not current:
                res.append(f'{ClassStatus.NEXT} {c}')
            elif c.class_ == target.class_:
                res.append(f'{ClassStatus.CURRENT} {c}')
            else:
                res.append(f'{ClassStatus.PAST} {c}')
        await msg.api.send_text(msg.ctx, '\n\n'.join(res))
