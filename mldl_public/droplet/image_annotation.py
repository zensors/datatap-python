from __future__ import annotations

from typing import Any, Callable, Dict, Mapping, Optional

from typing_extensions import TypedDict

from ..geometry import Mask, MaskJson
from ..utils import basic_repr
from .class_annotation import ClassAnnotation, ClassAnnotationJson
from .image import Image, ImageJson
from .instance import Instance
from .multi_instance import MultiInstance


class _ImageAnnotationJsonOptional(TypedDict, total = False):
	mask: MaskJson

class ImageAnnotationJson(_ImageAnnotationJsonOptional, TypedDict):
	image: ImageJson
	classes: Mapping[str, ClassAnnotationJson]

class ImageAnnotation:
	image: Image
	classes: Mapping[str, ClassAnnotation]
	mask: Optional[Mask]

	@staticmethod
	def from_json(json: Mapping[str, Any]) -> ImageAnnotation:
		return ImageAnnotation(
			image = Image.from_json(json["image"]),
			classes = {
				class_name: ClassAnnotation.from_json(json["classes"][class_name])
				for class_name in json["classes"]
			},
			mask = Mask.from_json(json["mask"]) if "mask" in json else None
		)

	def __init__(self, *, image: Image, classes: Mapping[str, ClassAnnotation], mask: Optional[Mask] = None):
		self.image = image
		self.classes = classes
		self.mask = mask

	def filter_detections(
		self,
		*,
		instance_filter: Callable[[Instance], bool],
		multi_instance_filter: Callable[[MultiInstance], bool]
	) -> ImageAnnotation:
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
		json: ImageAnnotationJson = {
			"image": self.image.to_json(),
			"classes": {
				name: class_annotation.to_json()
				for name, class_annotation in self.classes.items()
			}
		}

		if self.mask is not None:
			json["mask"] = self.mask.to_json()

		return json
