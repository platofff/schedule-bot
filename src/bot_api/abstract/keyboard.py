from dataclasses import dataclass
from typing import Tuple

@dataclass(frozen=True)
class Button:
    text: str
    color: str


class Row(Tuple[Button, ...]):
    pass

class Keyboard(Tuple[Row, ...]):
    pass
