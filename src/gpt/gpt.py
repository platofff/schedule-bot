import asyncio
import datetime
import inspect
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict, field, is_dataclass, fields
from enum import Enum
from os import environ
from typing import List, Type, Callable, Union, Any, FrozenSet

import openai
import tiktoken
from docstring_parser import parse as parse_docstring, Docstring
from frozendict import frozendict

from src.bot.entities import User
from src.gpt.keys import OpenAIKeysManager
from src.gpt.rate_limit import get_remaining_tokens, decrease_remaining_tokens
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
    if issubclass(x, GPTEnum):
        return 'enum'
    return 'object'


def get_args_without_defaults(func: Callable) -> List[str]:
    signature = inspect.signature(func)
    parameters = signature.parameters

    result = [name for name, param in parameters.items() if param.default is param.empty]

    try:
        si = result.index('self')
        result.pop(si)
    except ValueError:
        pass

    return result


@dataclass
class GPTFunction(ABC):
    name: str
    description: str = field(default=None, init=False, repr=False)
    parameters: frozendict = field(default=None, init=False, repr=False)


    def _get_properties(self, doc: Docstring) -> dict:
        result = {}
        th = self.get_args_types()
        def process_type(_type: Any, first_level=True) -> dict:
            type_name = openai_type_name(_type)

            entry = {}

            if type_name == 'enum':
                entry['enum'] = list(_type.possible_values)
                type_name = _type.type_name

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

    @abstractmethod
    async def __call__(self, *args, **kwargs):
        raise NotImplementedError

    def get_args_types(self):
        return get_args_types(self.__call__)

    def to_dict(self):
        return {
            'name': self.name,
            'description': self.description,
            'parameters': self.parameters
        }

    def __post_init__(self):
        doc = parse_docstring(self.__call__.__doc__)
        self.description = doc.short_description
        self.parameters = frozendict({
            'type': 'object',
            'properties': self._get_properties(doc),
            'required': GPTFunction._get_required(self.__call__)
        })

class GPTEnum:
    type_name: str
    possible_values: FrozenSet

    def __new__(cls, value):
        if value not in cls.possible_values:
            raise ValueError(f'GPTEnum value must be in {cls.possible_values}')
        return super(GPTEnum, cls).__new__(cls, value)

class GPTStringEnum(GPTEnum, str):
    type_name = 'string'
    possible_values: FrozenSet[str]

class GPTIntegerEnum(GPTEnum, int):
    type_name = 'integer'
    possible_values: FrozenSet[int]

@dataclass
class GPTOutputFunction(GPTFunction, ABC):
     @classmethod
     @abstractmethod
     def format_result(cls, result: Any) -> str:
         raise NotImplementedError

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.date):
            return obj.isoformat()
        return super(JSONEncoder, self).default(obj)


tiktoken_encoding = tiktoken.encoding_for_model(environ['OPENAI_MODEL'])

async def get_gpt_response(user: User, _messages: List[GPTMessage],
                           _functions: Union[List[GPTFunction], None] = None) -> str:
    messages = [asdict(m) for m in _messages]
    functions = json.loads(json.dumps([f.to_dict() for f in _functions], cls=JSONEncoder)) # TODO
    f_call = 'auto'

    while True:
        (remaining_tokens, limit), openai_key = await asyncio.gather(get_remaining_tokens(user),
                                                                     OpenAIKeysManager.get_key())
        if remaining_tokens > 0:
            remaining_tokens -= len(tiktoken_encoding.encode(f'{" ".join(m["content"] for m in messages)} {functions}'))
        if remaining_tokens <= 0:
            return f'Исчерпан лимит запросов умного помощника! Он станет доступен через {limit} секунд'
        try:
            resp = await openai.ChatCompletion.acreate(
                model=environ['OPENAI_MODEL'],
                messages=messages,
                functions=functions,
                function_call=f_call,
                temperature=0.5,
                api_key=openai_key,
                max_tokens=remaining_tokens
            )
        except openai.error.OpenAIError:
            await OpenAIKeysManager.delay_key(openai_key)
            continue

        logging.info(f'GPT response: {resp}')

        choice = resp['choices'][0]
        await decrease_remaining_tokens(user, resp['usage']['total_tokens'])
        if choice['finish_reason'] == 'function_call' or 'function_call' in choice['message']:
            fc = choice['message']['function_call']
            messages.append(choice['message'])
            for function in _functions:
                if function.name == fc['name']:
                    arguments = json.loads(fc['arguments'])
                    arguments = initialize_dataclasses(arguments, function.__call__)
                    result = await function(**arguments)
                    if isinstance(function, GPTOutputFunction):
                        return function.format_result(result)
                    else:
                        messages.append(asdict(GPTFunctionMessage(name=function.name,
                                                                  content=
                            json.dumps(result, cls=JSONEncoder, ensure_ascii=False))))
                        f_call = {'name': '...'} # TODO: make post-functions support
                    break
        elif choice['finish_reason'] == 'stop':
            return choice['message']['content']
        else:
            logging.error(f'Unexpected stop reason: {choice}')
            return 'Ошибка'
