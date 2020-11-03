from __future__ import annotations

from shapely.geometry import box
from typing import Any, Sequence, Tuple, Optional, Union, overload

from .point import Point, PointJson
from ..utils import basic_repr

RectangleJson = Tuple[PointJson, PointJson]

class Rectangle:
	p1: Point
	p2: Point

	@staticmethod
	def from_json(json: RectangleJson):
		return Rectangle(Point.from_json(json[0]), Point.from_json(json[1]))

	@staticmethod
	def from_point_set(points: Sequence[Point]):
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

	def assert_valid(self):
		self.p1.assert_valid()
		self.p2.assert_valid()
		assert self.p1.x < self.p2.x and self.p1.y < self.p2.y, f"Rectangle has non-positive area; failed on rectangle {repr(self)}"

	def to_json(self) -> RectangleJson:
		return (self.p1.to_json(), self.p2.to_json())

	def to_shapely(self):
		return box(self.p1.x, self.p1.y, self.p2.x, self.p2.y)

	def to_xywh_tuple(self) -> Tuple[float, float, float, float]:
		w = self.p2.x - self.p1.x
		h = self.p2.y - self.p1.y
		return (self.p1.x, self.p1.y, w, h)

	def to_xyxy_tuple(self) -> Tuple[float, float, float, float]:
		return (self.p1.x, self.p1.y, self.p2.x, self.p2.y)

	def area(self):
		return abs(self.p1.x - self.p2.x) * abs(self.p1.y - self.p2.y)

	def iou(self, other: Rectangle) -> float:
		x1 = max(self.p1.x, other.p1.x)
		y1 = max(self.p1.y, other.p1.y)
		x2 = min(self.p2.x, other.p2.x)
		y2 = min(self.p2.y, other.p2.y)
		intersection_area = max(x2 - x1, 0) * max(y2 - y1, 0)
		union_area = self.area() + other.area() - intersection_area
		return intersection_area / union_area

	def diagonal(self) -> float:
		return self.p1.distance(self.p2)

	def scale(self, factor: Union[float, int, Tuple[float, float], Point]):
		return Rectangle(self.p1.scale(factor), self.p2.scale(factor))

	def scale_from_center(self, scale: float) -> Rectangle:
		center = (self.p1 + self.p2) / 2
		return Rectangle(
			(self.p1 - center) * scale + center,
			(self.p2 - center) * scale + center
		)

	def clip(self) -> Rectangle:
		return Rectangle(self.p1.clip(), self.p2.clip())

	def normalize(self) -> Rectangle:
		return Rectangle(self.p1, self.p2, True)

	def __repr__(self):
		return basic_repr("Rectangle", self.p1, self.p2)

	def __hash__(self):
		return hash((self.p1, self.p2))

	def __eq__(self, other: Any) -> bool:
		if not isinstance(other, Rectangle):
			return NotImplemented
		return self.p1 == other.p1 and self.p2 == other.p2

	@overload
	def __mul__(self, o: int) -> Rectangle: ...
	@overload
	def __mul__(self, o: float) -> Rectangle: ...
	def __mul__(self, o: Any):
		return Rectangle(self.p1 * o, self.p2 * o)
