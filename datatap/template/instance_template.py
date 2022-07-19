from __future__ import annotations

from typing import AbstractSet, Dict, List, Mapping

from typing_extensions import TypedDict

from ..utils import basic_repr


class InstanceTemplateJson(TypedDict, total=False):
	"""
	The serialized JSON representation of an instance template.
	"""

	id: bool
	boundingBox: bool
	segmentation: bool
	keypoints: List[str]
	attributes: Dict[str, List[str]]

class InstanceTemplate():
	"""
	Describes how an individual instance is structured.
	"""

	id: bool
	"""
	If `id` is `True`, then all corresponding `Instance`s will have an ID
	that uniquely identifies the object represented by the instance in the
	context of the containing annotation.
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
		id: bool = False,
		bounding_box: bool = False,
		segmentation: bool = False,
		keypoints: AbstractSet[str] = set(),
		attributes: Mapping[str, AbstractSet[str]] = dict(),
	):
		self.id = id
		self.bounding_box = bounding_box
		self.segmentation = segmentation
		self.keypoints = keypoints
		self.attributes = attributes

	def to_json(self) -> InstanceTemplateJson:
		"""
		Serializes this object as JSON.
		"""
		json = InstanceTemplateJson()

		if self.id: json["id"] = True
		if self.bounding_box: json["boundingBox"] = True
		if self.segmentation: json["segmentation"] = True
		if len(self.keypoints) > 0: json["keypoints"] = list(self.keypoints)
		if len(self.attributes) > 0: json["attributes"] = { key: list(values) for key, values in self.attributes.items() }

		return json

	@staticmethod
	def from_json(json: InstanceTemplateJson) -> InstanceTemplate:
		"""
		Deserializes a JSON object as an `InstanceTemplate`.
		"""
		id = json.get("id", False)
		bounding_box = json.get("boundingBox", False)
		segmentation = json.get("segmentation", False)
		keypoints = set(json.get("keypoints", []))
		attributes = {
			key: set(values)
			for key, values in json.get("attributes", {}).items()
		}
		return InstanceTemplate(
			id = id,
			bounding_box=bounding_box,
			segmentation=segmentation,
			keypoints=keypoints,
			attributes=attributes,
		)

	def __repr__(self) -> str:
		return basic_repr(
			"InstanceTemplate",
			id = self.id,
			bounding_box = self.bounding_box,
			segmentation = self.segmentation,
			keypoints = self.keypoints,
			attributes = self.attributes,
		)
