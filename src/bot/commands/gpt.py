import datetime
from dataclasses import field, dataclass
from time import strptime
from typing import List, Union, Dict

from src.bot.commands._abstract import AbstractCommand
from src.bot.entities import Message
from src.db import db
from src.gpt import get_gpt_response, GPTMessage, GPTFunction
from src.schedule.class_ import Class
from src.schedule.schedule import Schedule

triggers = None

@dataclass
class City:
    name: str = field(metadata={'description': 'City name'})
    station: int = field(metadata={'description': 'Station ID'})

@dataclass
class ScheduleFunction(GPTFunction):
    name: str = field(default='get_schedule')
    classes: List[Class] = field(default=None)

    async def __call__(self, date: str, offset: int) -> Dict[str, Union[List[Class], datetime.date, str]]:
        """Get user's schedule for a date

        Args:
            date: YYYY-MM-DD
            offset: offset in days
        """

        delta = datetime.timedelta(days=offset)
        sdate = strptime(date, '%Y-%m-%d')
        date_ = datetime.datetime(sdate.tm_year, sdate.tm_mon, sdate.tm_mday)
        date_ += delta
        date = datetime.date(date_.year, date_.month, date_.day)

        classes = []
        for class_ in self.classes:
            if class_.date == date:
                classes.append(class_)

        return {'classes': list(sorted(classes)), 'date': date, 'weekday': date.weekday()}

class Command(AbstractCommand):
    @classmethod
    async def run(cls, msg: Message, schedule: Schedule):
        user = db[msg.sid]
        text = await get_gpt_response([
            GPTMessage(role=GPTMessage.Role.SYSTEM, content='''You are an AI assistant in a university schedule '
            'application. Now is 2024-02-26 08:45 MSK, Monday'''),
            GPTMessage(role=GPTMessage.Role.USER, content=msg.text)
        ], [
            ScheduleFunction(classes=schedule.classes)
        ])

        await msg.api.send_text(msg.ctx, text)
