from __future__ import annotations

from shapely.geometry import box, Polygon as ShapelyPolygon
from typing import Any, Sequence, Tuple, Union, overload

from .point import Point, PointJson
from ..utils import basic_repr

RectangleJson = Tuple[PointJson, PointJson]

class Rectangle:
	"""
	An axis-aligned rectangle in 2D space.
	"""

	p1: Point
	"""
	The top-left corner of the rectangle.
	"""

	p2: Point
	"""
	The bottom-right corner of the rectangle.
	"""

	@staticmethod
	def from_json(json: RectangleJson) -> Rectangle:
		"""
		Creates a `Rectangle` from a `RectangleJson`.
		"""
		return Rectangle(Point.from_json(json[0]), Point.from_json(json[1]))

	@staticmethod
	def from_point_set(points: Sequence[Point]) -> Rectangle:
		"""
		Creates the bounding rectangle of a set of points.

		Note, it is possible for this to create an invalid rectangle if all points
		are colinear and axis-aligned.
		"""
		return Rectangle(
			Point(min(p.x for p in points), min(p.y for p in points)),
			Point(max(p.x for p in points), max(p.y for p in points))
		)

	def __init__(self, p1: Point, p2: Point, normalize: bool = False):
		if normalize:
			self.p1 = Point(min(p1.x, p2.x), min(p1.y, p2.y))
			self.p2 = Point(max(p1.x, p2.x), max(p1.y, p2.y))
		else:
			self.p1 = p1
			self.p2 = p2

	def assert_valid(self) -> None:
		"""
		Ensures that this rectangle is valid on the unit plane.
		"""
		self.p1.assert_valid()
		self.p2.assert_valid()
		assert self.p1.x < self.p2.x and self.p1.y < self.p2.y, f"Rectangle has non-positive area; failed on rectangle {repr(self)}"

	def to_json(self) -> RectangleJson:
		"""
		Serializes this object as a `RectangleJson`.
		"""
		return (self.p1.to_json(), self.p2.to_json())

	def to_shapely(self) -> ShapelyPolygon:
		"""
		Converts this rectangle into a `Shapely.Polygon`.
		"""
		return box(self.p1.x, self.p1.y, self.p2.x, self.p2.y)

	def to_xywh_tuple(self) -> Tuple[float, float, float, float]:
		"""
		Converts this rectangle into a tuple of `(x_coordinate, y_coordinate, width, height)`.
		"""
		w = self.p2.x - self.p1.x
		h = self.p2.y - self.p1.y
		return (self.p1.x, self.p1.y, w, h)

	def to_xyxy_tuple(self) -> Tuple[float, float, float, float]:
		"""
		Converts this rectangle into a tuple of `(x_min, y_min, x_max, y_max)`.
		"""
		return (self.p1.x, self.p1.y, self.p2.x, self.p2.y)

	def area(self) -> float:
		"""
		Computes the area of this rectangle.
		"""
		return abs(self.p1.x - self.p2.x) * abs(self.p1.y - self.p2.y)

	def iou(self, other: Rectangle) -> float:
		"""
		Computes the iou (intersection-over-union) of this rectangle with another.
		"""
		x1 = max(self.p1.x, other.p1.x)
		y1 = max(self.p1.y, other.p1.y)
		x2 = min(self.p2.x, other.p2.x)
		y2 = min(self.p2.y, other.p2.y)
		intersection_area = max(x2 - x1, 0) * max(y2 - y1, 0)
		union_area = self.area() + other.area() - intersection_area
		return intersection_area / union_area

	def diagonal(self) -> float:
		"""
		Computes the diagonal length of this rectangle.
		"""
		return self.p1.distance(self.p2)

	def scale(self, factor: Union[float, int, Tuple[float, float], Point]):
		"""
		Resizes the rectangle according to `factor`. The scaling factor can
		either be a scalar (`int` or `float`), in which case the rectangle will
		be scaled by the same factor on both axes, or a point-like
		(`Tuple[float, float]` or `Point`), in which case the rectangle will be
		scaled independently on each axis.
		"""
		return Rectangle(self.p1.scale(factor), self.p2.scale(factor))

	def scale_from_center(self, factor: Union[float, int, Tuple[float, float], Point]) -> Rectangle:
		"""
		Resizes the rectangle according to `factor`, though translates it so
		that its center does not move. The scaling factor can either be a scalar
		(`int` or `float`), in which case the rectangle will be scaled by the
		same factor on both axes, or a point-like (`Tuple[float, float]` or
		`Point`), in which case the rectangle will be scaled independently on
		each axis.
		"""
		center = (self.p1 + self.p2) / 2
		return Rectangle(
			(self.p1 - center).scale(factor) + center,
			(self.p2 - center).scale(factor) + center
		)

	def clip(self) -> Rectangle:
		"""
		Clips the rectangle the unit-plane.
		"""
		return Rectangle(self.p1.clip(), self.p2.clip())

	def normalize(self) -> Rectangle:
		"""
		Returns a new rectangle that is guaranteed to have `p1` be the top left
		corner and `p2` be the bottom right corner.
		"""
		return Rectangle(self.p1, self.p2, True)

	def __repr__(self) -> str:
		return basic_repr("Rectangle", self.p1, self.p2)

	def __hash__(self) -> int:
		return hash((self.p1, self.p2))

	def __eq__(self, other: Any) -> bool:
		if not isinstance(other, Rectangle):
			return NotImplemented
		return self.p1 == other.p1 and self.p2 == other.p2

	@overload
	def __mul__(self, o: int) -> Rectangle: ...
	@overload
	def __mul__(self, o: float) -> Rectangle: ...
	def __mul__(self, o: Any) -> Rectangle:
		return Rectangle(self.p1 * o, self.p2 * o)
