from __future__ import annotations

from typing import Any, Dict, Mapping

from ..utils import basic_repr
from .class_annotation_template import ClassAnnotationTemplate

class ImageAnnotationTemplate():
	classes: Mapping[str, ClassAnnotationTemplate]

	def __init__(self, *, classes: Mapping[str, ClassAnnotationTemplate]):
		self.classes = classes

	def to_json(self) -> Dict[str, Any]:
		return {
			"classes": {
				class_name: class_template.to_json()
				for class_name, class_template in self.classes.items()
			}
		}

	@staticmethod
	def from_json(json: Dict[str, Any]) -> ImageAnnotationTemplate:
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
