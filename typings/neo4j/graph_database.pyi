from typing import Tuple
from .driver import Driver

class GraphDatabase:
	@staticmethod
	def driver(url: str, *, auth: Tuple[str, str]) -> Driver: ...
