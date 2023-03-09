from .lecturer import LecturerRegistration
from .student import StudentRegistration
from src.bot.entities import Message, Student, Lecturer
from src.db import db


class Registration:
    lecturer: LecturerRegistration
    student: StudentRegistration

    def __init__(self):
        self.lecturer = LecturerRegistration()
        self.student = StudentRegistration()

    async def register(self, msg: Message):
        if msg.text == 'Студент':
            db[msg.sid] = Student()
            await msg.api.send_text(msg.ctx, 'Отлично. Теперь отправь мне название своего факультета', 'clear')
        elif msg.text == 'Преподаватель':
            db[msg.sid] = Lecturer()
            await msg.api.send_text(msg.ctx,
                                    'Отлично. Теперь напишите мне свою фамилию и инициалы в формате "Иванов И И".',
                                    'clear')
        else:
            await msg.api.send_text(msg.ctx, 'Введите "Преподаватель" или "Студент"!', 'role')
