from typing import Type, Dict, Union

from src.bot.entities import Message, User
from src.db import db
from .abstract import AbstractRegistration
from .lecturer import LecturerRegistration
from .student import StudentRegistration
from ...bot_api.abstract import CommonMessages


class CommonRegistration:
    _USER_TYPES: Dict[str, Type[AbstractRegistration]] = {
        'Студент': StudentRegistration,
        'Преподаватель': LecturerRegistration
    }
    _REGISTRATIONS_MAP: Dict[Type[User], Type[AbstractRegistration]] = dict(map(lambda x: (x.USER_TYPE, x), _USER_TYPES.values()))

    @staticmethod
    async def _start(msg: Message):
        try:
            Registration = CommonRegistration._USER_TYPES[msg.text]
            db[msg.sid] = Registration.USER_TYPE()
            await Registration.start(msg)
        except KeyError:
            await msg.api.send_text(msg.ctx,f'Выберите один из вариантов: '
                                            f'{", ".join(CommonRegistration._USER_TYPES.keys())}', 'role')

    @staticmethod
    async def get_or_register_user(msg: Message) -> Union[User, None]:
        if msg.sid not in db:
            await CommonRegistration._start(msg)
            return None
        user = db[msg.sid]

        if msg.text == 'Сброс':
            del db[msg.sid]
            await msg.api.send_text(msg.ctx, CommonMessages.START, 'role')
            return None

        Registration = CommonRegistration._REGISTRATIONS_MAP[type(user)]
        for field, setter in Registration.FIELD_SETTERS.items():
            if getattr(user, field) is None:
                await setter(msg)
                return None
        return user
