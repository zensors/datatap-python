from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

from typing_extensions import TypedDict

from .keypoint import Keypoint, KeypointJson
from ..geometry import Mask, MaskJson, Rectangle, RectangleJson
from ..utils import basic_repr

class _InstanceJsonOptional(TypedDict, total = False):
	segmentation: MaskJson
	keypoints: Mapping[str, Optional[KeypointJson]]
	attributes: Mapping[str, str]
	confidence: float

class InstanceJson(_InstanceJsonOptional, TypedDict):
	boundingBox: RectangleJson

class Instance:
	bounding_box: Rectangle
	segmentation: Optional[Mask]
	keypoints: Optional[Mapping[str, Optional[Keypoint]]]
	attributes: Optional[Mapping[str, str]]
	confidence: Optional[float] # TODO: should confidence be here or on the geometric pieces (i.e. bounding_box, segmentation)?

	@staticmethod
	def from_json(json: InstanceJson) -> Instance:
		return Instance(
			bounding_box = Rectangle.from_json(json["boundingBox"]),
			segmentation = Mask.from_json(json["segmentation"]) if "segmentation" in json else None,
			keypoints = {
				name: Keypoint.from_json(keypoint) if keypoint is not None else None
				for name, keypoint in json["keypoints"].items()
			} if "keypoints" in json else None,
			attributes = json.get("attributes"),
			confidence = json.get("confidence")
		)

	def __init__(
		self,
		*,
		bounding_box: Rectangle,
		segmentation: Optional[Mask] = None,
		keypoints: Optional[Mapping[str, Optional[Keypoint]]] = None,
		attributes: Optional[Mapping[str, str]] = None,
		confidence: Optional[float] = None
	):
		self.bounding_box = bounding_box
		self.segmentation = segmentation
		self.keypoints = keypoints
		self.attributes = attributes
		self.confidence = confidence

		self.bounding_box.assert_valid()
		if self.segmentation is not None: self.segmentation.assert_valid()

	def __repr__(self) -> str:
		return basic_repr(
			"Instance",
			bounding_box = self.bounding_box,
			segmentation = self.segmentation,
			keypoints = self.keypoints,
			attributes = self.attributes,
			confidence = self.confidence
		)

	def __eq__(self, other: Any) -> bool:
		if not isinstance(other, Instance):
			return NotImplemented
		return (self.bounding_box == other.bounding_box and self.segmentation == other.segmentation
			and self.keypoints == other.keypoints and self.attributes == other.attributes
			and self.confidence == other.confidence)

	def to_json(self) -> InstanceJson:
		json: InstanceJson = {
			"boundingBox": self.bounding_box.to_json()
		}

		if self.segmentation is not None:
			json["segmentation"] = self.segmentation.to_json()

		if self.keypoints is not None:
			keypoints: Dict[str, Optional[KeypointJson]] = {}

			for name, keypoint in self.keypoints.items():
				keypoints[name] = keypoint.to_json() if keypoint is not None else None

			json["keypoints"] = keypoints

		if self.attributes is not None:
			json["attributes"] = self.attributes

		if self.confidence is not None:
			json["confidence"] = self.confidence

		return json
