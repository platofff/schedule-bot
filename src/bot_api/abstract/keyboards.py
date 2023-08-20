from src.bot_api.abstract.keyboard import *

from dataclasses import dataclass, field


@dataclass
class Keyboards:
    DEFAULT: Keyboard = Keyboard([
        Row([Button('Пара', 'POSITIVE'), Button('Пары сегодня', 'PRIMARY')]),
        Row([Button('Пары завтра', 'SECONDARY'), Button('Сброс', 'NEGATIVE')])
    ])

    START: Keyboard = Keyboard([
        Row([Button('Преподаватель', 'PRIMARY'), Button('Студент', 'POSITIVE')])
    ])

    RESET: Keyboard = Keyboard([
        Row([Button('Сброс', 'NEGATIVE')])
    ])
