import asyncio
from typing import Iterable, List

from src.bot import commands
from src.bot.entities import Message
from src.bot.registration import CommonRegistration
from src.bot_api.abstract import AbstractBotAPI, CommonMessages, Keyboards
from src.gpt.keys import OpenAIKeysManager
from src.schedule.schedule import Schedule

class Bot:
    _tasks: List[asyncio.Task] = []
    _km: OpenAIKeysManager

    async def run(self):
        await asyncio.gather(*self._tasks)

    def __init__(self, apis: Iterable[AbstractBotAPI]):
        for api in apis:
            api.add_text_handler(self._handler)
            self._tasks.append(api.task)

    @staticmethod
    async def _handler(msg: Message):
        user = await CommonRegistration.get_or_register_user(msg)
        if user is None:
            return

        user.schedule, user.username = await asyncio.gather(Schedule.create(user), msg.api.get_username(msg.ctx))

        if 'classes' not in dir(user.schedule) or not user.schedule.classes:
            await user.delete()
            await msg.api.send_text(msg.ctx, 'Произошла ошибка: расписание для вас не найдено!')
            return await msg.api.send_text(msg.ctx, CommonMessages.START, Keyboards.START)

        ltext = msg.text.lower()
        for cname in commands.__all__:
            command = getattr(commands, cname)
            if command.triggers is not None and any(ltext.startswith(x) for x in command.triggers):
                return await command.Command.run(msg, user)

        await msg.api.set_typing_state(msg.ctx, True)
        result = await commands.gpt.Command.run(msg, user)
        await msg.api.set_typing_state(msg.ctx, False)
        return result