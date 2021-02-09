from __future__ import annotations

import json
from typing import Any, Callable, Dict, Mapping, Optional
from urllib.parse import quote, urlencode

from datatap.utils import Environment
from typing_extensions import Literal, TypedDict

from ..geometry import Mask, MaskJson
from ..utils import basic_repr
from .class_annotation import ClassAnnotation, ClassAnnotationJson
from .image import Image, ImageJson
from .instance import Instance
from .multi_instance import MultiInstance


class _ImageAnnotationJsonOptional(TypedDict, total = False):
	uid: str
	mask: MaskJson

class ImageAnnotationJson(_ImageAnnotationJsonOptional, TypedDict):
	"""
	The serialized JSON representation of an image annotation.
	"""

	kind: Literal["ImageAnnotation"]
	image: ImageJson
	classes: Mapping[str, ClassAnnotationJson]

class ImageAnnotation:
	"""
	A collection of class annotations that annotate a given image.
	"""

	image: Image
	"""
	The image being annotated.
	"""

	classes: Mapping[str, ClassAnnotation]
	"""
	A mapping from class name to the annotations of that class.
	"""

	uid: Optional[str]
	"""
	A unique identifier for this image annotation.
	"""

	mask: Optional[Mask]
	"""
	An optional region-of-interest mask to indicate that only
	features within the mask have been annotated.
	"""

	@staticmethod
	def from_json(json: Mapping[str, Any]) -> ImageAnnotation:
		"""
		Constructs an `ImageAnnotation` from an `ImageAnnotationJson`.
		"""
		return ImageAnnotation(
			image = Image.from_json(json["image"]),
			classes = {
				class_name: ClassAnnotation.from_json(json["classes"][class_name])
				for class_name in json["classes"]
			},
			mask = Mask.from_json(json["mask"]) if "mask" in json else None,
			uid = json.get("uid")
		)

	def __init__(
		self,
		*,
		image: Image,
		classes: Mapping[str, ClassAnnotation],
		mask: Optional[Mask] = None,
		uid: Optional[str] = None
	):
		self.image = image
		self.classes = classes
		self.mask = mask
		self.uid = uid

	def filter_detections(
		self,
		*,
		instance_filter: Callable[[Instance], bool],
		multi_instance_filter: Callable[[MultiInstance], bool]
	) -> ImageAnnotation:
		"""
		Returns a new image annotation consisting only of the instances and
		multi-instances that meet the given constraints.
		"""
		return ImageAnnotation(
			image = self.image,
			mask = self.mask,
			classes = {
				class_name: class_annotation.filter_detections(
					instance_filter = instance_filter,
					multi_instance_filter = multi_instance_filter
				)
				for class_name, class_annotation in self.classes.items()
			}
		)

	def apply_bounding_box_confidence_threshold(self, threshold: float) -> ImageAnnotation:
		"""
		Returns a new image annotation consisting only of the instances and
		multi-instances that have bounding boxes which either do not have a
		confidence specified or which have a confience meeting the given
		threshold.
		"""
		return self.filter_detections(
			instance_filter = lambda instance: (
				instance.bounding_box is not None
					and instance.bounding_box.meets_confidence_threshold(threshold)
			),
			multi_instance_filter = lambda multi_instance: (
				multi_instance.bounding_box is not None
					and multi_instance.bounding_box.meets_confidence_threshold(threshold)
			)
		)

	def apply_segmentation_confidence_threshold(self, threshold: float) -> ImageAnnotation:
		"""
		Returns a new image annotation consisting only of the instances and
		multi-instances that have segmentations which either do not have a
		confidence specified or which have a confience meeting the given
		threshold.
		"""
		return self.filter_detections(
			instance_filter = lambda instance: (
				instance.segmentation is not None
					and instance.segmentation.meets_confidence_threshold(threshold)
			),
			multi_instance_filter = lambda multi_instance: (
				multi_instance.segmentation is not None
					and multi_instance.segmentation.meets_confidence_threshold(threshold)
			)
		)

	def __repr__(self) -> str:
		return basic_repr(
			"ImageAnnotation",
			uid = self.uid,
			image = self.image,
			mask = self.mask,
			classes = self.classes
		)

	def __eq__(self, other: Any) -> bool:
		if not isinstance(other, ImageAnnotation):
			return NotImplemented
		return self.image == other.image and self.classes == other.classes and self.mask == other.mask

	def __add__(self, other: Any) -> ImageAnnotation:
		if not isinstance(other, ImageAnnotation):
			return NotImplemented

		classes: Dict[str, ClassAnnotation] = {}

		for key, value in self.classes.items():
			classes[key] = value

		for key, value in other.classes.items():
			if key in classes:
				classes[key] += value
			else:
				classes[key] = value

		return ImageAnnotation(
			image = self.image,
			classes = classes,
			mask = self.mask
		)

	def to_json(self) -> ImageAnnotationJson:
		"""
		Serializes this image annotation into an `ImageAnnotationJson`.
		"""
		json: ImageAnnotationJson = {
			"kind": "ImageAnnotation",
			"image": self.image.to_json(),
			"classes": {
				name: class_annotation.to_json()
				for name, class_annotation in self.classes.items()
			}
		}

		if self.mask is not None:
			json["mask"] = self.mask.to_json()

		if self.uid is not None:
			json["uid"] = self.uid

		return json

	def get_visualization_url(self) -> str:
		"""
		Generates a URL on the dataTap platform that can be visited to view a
		visualization of this `ImageAnnotation`.
		"""
		params = {
			"annotation": json.dumps(self.to_json(), separators = (",", ":"))
		}

		return f"{Environment.BASE_URI}/visualizer/single#{urlencode(params, quote_via = quote)}"

	def get_comparison_url(self, other: ImageAnnotation) -> str:
		"""
		Generates a URL on the dataTap platform that can be visited to view a
		visual comparison of this `ImageAnnotation` (which is treated as the
		"ground truth") and the `other` argument (which is treated as the
		"proposal").

		This method does not check that the two annotations agree on what image
		they are annotating, and will always use this `ImageAnnotation`'s
		image.
		"""
		params = {
			"groundTruth": json.dumps(self.to_json(), separators = (",", ":")),
			"proposal": json.dumps(other.to_json(), separators = (",", ":"))
		}

		return f"{Environment.BASE_URI}/visualizer/compare#{urlencode(params, quote_via = quote)}"
