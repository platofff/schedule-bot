import asyncio
from typing import Iterable, List

from src.bot import commands
from src.bot.entities import Message
from src.bot.registration import CommonRegistration
from src.bot_api.abstract import AbstractBotAPI, CommonMessages, Keyboards
from src.db import db
from src.schedule.schedule import Schedule


class Bot:
    _tasks: List[asyncio.Task] = []

    async def run(self):
        await asyncio.gather(*self._tasks)

    def __init__(self, apis: Iterable[AbstractBotAPI]):
        for api in apis:
            api.add_text_handler(self._handler)
            self._tasks.append(api.task)

    @classmethod
    async def _handler(cls, msg: Message) -> None:
        user = await CommonRegistration.get_or_register_user(msg)
        if user is None:
            return

        schedule = await Schedule.create(user)

        if 'classes' not in dir(schedule) or not schedule.classes:
            del db[msg.sid]
            await msg.api.send_text(msg.ctx, 'Произошла ошибка: расписание для вас не найдено!')
            return await msg.api.send_text(msg.ctx, CommonMessages.START, Keyboards.START)

        ltext = msg.text.lower()
        for cname in commands.__all__:
            command = getattr(commands, cname)
            if command.triggers is not None and any(ltext.startswith(x) for x in command.triggers):
                return await command.Command.run(msg, schedule)

        return await commands.gpt.Command.run(msg, schedule)