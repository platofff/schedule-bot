from typing import Type, Dict, Optional

from src.bot.entities import Message, User
from .abstract import AbstractRegistration
from .lecturer import LecturerRegistration
from .student import StudentRegistration
from ...bot_api.abstract import CommonMessages, Keyboards


class CommonRegistration:
    _USER_TYPES: Dict[str, Type[AbstractRegistration]] = {
        'Студент': StudentRegistration,
        'Преподаватель': LecturerRegistration
    }
    _REGISTRATIONS_MAP: Dict[Type[User], Type[AbstractRegistration]] =\
        dict(map(lambda x: (x.USER_TYPE, x), _USER_TYPES.values()))

    @staticmethod
    async def _start(msg: Message):
        try:
            Registration = CommonRegistration._USER_TYPES[msg.text]
        except KeyError:
            return await msg.api.send_text(msg.ctx, f'Выберите один из вариантов: '
                                             f'{", ".join(CommonRegistration._USER_TYPES.keys())}', Keyboards.START)
        user = Registration.USER_TYPE(id=msg.from_id)
        await user.create()
        await Registration.start(msg)


    @staticmethod
    async def get_or_register_user(msg: Message) -> Optional[User]:
        user = await User.get(msg.from_id, with_children=True)
        if user is None:
            await CommonRegistration._start(msg)
            return None

        if msg.text == 'Сброс':
            await user.delete()
            await msg.api.send_text(msg.ctx, CommonMessages.START, Keyboards.START)
            return None

        Registration = CommonRegistration._REGISTRATIONS_MAP[type(user)]
        for field, setter in Registration.FIELD_SETTERS.items():
            if getattr(user, field) is None:
                await setter(msg, user)
                return None
        return user
