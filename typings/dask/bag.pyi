from typing import Generic, Iterable, TypeVar, List

from .delayed import Delayed

T = TypeVar("T")

class Bag(Generic[T]):
	def to_delayed(self) -> List[Delayed[List[T]]]: ...
	def take(self, count: int) -> List[T]: ...

def from_delayed(delayed: Iterable[Delayed[Iterable[T]]]) -> Bag[T]: ...