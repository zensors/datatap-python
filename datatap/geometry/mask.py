from __future__ import annotations
from datatap.geometry.point import Point

from typing import Any, Generator, Sequence, Tuple, Union

from .polygon import Polygon, PolygonJson
from ..utils import basic_repr

MaskJson = Sequence[PolygonJson]

class Mask:
	"""
	The shape resulting from XORing a set of polygons in 2D space.

	Generally, the expectation is that the polygons have no edge itersections; specifically, that for any pair of
	polygons in the mask, either they have no intersection or one completely contains the other.  However, there is no
	assertion that this is the case, and generally speaking, the even-odd rule is used to determine if a particular
	point is contained by the mask.
	"""

	polygons: Sequence[Polygon]
	"""
	The constituent polygons of this `Mask`.
	"""

	@staticmethod
	def from_json(json: MaskJson) -> Mask:
		"""
		Creates a `Mask` from a `MaskJson`.
		"""
		return Mask([Polygon.from_json(poly) for poly in json])

	def __init__(self, polygons: Sequence[Polygon]):
		self.polygons = polygons

		if len(self.polygons) < 1:
			raise ValueError(f"A mask must have at least one polygon; failed on mask {repr(self)}")

	def scale(self, factor: Union[float, int, Tuple[float, float], Point]) -> Mask:
		"""
		Resizes the mask according to `factor`. The scaling factor can either be
		a scalar (`int` or `float`), in which case the mask will be scaled by
		the same factor on both axes, or a point-like (`Tuple[float, float]`
		or `Point`), in which case the mask will be scaled independently on each
		axis.
		"""
		return Mask([p.scale(factor) for p in self.polygons])

	def to_json(self) -> MaskJson:
		"""
		Serializes this object as a `MaskJson`.
		"""
		return [polygon.to_json() for polygon in self.polygons]

	def assert_valid(self) -> None:
		"""
		Asserts that this mask is valid on the unit plane.
		"""
		for polygon in self.polygons:
			polygon.assert_valid()
		# TODO(mdsavage): check for invalid polygon intersections?

	def __repr__(self) -> str:
		return basic_repr("Mask", self.polygons)

	def __eq__(self, other: Any) -> bool:
		# TODO(mdsavage): currently, this requires the polygons to be in the same order, not just represent the same mask
		if not isinstance(other, Mask):
			return NotImplemented
		return self.polygons == other.polygons

	def __iter__(self) -> Generator[Polygon, None, None]:
		yield from self.polygons
