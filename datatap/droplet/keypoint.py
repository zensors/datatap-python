from __future__ import annotations

from typing import Any, Optional

from typing_extensions import TypedDict

from ..geometry import Point, PointJson
from ..utils import basic_repr

class _KeypointJsonOptional(TypedDict, total = False):
	occluded: bool
	confidence: float

class KeypointJson(_KeypointJsonOptional, TypedDict):
	"""
	The JSON serialization of a `Keypoint`.
	"""
	point: PointJson

class Keypoint:
	"""
	An object representing a specific keypoint in a particular instance.
	"""

	point: Point
	"""
	The point in the image where this keypoint appears.
	"""

	occluded: Optional[bool]
	"""
	Whether this keypoint is occluded.

	If `False`, the keypoint is visible within the image.
	If `True`, the keypoint is not visible in the image because it is blocked by some other object,
	but has an inferrable position that would lie within the frame of the image.
	If `None`, then the data source did not differentiate between occluded and unoccluded keypoints.
	"""

	confidence: Optional[float]
	"""
	The confidence associated with this keypoint.
	"""

	@staticmethod
	def from_json(json: KeypointJson) -> Keypoint:
		"""
		Creates a `Keypoint` from a `KeypointJson`.
		"""
		return Keypoint(
			Point.from_json(json["point"]),
			occluded = json.get("occluded"),
			confidence = json.get("confidence")
		)

	def __init__(self, point: Point, *, occluded: Optional[bool] = None, confidence: Optional[float] = None):
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
		"""
		Serializes this object into a `KeypointJson`.
		"""
		json: KeypointJson = {
			"point": self.point.to_json()
		}

		if self.occluded is not None:
			json["occluded"] = self.occluded

		if self.confidence is not None:
			json["confidence"] = self.confidence

		return json
