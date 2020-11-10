from __future__ import annotations

from typing import AbstractSet, Any, Dict, Mapping

from ..utils import basic_repr


class InstanceTemplate():
	bounding_box: bool
	segmentation: bool
	keypoints: AbstractSet[str]
	attributes: Mapping[str, AbstractSet[str]]
	identity: bool

	def __init__(
		self,
		*,
		bounding_box: bool = False,
		segmentation: bool = False,
		keypoints: AbstractSet[str] = set(),
		attributes: Mapping[str, AbstractSet[str]] = dict(),
		identity: bool = False
	):
		self.bounding_box = bounding_box
		self.segmentation = segmentation
		self.keypoints = keypoints
		self.attributes = attributes
		self.identity = identity

	def to_json(self) -> Dict[str, Any]:
		json = {}
		if self.bounding_box: json["boundingBox"] = True
		if self.segmentation: json["segmentation"] = True
		if len(self.keypoints) > 0: json["keypoints"] = list(self.keypoints)
		if len(self.attributes) > 0: json["attributes"] = { key: list(values) for key, values in self.attributes.items() }
		if self.identity: json["identity"] = True
		return json

	@staticmethod
	def from_json(json: Dict[str, Any]) -> InstanceTemplate:
		bounding_box = json.get("boundingBox", False)
		segmentation = json.get("segmentation", False)
		keypoints = set(json.get("keypoints", []))
		attributes = {
			key: set(values)
			for key, values in json.get("keypoints", {})
		}
		identity = json.get("identity", False)
		return InstanceTemplate(
			bounding_box=bounding_box,
			segmentation=segmentation,
			keypoints=keypoints,
			attributes=attributes,
			identity=identity,
		)

	def __repr__(self) -> str:
		return basic_repr(
			"InstanceTemplate",
			bounding_box = self.bounding_box,
			segmentation = self.segmentation,
			keypoints = self.keypoints,
			attributes = self.attributes,
			identity = self.identity
		)
