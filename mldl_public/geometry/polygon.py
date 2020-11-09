from __future__ import annotations

from typing import Any, Sequence, Tuple, Union, overload

from .point import Point, PointJson
from ..utils import basic_repr

PolygonJson = Sequence[PointJson]

class Polygon:
	points: Sequence[Point]

	@staticmethod
	def from_json(json: PolygonJson):
		return Polygon([Point.from_json(pt) for pt in json])

	def __init__(self, points: Sequence[Point]):
		self.points = points

		if len(self.points) < 3:
			raise ValueError(f"A polygon must have at least three points; failed on polygon {repr(self)}")

	def scale(self, factor: Union[float, int, Tuple[float, float], Point]):
		return Polygon([p.scale(factor) for p in self.points])

	def to_json(self) -> PolygonJson:
		return [point.to_json() for point in self.points]

	def assert_valid(self):
		for point in self.points:
			point.assert_valid()
		# TODO(mdsavage): check for self-intersection?

	def __repr__(self):
		return basic_repr("Polygon", self.points)

	def __eq__(self, other: Any):
		# TODO(mdsavage): currently, this requires the points to be in the same order, not just represent the same polygon
		if not isinstance(other, Polygon):
			return NotImplemented
		return self.points == other.points

	@overload
	def __mul__(self, o: int) -> Polygon: ...
	@overload
	def __mul__(self, o: float) -> Polygon: ...
	def __mul__(self, o: Any):
		return Polygon([p * o for p in self.points])
