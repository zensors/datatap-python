from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

from ..geometry import Mask
from ..utils import basic_repr
from .class_annotation import ClassAnnotation
from .image import Image


class Annotation:
	image: Image
	classes: Mapping[str, ClassAnnotation]
	mask: Optional[Mask]

	@staticmethod
	def from_json(json: Mapping[str, Any]):
		return Annotation(
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

	def apply_confidence_threshold(self, threshold: float) -> Annotation:
		classes: Mapping[str, ClassAnnotation] = {}
		for class_name, class_annotation in self.classes.items():
			classes[class_name] = class_annotation.apply_confidence_threshold(threshold)

		return Annotation(
			image = self.image,
			classes = classes,
			mask = self.mask,
		)

	def __repr__(self):
		return basic_repr(
			"Annotation",
			image = self.image,
			mask = self.mask,
			classes = self.classes
		)

	def __eq__(self, other: Any):
		if not isinstance(other, Annotation):
			return NotImplemented
		return self.image == other.image and self.classes == other.classes and self.mask == other.mask

	def __add__(self, other: Any) -> Annotation:
		if not isinstance(other, Annotation):
			return NotImplemented

		classes: Dict[str, ClassAnnotation] = {}

		for key, value in self.classes.items():
			classes[key] = value

		for key, value in other.classes.items():
			if key in classes:
				classes[key] += value
			else:
				classes[key] = value

		return Annotation(
			image = self.image,
			classes = classes,
			mask = self.mask
		)