from __future__ import annotations

from typing import Any, Optional

from typing_extensions import TypedDict

from ..utils import basic_repr
from .bounding_box import BoundingBox, BoundingBoxJson
from .segmentation import Segmentation, SegmentationJson


class MultiInstanceJson(TypedDict, total = False):
	"""
	The JSON serialization of a `MultiInstance`.
	"""
	boundingBox: BoundingBoxJson
	segmentation: SegmentationJson
	count: int

class MultiInstance:
	"""
	An appearance of a group of objects of a particular class in a particular image.

	There is not a strict definition as to when a group of instances should be categorized as a multi-instance.
	As such, when constructing a dataset, it is best to ensure that all of the `DataSource`s agree on what
	constitutes a `MultiInstance`. These are most often used in public datasets when the cost of annotating
	every instance would be too high.
	"""

	bounding_box: Optional[BoundingBox]
	"""
	The bounding box of this multi-instance.
	"""

	segmentation: Optional[Segmentation]
	"""
	The segmentation of this multi-instance.
	"""

	count: Optional[int]
	"""
	A count of how many true instances are encapsulated in this multi-instance.
	"""

	@staticmethod
	def from_json(json: MultiInstanceJson) -> MultiInstance:
		"""
		Creates a `MultiInstance` from a `MultiInstanceJson`.
		"""
		return MultiInstance(
			bounding_box = BoundingBox.from_json(json["boundingBox"]) if "boundingBox" in json else None,
			segmentation = Segmentation.from_json(json["segmentation"]) if "segmentation" in json else None,
			count = json.get("count")
		)

	def __init__(
		self,
		*,
		bounding_box: Optional[BoundingBox] = None,
		segmentation: Optional[Segmentation] = None,
		count: Optional[int] = None
	):
		self.bounding_box = bounding_box
		self.segmentation = segmentation
		self.count = count

	def __repr__(self) -> str:
		return basic_repr(
			"MultiInstance",
			bounding_box = self.bounding_box,
			segmentation = self.segmentation,
			count = self.count
		)

	def __eq__(self, other: Any) -> bool:
		if not isinstance(other, MultiInstance):
			return NotImplemented
		return self.bounding_box == other.bounding_box and self.segmentation == other.segmentation and self.count == other.count

	def to_json(self) -> MultiInstanceJson:
		"""
		Serializes this object as a `MultiInstanceJson`.
		"""
		json: MultiInstanceJson = {}

		if self.bounding_box is not None:
			json["boundingBox"] = self.bounding_box.to_json()

		if self.segmentation is not None:
			json["segmentation"] = self.segmentation.to_json()

		if self.count is not None:
			json["count"] = self.count

		return json
