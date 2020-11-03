from typing import Generic, Iterator, TypeVar

from .record import Record

T = TypeVar("T")

class Result(Generic[T]):
	def __iter__(self) -> Iterator[Record[T]]: ...
	def single(self) -> Record[T]: ...
