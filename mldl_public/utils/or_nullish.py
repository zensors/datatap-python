from typing import Optional, TypeVar, Callable

_T = TypeVar("_T")
_S = TypeVar("_S")

class OrNullish:
    """
    A helper class to represent the monad `α OrNullish = α | None`.
    """

    @staticmethod
    def bind(val: Optional[_T], fn: Callable[[_T], Optional[_S]]) -> Optional[_S]:
        """
        Monadically binds `fn` to the value of `val`.
        """
        if val is None:
            return None
        else:
            return fn(val)