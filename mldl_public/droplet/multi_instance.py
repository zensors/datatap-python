from __future__ import annotations

from typing import Any, Mapping, Optional

from typing_extensions import TypedDict

from ..geometry import Mask, MaskJson, Rectangle, RectangleJson
from ..utils import basic_repr

class _MultiInstanceJsonOptional(TypedDict, total = False):
	segmentation: MaskJson
	count: int
	confidence: float

class MultiInstanceJson(_MultiInstanceJsonOptional, TypedDict):
	boundingBox: RectangleJson

class MultiInstance:
	bounding_box: Rectangle
	segmentation: Optional[Mask]
	count: Optional[int]
	confidence: Optional[float] # TODO: should confidence be here or on the geometric pieces (i.e. bounding_box, segmentation)?

	@staticmethod
	def from_json(json: Mapping[str, Any]) -> MultiInstance:
		return MultiInstance(
			bounding_box = Rectangle.from_json(json["boundingBox"]),
			segmentation = Mask.from_json(json["segmentation"]) if "segmentation" in json else None,
			count = json.get("count"),
			confidence = json.get("confidence")
		)

	def __init__(
		self,
		*,
		bounding_box: Rectangle,
		segmentation: Optional[Mask] = None,
		count: Optional[int] = None,
		confidence: Optional[float] = None
	):
		self.bounding_box = bounding_box
		self.segmentation = segmentation
		self.count = count
		self.confidence = confidence

		self.bounding_box.assert_valid()
		if self.segmentation is not None: self.segmentation.assert_valid()

	def __repr__(self) -> str:
		return basic_repr(
			"MultiInstance",
			bounding_box = self.bounding_box,
			segmentation = self.segmentation,
			count = self.count,
			confidence = self.confidence
		)

	def __eq__(self, other: Any) -> bool:
		if not isinstance(other, MultiInstance):
			return NotImplemented
		return self.bounding_box == other.bounding_box and self.segmentation == other.segmentation and self.count == other.count and self.confidence == other.confidence

	def to_json(self) -> MultiInstanceJson:
		json: MultiInstanceJson = {
			"boundingBox": self.bounding_box.to_json()
		}

		if self.segmentation is not None:
			json["segmentation"] = self.segmentation.to_json()

		if self.count is not None:
			json["count"] = self.count

		if self.confidence is not None:
			json["confidence"] = self.confidence

		return json
