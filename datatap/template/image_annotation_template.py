from __future__ import annotations

from typing import Dict, Mapping

from typing_extensions import Literal, TypedDict

from ..utils import basic_repr
from .class_annotation_template import ClassAnnotationTemplate, ClassAnnotationTemplateJson

class ImageAnnotationTemplateJson(TypedDict):
	"""
	The serialized JSON representation of an image annotation template.
	"""

	kind: Literal["ImageAnnotationTemplate"]
	classes: Dict[str, ClassAnnotationTemplateJson]

class ImageAnnotationTemplate():
	"""
	Describes how an `ImageAnnotation` is structured.

	For each of its classes, it provides a `ClassAnnotationTemplate`.
	"""

	classes: Mapping[str, ClassAnnotationTemplate]
	"""
	A mapping from class name to `ClassAnnotationTemplate`.
	"""

	def __init__(self, *, classes: Mapping[str, ClassAnnotationTemplate]):
		self.classes = classes

	def to_json(self) -> ImageAnnotationTemplateJson:
		"""
		Serializes this object to JSON.
		"""
		return {
			"kind": "ImageAnnotationTemplate",
			"classes": {
				class_name: class_template.to_json()
				for class_name, class_template in self.classes.items()
			}
		}

	@staticmethod
	def from_json(json: ImageAnnotationTemplateJson) -> ImageAnnotationTemplate:
		"""
		Deserializes a JSON object into an `ImageAnnotationTemplate`.
		"""
		classes = {
			key: ClassAnnotationTemplate.from_json(value)
			for key, value in json.get("classes", {}).items()
		}

		return ImageAnnotationTemplate(classes=classes)

	def __repr__(self) -> str:
		return basic_repr(
			"ImageAnnotationTemplate",
			classes = self.classes
		)
