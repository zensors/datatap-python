from io import BytesIO
from typing import Optional, Sequence, SupportsBytes, Tuple


class Image:
	size: Tuple[int, int]

	def convert(self, mode: str) -> Image: ...
	def resize(self, size: Tuple[int, int], resample: Optional[int]) -> Image: ...
	def getdata(self) -> Sequence[int]: ...

def open(data: BytesIO) -> Image: ...
def fromarray(buffer: SupportsBytes, mode: Optional[str]) -> Image: ...

BOX: int
