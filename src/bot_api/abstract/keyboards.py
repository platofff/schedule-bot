from src.bot_api.abstract.keyboard import *

keyboards = {
    'set': Keyboard([
        Row([Button('Пара', 'POSITIVE'), Button('Пары сегодня', 'PRIMARY')]),
        Row([Button('Пары завтра', 'SECONDARY'), Button('Сброс', 'NEGATIVE')])
    ]),

    'role': Keyboard([
        Row([Button('Преподаватель', 'PRIMARY'), Button('Студент', 'POSITIVE')])
    ]),

    'reset_btn': Keyboard([
        Row([Button('Сброс', 'NEGATIVE')])
    ])
}
