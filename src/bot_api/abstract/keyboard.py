from dataclasses import dataclass
from typing import List


@dataclass
class Button:
    text: str
    color: str


class Row(List[Button]):
    pass


class Keyboard(List[Row]):
    pass
