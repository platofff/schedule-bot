from src.bot.commands._abstract import AbstractCommand
from src.bot.entities import Message
from src.misc.class_status import ClassStatus
from src.schedule.schedule import Schedule

triggers = {'пара'}


class Command(AbstractCommand):
    @classmethod
    async def run(cls, msg: Message, s: Schedule):
        s.closest = s.get_closest(s.now)
        if s.now.date != s.closest.date:
            return await msg.api.send_text(msg.ctx, 'Пары закончились. Пора отдыхать 😼')
        res = []

        for c in filter(lambda c: c.date == s.now.date, s.classes):
            if c.class_ == s.closest.class_:
                res.append(f'{ClassStatus.CURRENT} {c}')
            elif c.class_ > s.closest.class_:
                res.append(f'{ClassStatus.NEXT} {c}')
        if not res:
            res = 'Пары закончились. Пора отдыхать 😼'
        await msg.api.send_text(msg.ctx, '\n\n'.join(res))
