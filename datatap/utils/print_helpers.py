from __future__ import annotations

import sys
from typing import Any, Dict, List, Tuple, Union, cast

_ansi = {
    "gray": "\033[30m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "purple": "\033[35m",
    "cyan": "\033[36m",
    "white": "\033[37m",
    "black": "\033[38m",

    "orange": "\033[38;5;209m", # TODO(zwade): This is a bit closer to "salmon"

    "clear": "\033[0m",

    "prev": "\033[F",
    "start": "\033[G",
}

IS_INTERACTIVE = sys.stdout.isatty()
pretty_print: bool = False

def force_pretty_print():
    """
    By default, this library only uses pretty-printing when it's in an
    interactive environment (terminal, python shell, etc.). However, there are a
    few cases when pretty-printing is desired in a non-interactive environment,
    such as when running under Jupyter. Calling this function once will ensure
    all future prints will be pretty.
    """
    global pretty_print
    pretty_print = True

def pprint(fmt: str, *args: Any, print_args: Dict[str, Any] = {}, **kwargs: Any) -> None:
    """
    Pretty printer. The first argument is a format string, and the remaining
    arguments are the values for the string. Additionally, the format string
    can access a number of ansi escape codes such as colors, `clear`, `prev`,
    and `start`.

    ```py
    pprint("{prev}Progress: {orange}{i}{clear}/{total}, i=i, total=total)
    ```
    """
    print((fmt + "{clear}").format(*args, **{**kwargs, **_ansi}), **print_args)
    sys.stdout.flush()

def pprints(fmt: str, *args: Any, **kwargs: Any) -> str:
    """
    Pretty prints to a string.

    See `datatap.utils.pprint`.
    """
    return (fmt + "{clear}").format(*args, **{**kwargs, **_ansi})

def color_repr(entity: Any) -> str:
    """
    A dynamic pretty-printer that will syntax highlight different python
    entities.

    Rarely used on its own, see `datatap.utils.basic_repr`.
    """
    if entity is None:
        return f"{_ansi['orange']}None{_ansi['clear']}"
    if isinstance(entity, str):
        return f"{_ansi['cyan']}\"{_ansi['green']}{entity}{_ansi['clear']}{_ansi['cyan']}\"{_ansi['clear']}"
    if isinstance(entity, (int, float)):
        return f"{_ansi['orange']}{entity}{_ansi['clear']}"
    if isinstance(entity, (list, tuple)):
        entity_list = cast(Union[List[Any], Tuple[Any]], entity)
        return (
            f"{_ansi['cyan']}{'[' if type(entity_list) == list else '('}" +
                f"{_ansi['cyan']},{_ansi['clear']} ".join([color_repr(e) for e in entity_list]) +
            f"{_ansi['cyan']}{']' if type(entity_list) == list else ')'}"
        )
    if isinstance(entity, dict):
        entity_dict = cast(Dict[Any, Any], entity)
        return (
            f"{_ansi['cyan']}{{" +
                f"{_ansi['cyan']},{_ansi['clear']} ".join([
                    f"{color_repr(key)}{_ansi['cyan']}: {color_repr(value)}"
                    for key, value in entity_dict.items()
                ]) +
            f"{_ansi['cyan']}}}"
        )
    return repr(entity)

def basic_repr(class_name: str, *args: Any, **kwargs: Any) -> str:
    """
    A function to be used for defining a class's `__repr__` method.
    When possible, will pretty-print the object in a way that is both easy
    to read, and useful for testing.

    ```py
    from datatap.utils import basic_repr

    class Person:
        name: string
        age: int
        height: int

        def __repr__(self):
            return basic_repr("Person", name, age = age, height = height)
    ```
    """
    if not IS_INTERACTIVE and not pretty_print:
        positional_properties = [repr(value) for value in args]
        named_properties = [f"{key} = {repr(value)}" for key, value in kwargs.items() if value is not None]
        properties = ", ".join(positional_properties + named_properties)
        return f"{class_name}({properties})"
    else:
        positional_properties = [
            f"{_ansi['green']}{color_repr(value)}{_ansi['clear']}"
            for value in args
        ]
        named_properties = [
            f"{_ansi['red']}{key} {_ansi['purple']}= {color_repr(value)}"
            for key, value in kwargs.items()
            if value is not None
        ]
        properties = f"{_ansi['cyan']},{_ansi['clear']} ".join(positional_properties + named_properties)
        return f"{_ansi['yellow']}{class_name}{_ansi['cyan']}({_ansi['clear']}{properties}{_ansi['cyan']}){_ansi['clear']}"
