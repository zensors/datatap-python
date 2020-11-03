from typing import Any, ContextManager, Dict, TypeVar, Callable, overload

from neo4j.result import Result

from .transaction import Transaction


_F = TypeVar("_F")

class Session:
	def begin_transaction(self) -> ContextManager[Transaction]: ...

	def write_transaction(self, fn: Callable[[Transaction], _F]) -> _F: ...

	@overload
	def run(self, query: str, args: Dict[str, Any]) -> Result[_F]: ...
	@overload
	def run(self, query: str, **kwargs: Any) -> Result[_F]: ...
