from __future__ import annotations

from typing_extensions import TypedDict

from ..utils import basic_repr

class MultiInstanceTemplateJson(TypedDict, total=False):
	"""
	The serialized JSON representation of a multi instance template.
	"""

	boundingBox: bool
	segmentation: bool
	count: bool

class MultiInstanceTemplate():
	"""
	Describes how an individual multi-instance is structured.
	"""

	bounding_box: bool
	"""
	If `bounding_box` is `True`, then all corresponding `MultiInstance`s will
	have a `BoundingBox` representing the bounds of their shape.
	"""

	segmentation: bool
	"""
	If `segmentation` is `True`, then all corresponding `MultiInstance`s will
	have a `Segmentation` tightly representing their shape.
	"""

	count: bool
	"""
	If `count` is `True`, then all corresponding `MultiInstance`s will have a
	count of how many true instances are present in the multi-instance.
	"""

	def __init__(
		self,
		*,
		bounding_box: bool = False,
		segmentation: bool = False,
		count: bool = False
	):
		self.bounding_box = bounding_box
		self.segmentation = segmentation
		self.count = count

	def to_json(self) -> MultiInstanceTemplateJson:
		json = MultiInstanceTemplateJson()
		if self.bounding_box: json["boundingBox"] = True
		if self.segmentation: json["segmentation"] = True
		if self.count: json["count"] = True
		return json

	@staticmethod
	def from_json(json: MultiInstanceTemplateJson) -> MultiInstanceTemplate:
		bounding_box = json.get("boundingBox", False)
		segmentation = json.get("segmentation", False)
		count = json.get("count", False)
		return MultiInstanceTemplate(
			bounding_box = bounding_box,
			segmentation = segmentation,
			count = count
		)

	def __repr__(self) -> str:
		return basic_repr(
			"MultiInstanceTemplate",
			bounding_box = self.bounding_box,
			segmentation = self.segmentation
		)
