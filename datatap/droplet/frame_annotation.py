from __future__ import annotations

from typing import Any, Callable, Dict, Mapping

from typing_extensions import TypedDict

from ..utils import basic_repr
from .class_annotation import ClassAnnotation, ClassAnnotationJson
from .instance import Instance
from .multi_instance import MultiInstance

class FrameAnnotationJson(TypedDict):
	"""
	The serialized JSON representation of an image annotation.
	"""

	classes: Mapping[str, ClassAnnotationJson]

class FrameAnnotation:
	"""
	A collection of class annotations that annotate a given image.
	"""

	classes: Mapping[str, ClassAnnotation]
	"""
	A mapping from class name to the annotations of that class.
	"""

	@staticmethod
	def from_json(json: Mapping[str, Any]) -> FrameAnnotation:
		"""
		Constructs an `FrameAnnotation` from an `FrameAnnotationJson`.
		"""
		return FrameAnnotation(
			classes = {
				class_name: ClassAnnotation.from_json(json["classes"][class_name])
				for class_name in json["classes"]
			}
		)

	def __init__(
		self,
		*,
		classes: Mapping[str, ClassAnnotation],
	):
		self.classes = classes

	def filter_detections(
		self,
		*,
		instance_filter: Callable[[Instance], bool],
		multi_instance_filter: Callable[[MultiInstance], bool]
	) -> FrameAnnotation:
		"""
		Returns a new image annotation consisting only of the instances and
		multi-instances that meet the given constraints.
		"""
		return FrameAnnotation(
			classes = {
				class_name: class_annotation.filter_detections(
					instance_filter = instance_filter,
					multi_instance_filter = multi_instance_filter
				)
				for class_name, class_annotation in self.classes.items()
			}
		)

	def apply_bounding_box_confidence_threshold(self, threshold: float) -> FrameAnnotation:
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

	def apply_segmentation_confidence_threshold(self, threshold: float) -> FrameAnnotation:
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
			"FrameAnnotation",
			classes = self.classes
		)

	def __eq__(self, other: object) -> bool:
		if not isinstance(other, FrameAnnotation):
			return NotImplemented
		return self.classes == other.classes

	def __add__(self, other: FrameAnnotation) -> FrameAnnotation:
		if not isinstance(other, FrameAnnotation): # type: ignore - pyright complains about the isinstance check being redundant
			return NotImplemented

		classes: Dict[str, ClassAnnotation] = {}

		for key, value in self.classes.items():
			classes[key] = value

		for key, value in other.classes.items():
			if key in classes:
				classes[key] += value
			else:
				classes[key] = value

		return FrameAnnotation(
			classes = classes
		)

	def to_json(self) -> FrameAnnotationJson:
		"""
		Serializes this image annotation into an `FrameAnnotationJson`.
		"""
		json: FrameAnnotationJson = {
			"classes": {
				name: class_annotation.to_json()
				for name, class_annotation in self.classes.items()
			}
		}

		return json
