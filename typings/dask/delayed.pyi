from typing import Generic, TypeVar

T = TypeVar("T")

class Delayed(Generic[T]):
	def compute(self) -> T: ...
