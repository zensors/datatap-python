from __future__ import annotations

from typing import AbstractSet, Any, Dict, Mapping

from ..utils import basic_repr


class InstanceTemplate():
	"""
	Describes how an individual instance is structured.
	"""

	bounding_box: bool
	"""
	If `bounding_box` is `True`, then all corresponding `Instance`s will have a
	`BoundingBox` representing the bounds of their shape.
	"""

	segmentation: bool
	"""
	If `segmentation` is `True`, then all corresponding `Instance`s will have a
	`Segmentation` tightly representing their shape.
	"""

	keypoints: AbstractSet[str]
	"""
	For each keypoint name specified in `keypoints`, all corresponding instances
	will have a corresponding key in their `keypoints` field, the value of which
	will contain he keypoint if it is present or has an inferrable position in
	the image or `None` if it is not in-frame.
	"""

	attributes: Mapping[str, AbstractSet[str]]
	"""
	For each attribute name specified in `attributes`, all corresponding
	`Instance`s will provide one of the given values.
	"""

	def __init__(
		self,
		*,
		bounding_box: bool = False,
		segmentation: bool = False,
		keypoints: AbstractSet[str] = set(),
		attributes: Mapping[str, AbstractSet[str]] = dict(),
	):
		self.bounding_box = bounding_box
		self.segmentation = segmentation
		self.keypoints = keypoints
		self.attributes = attributes

	def to_json(self) -> Dict[str, Any]:
		"""
		Serializes this object as JSON.
		"""
		json = {}
		if self.bounding_box: json["boundingBox"] = True
		if self.segmentation: json["segmentation"] = True
		if len(self.keypoints) > 0: json["keypoints"] = list(self.keypoints)
		if len(self.attributes) > 0: json["attributes"] = { key: list(values) for key, values in self.attributes.items() }
		return json

	@staticmethod
	def from_json(json: Dict[str, Any]) -> InstanceTemplate:
		"""
		Deserializes a JSON object as an `InstanceTemplate`.
		"""
		bounding_box = json.get("boundingBox", False)
		segmentation = json.get("segmentation", False)
		keypoints = set(json.get("keypoints", []))
		attributes = {
			key: set(values)
			for key, values in json.get("keypoints", {})
		}
		return InstanceTemplate(
			bounding_box=bounding_box,
			segmentation=segmentation,
			keypoints=keypoints,
			attributes=attributes,
		)

	def __repr__(self) -> str:
		return basic_repr(
			"InstanceTemplate",
			bounding_box = self.bounding_box,
			segmentation = self.segmentation,
			keypoints = self.keypoints,
			attributes = self.attributes,
		)
