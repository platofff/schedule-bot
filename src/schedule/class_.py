from abc import abstractmethod
from datetime import datetime


class Class:
    lecturer = ''
    _interval: dict
    _ci: dict
    _class: int

    @property
    def interval(self):
        return self._interval

    @property
    def class_(self):
        return self._class

    @class_.setter
    def class_(self, v):
        self._class = int(v)
        try:
            self._interval = self._ci[str(self._class)]
        except KeyError:
            pass

    def __init__(self, c: dict, ci: dict):
        self.week = c['week']
        self.day = c['day']
        self._ci = ci
        self.class_ = int(c['class'])
        try:
            self.lecturer = c['lecturer']
        except KeyError:
            pass
        try:
            self.discipline = c['discipline']
            self.type = c['type']
            self.auditorium = c['auditorium']
            self.dates = [datetime.strptime(x, '%Y-%m-%d') for x in c['dates']]
        except KeyError:
            pass

    def __lt__(self, other):
        return int(f'{self.week}{self.day}{self.class_}') < int(f'{other.week}{other.day}{other.class_}')

    @abstractmethod
    def _bold_text(self, t: str) -> str:
        pass

    def __str__(self):
        r = f'{self.interval["start"]}–{self.interval["end"]} {self._bold_text(self.auditorium)}\n' \
            f'{self.discipline}'
        if self.lecturer != '':
            r += f'\n{self.lecturer}'
        return r

