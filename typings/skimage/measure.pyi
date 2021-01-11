from typing import Optional, Sequence

import numpy as np


Polygon = np.ndarray

def approximate_polygon(polygon: Polygon, tolerance: float) -> Polygon: ...
def find_contours(image: np.ndarray, level: Optional[float]) -> Sequence[Polygon]: ...
