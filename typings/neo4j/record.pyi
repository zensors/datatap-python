from typing import Generic, Iterable, TypeVar

T = TypeVar("T")
V = TypeVar("V")
K = TypeVar("K", str, int)
R = TypeVar("R")

class Record(Generic[T], Iterable[V]):
	def __getitem__(self, key: K) -> R: ...

