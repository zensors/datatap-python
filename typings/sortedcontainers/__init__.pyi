from typing import Generic, Iterator, MutableMapping, TypeVar


K = TypeVar("K")
V = TypeVar("V")

class SortedDict(Generic[K, V], MutableMapping[K, V]):
	def __reversed__(self) -> Iterator[K]: ...
	def copy(self) -> SortedDict[K, V]: ...
