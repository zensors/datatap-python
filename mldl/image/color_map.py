from palettable.cartocolors.qualitative import Vivid_10
from typing import Dict, Tuple, Optional, Sequence
from uuid import UUID

class ColorMap:
    palette: Sequence[Tuple[int, int, int]]
    map: Dict[Tuple[str, Optional[UUID]], Tuple[int, int, int]]
    palette_index: int

    def __init__(self, palette: Sequence[Tuple[int, int, int]] = Vivid_10.colors):
        self.palette = palette
        self.map = {}
        self.palette_index = 0

    def update_and_get(self, class_name: str, identity: Optional[UUID] = None):
        if (class_name, identity) in self.map:
            return self.map[(class_name, identity)]
        self.map[(class_name, identity)] = self.palette[self.palette_index % len(self.palette)]
        self.palette_index += 1
        return self.map[(class_name, identity)]

color_map = ColorMap()