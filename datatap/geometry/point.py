from __future__ import annotations

from typing import Any, Tuple, Union, overload

from ..utils import basic_repr

PointJson = Tuple[float, float]

class Point:
	"""
	A point in 2D space.  Also often used to represent a 2D vector.
	"""

	x: float
	"""
	The x-coordinate of the point.
	"""

	y: float
	"""
	The y-coordinate of the point.
	"""

	@staticmethod
	def from_json(json: PointJson) -> Point:
		"""
		Creates a `Point` from a `PointJson`.
		"""
		return Point(json[0], json[1])

	def __init__(self, x: float, y: float, clip: bool = False):
		self.x = min(max(x, 0), 1) if clip else x
		self.y = min(max(y, 0), 1) if clip else y

	def to_json(self) -> PointJson:
		"""
		Serializes this object as a `PointJson`.
		"""
		return (self.x, self.y)

	def distance(self, other: Point) -> float:
		"""
		Computes the scalar distance to another point.
		"""
		return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5

	def assert_valid(self) -> None:
		"""
		Asserts that this polygon is valid on the unit plane.
		"""
		assert 0 <= self.x <= 1 and 0 <= self.y <= 1, f"Point coordinates must be between 0 and 1; failed on point {repr(self)}"

	def clip(self) -> Point:
		"""
		Clips both coordinates of this point to the range [0, 1].
		"""
		return Point(self.x, self.y, clip = True)

	def scale(self, factor: Union[float, int, Tuple[float, float], Point]) -> Point:
		"""
		Resizes the point according to `factor`. The scaling factor can either
		be a scalar (`int` or `float`), in which case the point will be scaled
		by the same factor on both axes, or a point-like (`Tuple[float, float]`
		or `Point`), in which case the point will be scaled independently on
		each axis.
		"""
		if isinstance(factor, (float, int)):
			return self * factor
		if isinstance(factor, tuple):
			return Point(self.x * factor[0], self.y * factor[1])
		return Point(self.x * factor.x, self.x * factor.y)

	@overload
	def __add__(self, o: Point) -> Point: ...
	def __add__(self, o: Any) -> Point:
		if isinstance(o, Point):
			return Point(self.x + o.x, self.y + o.y)
		return NotImplemented

	@overload
	def __sub__(self, o: Point) -> Point: ...
	def __sub__(self, o: Any) -> Point:
		if isinstance(o, Point):
			return Point(self.x - o.x, self.y - o.y)
		return NotImplemented

	@overload
	def __mul__(self, o: int) -> Point: ...
	@overload
	def __mul__(self, o: float) -> Point: ...
	def __mul__(self, o: Any) -> Point:
		if isinstance(o, (int, float)):
			return Point(self.x * o, self.y * o)
		return NotImplemented

	@overload
	def __truediv__(self, o: int) -> Point: ...
	@overload
	def __truediv__(self, o: float) -> Point: ...
	def __truediv__(self, o: Any) -> Point:
		if isinstance(o, (int, float)):
			return Point(self.x / o, self.y / o)
		return NotImplemented

	def __repr__(self) -> str:
		return basic_repr("Point", self.x, self.y)

	def __hash__(self) -> int:
		return hash((self.x, self.y))

	def __eq__(self, other: Any) -> bool:
		if not isinstance(other, Point):
			return NotImplemented
		return self.x == other.x and self.y == other.y
