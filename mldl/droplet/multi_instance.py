from __future__ import annotations

from typing import Any, Mapping, Optional

from ..geometry import Mask, Rectangle
from ..utils import basic_repr


class MultiInstance:
	bounding_box: Rectangle
	segmentation: Optional[Mask]
	count: Optional[int]
	confidence: Optional[float] # TODO: should confidence be here or on the geometric pieces (i.e. bounding_box, segmentation)?

	@staticmethod
	def from_json(json: Mapping[str, Any]):
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

	def __repr__(self):
		return basic_repr(
			"MultiInstance",
			bounding_box = self.bounding_box,
			segmentation = self.segmentation,
			count = self.count,
			confidence = self.confidence
		)

	def __eq__(self, other: Any):
		if not isinstance(other, MultiInstance):
			return NotImplemented
		return self.bounding_box == other.bounding_box and self.segmentation == other.segmentation and self.count == other.count and self.confidence == other.confidence
