from __future__ import annotations

from typing import Dict, Mapping, Optional

from typing_extensions import TypedDict

from ..utils import basic_repr
from .attributes import AttributeValues, AttributeValuesJson
from .bounding_box import BoundingBox, BoundingBoxJson
from .keypoint import Keypoint, KeypointJson
from .segmentation import Segmentation, SegmentationJson


class InstanceJson(TypedDict, total = False):
	"""
	The JSON serialization of an `Instance`.
	"""
	id: str
	boundingBox: BoundingBoxJson
	segmentation: SegmentationJson
	keypoints: Mapping[str, Optional[KeypointJson]]
	attributes: Mapping[str, AttributeValuesJson]

class Instance:
	"""
	A single appearance of an object of a particular class within a given image.
	"""

	id: Optional[str]
	"""
	A unique id for this instance (within the context of its containing
	annotation).  Multiple instances with the same id should be interpreted
	to be the same object.
	"""

	bounding_box: Optional[BoundingBox]
	"""
	The bounding box of this instance.
	"""

	segmentation: Optional[Segmentation]
	"""
	The segmentation of this instance.
	"""

	keypoints: Optional[Mapping[str, Optional[Keypoint]]]
	"""
	A mapping from keypoint name to the keypoint within this instance.  If a key
	maps to `None`, then the annotation is reporting the _absence of_ that
	keypoint (i.e., that it is not visible in the image and does not have an
	inferrable position in the image).
	"""

	attributes: Optional[Mapping[str, AttributeValues]]
	"""
	A mapping from attribute name to value.
	"""

	@staticmethod
	def from_json(json: InstanceJson) -> Instance:
		"""
		Creates an `Instance` from an `InstanceJson`.
		"""
		return Instance(
			id = json.get("id"),
			bounding_box = BoundingBox.from_json(json["boundingBox"]) if "boundingBox" in json else None,
			segmentation = Segmentation.from_json(json["segmentation"]) if "segmentation" in json else None,
			keypoints = {
				name: Keypoint.from_json(keypoint) if keypoint is not None else None
				for name, keypoint in json["keypoints"].items()
			} if "keypoints" in json else None,
			attributes = {
				k: AttributeValues.from_json(v) for k, v in json["attributes"].items()
			} if "attributes" in json else None
		)

	def __init__(
		self,
		*,
		id: Optional[str] = None,
		bounding_box: Optional[BoundingBox] = None,
		segmentation: Optional[Segmentation] = None,
		keypoints: Optional[Mapping[str, Optional[Keypoint]]] = None,
		attributes: Optional[Mapping[str, AttributeValues]] = None
	):
		self.id = id
		self.bounding_box = bounding_box
		self.segmentation = segmentation
		self.keypoints = keypoints
		self.attributes = attributes

	def __repr__(self) -> str:
		return basic_repr(
			"Instance",
			id = self.id,
			bounding_box = self.bounding_box,
			segmentation = self.segmentation,
			keypoints = self.keypoints,
			attributes = self.attributes
		)

	def __eq__(self, other: object) -> bool:
		if not isinstance(other, Instance):
			return NotImplemented
		return (
			self.id == other.id
			and self.bounding_box == other.bounding_box
			and self.segmentation == other.segmentation
			and self.keypoints == other.keypoints
			and self.attributes == other.attributes
		)

	def to_json(self) -> InstanceJson:
		"""
		Serializes an `Instance` into an `InstanceJson`.
		"""
		json: InstanceJson = {}

		if self.id is not None:
			json["id"] = self.id

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
			json["attributes"] = {
				k: v.to_json() for k, v in self.attributes.items()
			}

		return json
