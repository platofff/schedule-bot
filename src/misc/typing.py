from typing import Callable


def get_args_types(f: Callable):
    args_types = f.__annotations__
    if 'return' in args_types:
        del args_types['return']
    return args_types