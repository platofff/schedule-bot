from src.bot.commands._abstract import AbstractCommand
from src.bot.entities import Message
from src.misc.class_status import ClassStatus
from src.misc.weekdays import WEEKDAYS_DATIVE
from src.schedule.class_ import BaseClass
from src.schedule.schedule import Schedule

triggers = {'пары сегодня'}


class Command(AbstractCommand):
    _label = 'Сегодня'

    @staticmethod
    def _get_class(now: BaseClass) -> BaseClass:
        return now

    @classmethod
    async def run(cls, msg: Message, s: Schedule):
        res = []
        target = cls._get_class(s.now)
        s.closest = s.get_closest(target)
        if any(c.date == target.date for c in s.classes):
            target = s.now
            current = True
        else:
            target = s.closest
            res.append(f'{cls._label} пар нет! 😼 Вот расписание на {WEEKDAYS_DATIVE[target.day]}:')
            current = False

        for c in filter(lambda c: c.date == target.date, s.classes):
            if c.class_ > target.class_ or not current:
                res.append(f'{ClassStatus.NEXT} {c}')
            elif c.class_ == target.class_:
                res.append(f'{ClassStatus.CURRENT} {c}')
            else:
                res.append(f'{ClassStatus.PAST} {c}')
        await msg.api.send_text(msg.ctx, '\n\n'.join(res))
