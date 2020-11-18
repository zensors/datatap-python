from __future__ import annotations

from typing import Any, Generator, Sequence, Tuple, Union, overload

from .point import Point, PointJson
from ..utils import basic_repr

PolygonJson = Sequence[PointJson]

class Polygon:
	"""
	A polygon in 2D space.
	"""

	points: Sequence[Point]
	"""
	The vertices of this polygon.
	"""

	@staticmethod
	def from_json(json: PolygonJson) -> Polygon:
		"""
		Creates a `Polygon` from a `PolygonJson`.
		"""
		return Polygon([Point.from_json(pt) for pt in json])

	def __init__(self, points: Sequence[Point]):
		self.points = points

		if len(self.points) < 3:
			raise ValueError(f"A polygon must have at least three points; failed on polygon {repr(self)}")

	def scale(self, factor: Union[float, int, Tuple[float, float], Point]) -> Polygon:
		"""
		Resizes the polygon according to `factor`. The scaling factor can either
		be a scalar (`int` or `float`), in which case the polygon will be scaled
		by the same factor on both axes, or a point-like (`Tuple[float, float]`
		or `Point`), in which case the polygon will be scaled independently on
		each axis.
		"""
		return Polygon([p.scale(factor) for p in self.points])

	def to_json(self) -> PolygonJson:
		"""
		Serializes this object as a `PolygonJson`.
		"""
		return [point.to_json() for point in self.points]

	def assert_valid(self) -> None:
		"""
		Ensures that this polygon is valid on the unit plane.
		"""
		for point in self.points:
			point.assert_valid()
		# TODO(mdsavage): check for self-intersection?

	def __repr__(self) -> str:
		return basic_repr("Polygon", self.points)

	def __eq__(self, other: Any) -> bool:
		# TODO(mdsavage): currently, this requires the points to be in the same order, not just represent the same polygon
		if not isinstance(other, Polygon):
			return NotImplemented
		return self.points == other.points

	@overload
	def __mul__(self, o: int) -> Polygon: ...
	@overload
	def __mul__(self, o: float) -> Polygon: ...
	def __mul__(self, o: Any) -> Polygon:
		return Polygon([p * o for p in self.points])

	def __iter__(self) -> Generator[Point, None, None]:
		yield from self.points