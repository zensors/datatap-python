from __future__ import annotations

from typing import Any, Tuple, Union, overload

from ..utils import basic_repr

PointJson = Tuple[float, float]

class Point:
	x: float
	y: float

	@staticmethod
	def from_json(json: PointJson) -> Point:
		return Point(json[0], json[1])

	def __init__(self, x: float, y: float, clip: bool = False):
		self.x = min(max(x, 0), 1) if clip else x
		self.y = min(max(y, 0), 1) if clip else y

	def to_json(self) -> PointJson:
		return (self.x, self.y)

	def distance(self, other: Point) -> float:
		return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5

	def assert_valid(self) -> None:
		assert 0 <= self.x <= 1 and 0 <= self.y <= 1, f"Point coordinates must be between 0 and 1; failed on point {repr(self)}"

	def clip(self) -> Point:
		return Point(self.x, self.y, clip = True)

	def scale(self, factor: Union[float, int, Tuple[float, float], Point]) -> Point:
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
