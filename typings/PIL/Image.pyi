from io import BytesIO
from typing import Tuple


class Image:
	size: Tuple[int, int]

	def convert(self, mode: str) -> Image: ...

def open(data: BytesIO) -> Image: ...
