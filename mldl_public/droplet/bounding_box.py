from __future__ import annotations

from typing import Any, Optional

from typing_extensions import TypedDict

from ..geometry import Rectangle, RectangleJson
from ..utils import basic_repr

class _BoundingBoxJsonOptional(TypedDict, total = False):
	confidence: float

class BoundingBoxJson(_BoundingBoxJsonOptional, TypedDict):
	"""
	The serialized JSON representation of a bounding box.
	"""
	rectangle: RectangleJson

class BoundingBox:
	"""
	A `BoundingBox` represents the area within an image taken up by a detection,
	specified as an axis-aligned rectangle.
	"""

	rectangle: Rectangle
	"""
	The area within the image where the corresponding detection appears.
	"""

	confidence: Optional[float]
	"""
	The confidence associated with this bounding box.
	"""

	@staticmethod
	def from_json(json: BoundingBoxJson) -> BoundingBox:
		"""
		Constructs a `BoundingBox` from a `BoundingBoxJson`.
		"""
		return BoundingBox(
			Rectangle.from_json(json["rectangle"]),
			confidence = json.get("confidence")
		)

	def __init__(self, rectangle: Rectangle, *, confidence: Optional[float] = None):
		self.rectangle = rectangle
		self.confidence = confidence

		self.rectangle.assert_valid()

	def __repr__(self) -> str:
		return basic_repr("BoundingBox", self.rectangle, confidence = self.confidence)

	def __eq__(self, other: Any) -> bool:
		if not isinstance(other, BoundingBox):
			return NotImplemented
		return self.rectangle == other.rectangle and self.confidence == other.confidence

	def to_json(self) -> BoundingBoxJson:
		"""
		Serializes this `BoundingBox` to a `BoundingBoxJson`.
		"""
		json: BoundingBoxJson = {
			"rectangle": self.rectangle.to_json()
		}

		if self.confidence is not None:
			json["confidence"] = self.confidence

		return json

	def meets_confidence_threshold(self, threshold: float) -> bool:
		"""
		Returns `True` if and only if the confidence of this bounding box is
		either unset or it is at least the given `threshold`.
		"""
		return self.confidence is None or self.confidence >= threshold
