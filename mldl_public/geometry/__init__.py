"""
This module provides geometric primitives for storing or manipulating ML annotations.

Generally speaking, a geometric object is considered "valid" within MLDL when it lies entirely within the unit plane.
This is because annotations in MLDL are scaled to 0-to-1 along both axes so that they are resolution-independent.
This can be checked by invoking `assert_valid` on any of the geometric objects (though this is done automatically when
geometric constructs are used to create droplets).
"""

from .mask import Mask, MaskJson
from .point import Point, PointJson
from .polygon import Polygon, PolygonJson
from .rectangle import Rectangle, RectangleJson

__all__ = [
	"Mask",
	"MaskJson",
	"Point",
	"PointJson",
	"Polygon",
	"PolygonJson",
	"Rectangle",
	"RectangleJson"
]
