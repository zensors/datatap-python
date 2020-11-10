from __future__ import annotations

import sys
from typing import Any, Dict, List, Tuple, Union, cast

ansi = {
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

def color_repr(entity: Any) -> str:
	if entity is None:
		return f"{ansi['orange']}None{ansi['clear']}"
	if isinstance(entity, str):
		return f"{ansi['cyan']}\"{ansi['green']}{entity}{ansi['clear']}{ansi['cyan']}\"{ansi['clear']}"
	if isinstance(entity, (int, float)):
		return f"{ansi['orange']}{entity}{ansi['clear']}"
	if isinstance(entity, (list, tuple)):
		entity_list = cast(Union[List[Any], Tuple[Any]], entity)
		return (
			f"{ansi['cyan']}{'[' if type(entity_list) == list else '('}" +
				f"{ansi['cyan']},{ansi['clear']} ".join([color_repr(e) for e in entity_list]) +
			f"{ansi['cyan']}{']' if type(entity_list) == list else ')'}"
		)
	if isinstance(entity, dict):
		entity_dict = cast(Dict[Any, Any], entity)
		return (
			f"{ansi['cyan']}{{" +
				f"{ansi['cyan']},{ansi['clear']} ".join([
					f"{color_repr(key)}{ansi['cyan']}: {color_repr(value)}"
					for key, value in entity_dict.items()
				]) +
			f"{ansi['cyan']}}}"
		)
	return repr(entity)

def basic_repr(class_name: str, *args: Any, **kwargs: Any) -> str:
	if not IS_INTERACTIVE:
		positional_properties = [repr(value) for value in args]
		named_properties = [f"{key} = {repr(value)}" for key, value in kwargs.items() if value is not None]
		properties = ", ".join(positional_properties + named_properties)
		return f"{class_name}({properties})"
	else:
		positional_properties = [
			f"{ansi['green']}{color_repr(value)}{ansi['clear']}"
			for value in args
		]
		named_properties = [
			f"{ansi['red']}{key} {ansi['purple']}= {color_repr(value)}"
			for key, value in kwargs.items()
			if value is not None
		]
		properties = f"{ansi['cyan']},{ansi['clear']} ".join(positional_properties + named_properties)
		return f"{ansi['yellow']}{class_name}{ansi['cyan']}({ansi['clear']}{properties}{ansi['cyan']}){ansi['clear']}"
