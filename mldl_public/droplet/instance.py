from __future__ import annotations

from typing import Any, Mapping, Optional
from uuid import UUID

from .keypoint import Keypoint
from ..geometry import Mask, Rectangle
from ..utils import basic_repr


class Instance:
	bounding_box: Rectangle
	segmentation: Optional[Mask]
	keypoints: Optional[Mapping[str, Optional[Keypoint]]]
	attributes: Optional[Mapping[str, str]]
	confidence: Optional[float] # TODO: should confidence be here or on the geometric pieces (i.e. bounding_box, segmentation)?
	identity: Optional[UUID]

	@staticmethod
	def from_json(json: Mapping[str, Any]):
		return Instance(
			bounding_box = Rectangle.from_json(json["boundingBox"]),
			segmentation = Mask.from_json(json["segmentation"]) if "segmentation" in json else None,
			keypoints = {
				keypoint: Keypoint.from_json(json["keypoints"][keypoint])
				for keypoint in json["keypoints"]
			} if "keypoints" in json else None,
			attributes = json.get("attributes"),
			confidence = json.get("confidence"),
			identity = UUID(json["identity"]) if "identity" in json else None
		)

	def __init__(
		self,
		*,
		bounding_box: Rectangle,
		segmentation: Optional[Mask] = None,
		keypoints: Optional[Mapping[str, Optional[Keypoint]]] = None,
		attributes: Optional[Mapping[str, str]] = None,
		confidence: Optional[float] = None,
		identity: Optional[UUID] = None
	):
		self.bounding_box = bounding_box
		self.segmentation = segmentation
		self.keypoints = keypoints
		self.attributes = attributes
		self.confidence = confidence
		self.identity = identity

		self.bounding_box.assert_valid()
		if self.segmentation is not None: self.segmentation.assert_valid()

	def __repr__(self):
		return basic_repr(
			"Instance",
			bounding_box = self.bounding_box,
			segmentation = self.segmentation,
			keypoints = self.keypoints,
			attributes = self.attributes,
			confidence = self.confidence,
			identity = self.identity
		)

	def __eq__(self, other: Any):
		if not isinstance(other, Instance):
			return NotImplemented
		return (self.bounding_box == other.bounding_box and self.segmentation == other.segmentation
			and self.keypoints == other.keypoints and self.attributes == other.attributes
			and self.confidence == other.confidence and self.identity == other.identity)
