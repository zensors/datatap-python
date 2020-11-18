from __future__ import annotations
from mldl_public.geometry.point import Point

from typing import Any, Generator, List, Sequence, Tuple, Union

from .polygon import Polygon, PolygonJson
from ..utils import basic_repr

MaskJson = Sequence[PolygonJson]

class Mask:
	polygons: Sequence[Polygon]

	@staticmethod
	def from_json(json: MaskJson) -> Mask:
		return Mask([Polygon.from_json(poly) for poly in json])

	def __init__(self, polygons: Sequence[Polygon]):
		self.polygons = polygons

		if len(self.polygons) < 1:
			raise ValueError(f"A mask must have at least one polygon; failed on mask {repr(self)}")

	def scale(self, factor: Union[float, int, Tuple[float, float], Point]) -> Mask:
		return Mask([p.scale(factor) for p in self.polygons])

	def to_json(self) -> MaskJson:
		return [polygon.to_json() for polygon in self.polygons]

	def assert_valid(self) -> None:
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
