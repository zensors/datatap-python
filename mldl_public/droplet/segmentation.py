from __future__ import annotations

from typing import Any, Optional

from typing_extensions import TypedDict

from ..geometry import Mask, MaskJson
from ..utils import basic_repr

class _SegmentationJsonOptional(TypedDict, total = False):
	confidence: float

class SegmentationJson(_SegmentationJsonOptional, TypedDict):
	"""
	The serialized JSON representation of a segmentation.
	"""
	mask: MaskJson

class Segmentation:
	"""
	A `Segmentation` represents the area within an image taken up by a
	detection, specified as a `Mask`.
	"""

	mask: Mask
	"""
	The area within the image where the corresponding detection appears.
	"""

	confidence: Optional[float]
	"""
	The confidence associated with this segmentation.
	"""

	@staticmethod
	def from_json(json: SegmentationJson) -> Segmentation:
		"""
		Constructs a `Segmentation` from a `SegmentationJson`.
		"""
		return Segmentation(
			Mask.from_json(json["mask"]),
			confidence = json.get("confidence")
		)

	def __init__(self, mask: Mask, *, confidence: Optional[float] = None):
		self.mask = mask
		self.confidence = confidence

		self.mask.assert_valid()

	def __repr__(self) -> str:
		return basic_repr("Segmentation", self.mask, confidence = self.confidence)

	def __eq__(self, other: Any) -> bool:
		if not isinstance(other, Segmentation):
			return NotImplemented
		return self.mask == other.mask and self.confidence == other.confidence

	def to_json(self) -> SegmentationJson:
		"""
		Serializes this `Segmentation` to a `SegmentationJson`.
		"""
		json: SegmentationJson = {
			"mask": self.mask.to_json()
		}

		if self.confidence is not None:
			json["confidence"] = self.confidence

		return json

	def meets_confidence_threshold(self, threshold: float) -> bool:
		"""
		Returns `True` if and only if the confidence of this segmentation is
		either unset or is at least the given `threshold`.
		"""
		return self.confidence is None or self.confidence >= threshold
