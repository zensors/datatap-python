from typing import Any, Dict, TypeVar, overload
from .result import Result

T = TypeVar("T")

class Transaction:
	@overload
	def run(self, query: str, args: Dict[str, Any]) -> Result[T]: ...
	@overload
	def run(self, query: str, **kwargs: Any) -> Result[T]: ...
