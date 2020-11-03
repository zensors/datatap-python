from __future__ import annotations

from typing import Any


def basic_repr(class_name: str, *args: Any, **kwargs: Any) -> str:
	positional_properties = [repr(value) for value in args]
	named_properties = [f"{key} = {repr(value)}" for key, value in kwargs.items() if value is not None]
	properties = ", ".join(positional_properties + named_properties)
	return f"{class_name}({properties})"
