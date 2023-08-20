from typing import get_type_hints, Callable


def get_args_types(f: Callable):
    args_types = get_type_hints(f)
    del args_types['return']
    return args_types