from __future__ import annotations

from typing import Dict, Mapping

from typing_extensions import TypedDict

from ..utils import basic_repr
from .class_annotation_template import ClassAnnotationTemplate, ClassAnnotationTemplateJson

class FrameAnnotationTemplateJson(TypedDict):
	"""
	The serialized JSON representation of a frame annotation template.
	"""

	classes: Dict[str, ClassAnnotationTemplateJson]

class FrameAnnotationTemplate():
	"""
	Describes how a `FrameAnnotation` is structured.

	For each of its classes, it provides a `ClassAnnotationTemplate`.
	"""

	classes: Mapping[str, ClassAnnotationTemplate]
	"""
	A mapping from class name to `ClassAnnotationTemplate`.
	"""

	def __init__(self, *, classes: Mapping[str, ClassAnnotationTemplate]):
		self.classes = classes

	def to_json(self) -> FrameAnnotationTemplateJson:
		"""
		Serializes this object to JSON.
		"""
		return {
			"classes": {
				class_name: class_template.to_json()
				for class_name, class_template in self.classes.items()
			}
		}

	@staticmethod
	def from_json(json: FrameAnnotationTemplateJson) -> FrameAnnotationTemplate:
		"""
		Deserializes a JSON object into a `FrameAnnotationTemplate`.
		"""
		classes = {
			key: ClassAnnotationTemplate.from_json(value)
			for key, value in json.get("classes", {}).items()
		}

		return FrameAnnotationTemplate(classes=classes)

	def __repr__(self) -> str:
		return basic_repr(
			"FrameAnnotationTemplate",
			classes = self.classes
		)
