from src.bot_api.abstract.keyboard import *

from dataclasses import dataclass

@dataclass
class Keyboards:
    DEFAULT = Keyboard([
        Row([Button('Пара', 'POSITIVE'), Button('Пары сегодня', 'PRIMARY')]),
        Row([Button('Пары завтра', 'SECONDARY'), Button('Сброс', 'NEGATIVE')])
    ])

    START = Keyboard([
        Row([Button('Преподаватель', 'PRIMARY'), Button('Студент', 'POSITIVE')])
    ])

    RESET = Keyboard([
        Row([Button('Сброс', 'NEGATIVE')])
    ])
