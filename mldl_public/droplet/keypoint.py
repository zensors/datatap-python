from __future__ import annotations

from typing import Any, Optional

from typing_extensions import TypedDict

from ..geometry import Point, PointJson
from ..utils import basic_repr

class _KeypointJsonOptional(TypedDict, total = False):
	occluded: bool

class KeypointJson(_KeypointJsonOptional, TypedDict):
	point: PointJson

class Keypoint:
	point: Point
	occluded: Optional[bool]
	confidence: Optional[float]

	@staticmethod
	def from_json(json: KeypointJson) -> Keypoint:
		return Keypoint(
			Point.from_json(json["point"]),
			occluded = json["occluded"],
			confidence = json.get("confidence")
		)

	def __init__(self, point: Point, *, occluded: Optional[bool], confidence: Optional[float] = None):
		self.point = point
		self.occluded = occluded
		self.confidence = confidence

		self.point.assert_valid()

	def __repr__(self) -> str:
		return basic_repr("Keypoint", self.point, occluded = self.occluded, confidence = self.confidence)

	def __eq__(self, other: Any) -> bool:
		if not isinstance(other, Keypoint):
			return NotImplemented
		return self.point == other.point and self.occluded == other.occluded and self.confidence == other.confidence

	def to_json(self) -> KeypointJson:
		json: KeypointJson = {
			"point": self.point.to_json()
		}

		if self.occluded is not None:
			json["occluded"] = self.occluded

		return json