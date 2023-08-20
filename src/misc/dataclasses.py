from typing import Callable

from src.misc.typing import get_args_types


def initialize_dataclasses(d: dict, f: Callable) -> dict:
    annotations = get_args_types(f)
    for arg_name, arg_type in annotations.items():
        if arg_type is str or arg_type is int:
            continue
        d[arg_name] = arg_type(**initialize_dataclasses(d[arg_name], arg_type.__init__))

    return d