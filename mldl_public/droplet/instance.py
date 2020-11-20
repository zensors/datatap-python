from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

from typing_extensions import TypedDict

from ..utils import basic_repr
from .bounding_box import BoundingBox, BoundingBoxJson
from .keypoint import Keypoint, KeypointJson
from .segmentation import Segmentation, SegmentationJson


class InstanceJson(TypedDict, total = False):
	boundingBox: BoundingBoxJson
	segmentation: SegmentationJson
	keypoints: Mapping[str, Optional[KeypointJson]]
	attributes: Mapping[str, str]

class Instance:
	bounding_box: Optional[BoundingBox]
	segmentation: Optional[Segmentation]
	keypoints: Optional[Mapping[str, Optional[Keypoint]]]
	attributes: Optional[Mapping[str, str]]

	@staticmethod
	def from_json(json: InstanceJson) -> Instance:
		return Instance(
			bounding_box = BoundingBox.from_json(json["boundingBox"]) if "boundingBox" in json else None,
			segmentation = Segmentation.from_json(json["segmentation"]) if "segmentation" in json else None,
			keypoints = {
				name: Keypoint.from_json(keypoint) if keypoint is not None else None
				for name, keypoint in json["keypoints"].items()
			} if "keypoints" in json else None,
			attributes = json.get("attributes")
		)

	def __init__(
		self,
		*,
		bounding_box: Optional[BoundingBox] = None,
		segmentation: Optional[Segmentation] = None,
		keypoints: Optional[Mapping[str, Optional[Keypoint]]] = None,
		attributes: Optional[Mapping[str, str]] = None
	):
		self.bounding_box = bounding_box
		self.segmentation = segmentation
		self.keypoints = keypoints
		self.attributes = attributes

	def __repr__(self) -> str:
		return basic_repr(
			"Instance",
			bounding_box = self.bounding_box,
			segmentation = self.segmentation,
			keypoints = self.keypoints,
			attributes = self.attributes
		)

	def __eq__(self, other: Any) -> bool:
		if not isinstance(other, Instance):
			return NotImplemented
		return (self.bounding_box == other.bounding_box and self.segmentation == other.segmentation
			and self.keypoints == other.keypoints and self.attributes == other.attributes)

	def to_json(self) -> InstanceJson:
		json: InstanceJson = {}

		if self.bounding_box is not None:
			json["boundingBox"] = self.bounding_box.to_json()

		if self.segmentation is not None:
			json["segmentation"] = self.segmentation.to_json()

		if self.keypoints is not None:
			keypoints: Dict[str, Optional[KeypointJson]] = {}

			for name, keypoint in self.keypoints.items():
				keypoints[name] = keypoint.to_json() if keypoint is not None else None

			json["keypoints"] = keypoints

		if self.attributes is not None:
			json["attributes"] = self.attributes

		return json
