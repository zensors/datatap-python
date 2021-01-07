from __future__ import annotations

from typing import Sequence, Tuple

import numpy as np
from typing_extensions import TypedDict


class CocoRleJson(TypedDict):
	counts: Sequence[int]
	size: Tuple[int, int]

class CocoRle:
	pass

def frPyObjects(json: CocoRleJson, height: int, width: int) -> CocoRle: ...
def decode(rle: CocoRle) -> np.ndarray: ...
