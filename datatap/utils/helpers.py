import time
from types import TracebackType
from typing import Dict, List, Callable, Generator, Optional, Tuple, TypeVar
from contextlib import contextmanager

from .print_helpers import pprint

_T = TypeVar("_T")
_U = TypeVar("_U")
_V = TypeVar("_V")

class DeletableGenerator(Generator[_T, _U, _V]):
    """
    A deletable generator wraps an existing generator with a deletion
    function to allow cleanup.
    """

    _gen: Generator[_T, _U, _V]
    _delete: Callable[[], None]

    def __init__(self, gen: Generator[_T, _U, _V], delete_thunk: Callable[[], None]):
        self._gen = gen
        self._delete = delete_thunk

    def __next__(self):
        return next(self._gen)

    def send(self, value: _U):
        return self._gen.send(value)

    def throw(self, excn: BaseException, val: None, tb: Optional[TracebackType]):
        return self._gen.throw(excn, val, tb)

    def __del__(self):
        self._delete()
        pass


def assert_one(item_list: List[_T]) -> _T:
    """
    Given a list of items, asserts that the list is a singleton,
    and returns its value.
    """
    if len(item_list) != 1:
        raise AssertionError(f"Expected one item in list, but found {len(item_list)}", item_list)

    return item_list[0]


_timer_state: Dict[str, Tuple[float, int]] = {}
@contextmanager
def timer(name: str):
    start = time.time()
    yield None
    end = time.time()

    value = end - start
    avg, count = _timer_state.get(name, (0.0, 0))
    count += 1
    avg += (value - avg) / count
    _timer_state[name] = (avg, count)

    pprint(
        "{blue}{name} took {yellow}{value:1.3f}s{blue} for an average of {yellow}{avg:1.3f}s",
        name = name,
        value = value,
        avg = avg,
    )