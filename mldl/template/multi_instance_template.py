from __future__ import annotations

from typing import Any, Dict

from ..utils import basic_repr


class MultiInstanceTemplate():
	bounding_box: bool
	segmentation: bool

	def __init__(
		self,
		*,
		bounding_box: bool = False,
		segmentation: bool = False
	):
		self.bounding_box = bounding_box
		self.segmentation = segmentation

	def to_json(self):
		json = {}
		if self.bounding_box: json["boundingBox"] = True
		if self.segmentation: json["segmentation"] = True
		return json

	@staticmethod
	def from_json(json: Dict[str, Any]):
		bounding_box = json.get("boundingBox", False)
		segmentation = json.get("segmentation", False)
		return MultiInstanceTemplate(bounding_box=bounding_box, segmentation=segmentation)

	def __repr__(self):
		return basic_repr(
			"MultiInstanceTemplate",
			bounding_box = self.bounding_box,
			segmentation = self.segmentation
		)
