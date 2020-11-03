from typing import ContextManager

from .session import Session

class Driver:
	def session(self) -> ContextManager[Session]: ...
