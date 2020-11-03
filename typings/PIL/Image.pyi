from typing import Tuple

class Image:
	size: Tuple[int, int]
	def convert(self, mode: str) -> Image: ...
