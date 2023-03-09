import asyncio
from typing import Iterable, List

from src.bot import commands
from src.bot.entities import Message, Student
from src.bot_api.abstract import AbstractBotAPI
from src.bot.registration import Registration
from src.schedule.schedule import Schedule
from src.db import db


class Bot:
    _registration: Registration
    _tasks: List[asyncio.Task] = []

    async def run(self):
        await asyncio.gather(*self._tasks)

    def __init__(self, apis: Iterable[AbstractBotAPI]):
        for api in apis:
            api.add_text_handler(self._handler)
            self._tasks.append(api.task)
        self._registration = Registration()

    async def _handler(self, msg: Message) -> None:
        if msg.sid not in db:
            return await self._registration.register(msg)
        user = db[msg.sid]
        if type(user) is Student:
            if user.faculty is None:
                return await self._registration.student.fill_faculty(msg)
            if user.year is None:
                return await self._registration.student.fill_year(msg)
            if user.group is None:
                return await self._registration.student.fill_group(msg)
        else:
            if user.name is None:
                return await self._registration.lecturer.fill_name(msg)

        schedule = await Schedule.get(user, msg.api.ClassType)

        ltext = msg.text.lower()
        for cname in commands.__all__:
            command = getattr(commands, cname)
            if any(ltext.startswith(x) for x in command.triggers):
                return await command.Command.run(msg, schedule)
