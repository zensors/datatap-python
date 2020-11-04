from typing import Optional, TypeVar, Callable

_T = TypeVar("_T")
_S = TypeVar("_S")

class OrNullish:
    @staticmethod
    def bind(val: Optional[_T], fn: Callable[[_T], Optional[_S]]) -> Optional[_S]:
        if val is None:
            return None
        else:
            return fn(val)