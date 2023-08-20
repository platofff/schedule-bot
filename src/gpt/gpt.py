import asyncio
import datetime
import inspect
import json
import logging
from abc import ABC, abstractmethod, ABCMeta
from dataclasses import dataclass, asdict, field, is_dataclass, fields
from enum import Enum
from typing import List, Type, Callable, Union, Any

import openai
from docstring_parser import parse as parse_docstring, Docstring
from frozendict import frozendict

from src.misc.dataclasses import initialize_dataclasses
from src.misc.typing import get_args_types


@dataclass
class GPTMessage:
    class Role(str, Enum):
        SYSTEM = 'system'
        USER = 'user'
        ASSISTANT = 'assistant'
        FUNCTION = 'function'

    role: Role
    content: str


@dataclass
class GPTFunctionMessage:
    name: str
    content: str
    role: GPTMessage.Role = field(default=GPTMessage.Role.FUNCTION)

def openai_type_name(x: Type):
    if x is str:
        return 'string'
    if x is int:
        return 'integer'
    if x is Enum:
        return 'enum'
    return 'object'


def get_args_without_defaults(func: Callable) -> List[str]:
    signature = inspect.signature(func)
    parameters = signature.parameters

    result = [name for name, param in parameters.items() if param.default is param.empty]

    try:
        si = result.index('self')
        result.pop(si)
    except IndexError:
        pass

    return result

class GPTFunctionMeta(ABCMeta):
    @staticmethod
    def _get_properties(f:Callable, doc: Docstring) -> dict:
        result = {}
        th = get_args_types(f)
        def process_type(_type: Any, first_level=True) -> dict:
            type_name = openai_type_name(_type)

            entry = {}

            if type_name == 'enum':
                entry['enum'] = [x.value for x in _type]
                type_name = openai_type_name(type(entry['enum'][0]))

            if type_name == 'object':
                if not is_dataclass(_type):
                    raise TypeError('All complex nested types of function arguments should be dataclasses')
                entry['properties'] = {}
                entry['required'] = get_args_without_defaults(_type.__init__)

                for _field in fields(_type):
                    e = process_type(_field.type, False)
                    e['description'] = _field.metadata['description']
                    entry['properties'][_field.name] = e

            if first_level:
                for param in doc.params:
                    if param.arg_name == arg_name:
                        entry['description'] = param.description
                        break

            entry['type'] = type_name

            return entry

        for arg_name, _type in th.items():
            result[arg_name] = process_type(_type)
        return result

    @staticmethod
    def _get_required(f: Callable) -> List[str]:
        return get_args_without_defaults(f)

    def __init__(cls, name, bases, dct):
        if len(cls.__abstractmethods__) == 0:
            doc = parse_docstring(cls.__call__.__doc__)
            cls.description = doc.short_description
            cls.parameters = frozendict({
                'type': 'object',
                'properties': GPTFunctionMeta._get_properties(cls.__call__, doc),
                'required': GPTFunctionMeta._get_required(cls.__call__)
            })

        super().__init__(name, bases, dct)


@dataclass
class GPTFunction(ABC, metaclass=GPTFunctionMeta):
    name: str
    description: str = field(default=None, init=False, repr=False)
    parameters: frozendict = field(default=None, init=False, repr=False)

    @abstractmethod
    async def __call__(self, *args, **kwargs):
        raise NotImplementedError


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.date):
            return obj.isoformat()
        return super(JSONEncoder, self).default(obj)

async def get_gpt_response(_messages: List[GPTMessage], _functions: Union[List[GPTFunction], None] = None) -> str:
    print([asdict(f) for f in _functions])
    messages = [asdict(m) for m in _messages]
    functions = json.loads(json.dumps([asdict(f) for f in _functions], cls=JSONEncoder)) # TODO

    while True:
        try:
            resp = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=messages,
                functions=functions,
            )
        except openai.error.RateLimitError:
            await asyncio.sleep(30)
            continue

        print(resp)

        choice = resp['choices'][0]
        if choice['finish_reason'] == 'function_call':
            fc = choice['message']['function_call']
            messages.append(choice['message'])
            for function in _functions:
                if function.name == fc['name']:
                    arguments = json.loads(fc['arguments'])
                    arguments = initialize_dataclasses(arguments, function.__call__)
                    result = str(await function(**arguments))
                    messages.append(asdict(GPTFunctionMessage(name=function.name, content=result)))
                    break
        elif choice['finish_reason'] == 'stop':
            return choice['message']['content']
        else:
            logging.error(f'Unexpected stop reason: {choice}')
            return 'Ошибка'
