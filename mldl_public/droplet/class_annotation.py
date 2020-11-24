from __future__ import annotations

from typing import Any, Callable, Sequence

from typing_extensions import TypedDict

from ..utils import basic_repr
from .instance import Instance, InstanceJson
from .multi_instance import MultiInstance, MultiInstanceJson

__pdoc__ = { "ClassAnnotation.__add__": True }

class ClassAnnotationJson(TypedDict, total = False):
	"""
	The serialized JSON representation of a class annotation.
	"""
	instances: Sequence[InstanceJson]
	multiInstances: Sequence[MultiInstanceJson]

class ClassAnnotation:
	"""
	A `ClassAnnotation` represents the set of detections for a given
	class. These may either be individual instances, or "multi instances"
	that describe a visual clustering of the class.
	"""

	instances: Sequence[Instance]
	"""
	A sequence of individual instances of this class.
	"""

	multi_instances: Sequence[MultiInstance]
	"""
	A sequence of multi-instances of this class. An example of a
	multi instance would be a crowd of people (labeled as such).
	"""

	@staticmethod
	def from_json(json: ClassAnnotationJson) -> ClassAnnotation:
		"""
		Constructs a `ClassAnnotation` from a `ClassAnnotationJson`.
		"""
		return ClassAnnotation(
			instances = [Instance.from_json(instance) for instance in json["instances"]] if "instances" in json else [],
			multi_instances = [MultiInstance.from_json(multi_instance) for multi_instance in json["multiInstances"]] if "multiInstances" in json else []
		)

	def __init__(self, *, instances: Sequence[Instance], multi_instances: Sequence[MultiInstance] = []):
		self.instances = instances
		self.multi_instances = multi_instances

	def filter_detections(
		self,
		*,
		instance_filter: Callable[[Instance], bool],
		multi_instance_filter: Callable[[MultiInstance], bool]
	) -> ClassAnnotation:
		"""
		Returns a new class annotation consisting only of the instances and
		multi-instances that meet the given constraints.
		"""
		return ClassAnnotation(
			instances = [
				instance
				for instance in self.instances
				if instance_filter(instance)
			],
			multi_instances = [
				multi_instance
				for multi_instance in self.multi_instances
				if multi_instance_filter(multi_instance)
			]
		)

	def __repr__(self) -> str:
		return basic_repr("ClassAnnotation", instances = self.instances, multi_instances = self.multi_instances)

	def __eq__(self, other: Any) -> bool:
		if not isinstance(other, ClassAnnotation):
			return NotImplemented
		return self.instances == other.instances and self.multi_instances == other.multi_instances

	def __add__(self, other: Any) -> ClassAnnotation:
		if not isinstance(other, ClassAnnotation):
			return NotImplemented

		instances = list(self.instances) + list(other.instances)
		multi_instances = list(self.multi_instances) + list(other.multi_instances)

		return ClassAnnotation(
			instances = instances,
			multi_instances = multi_instances,
		)

	def to_json(self) -> ClassAnnotationJson:
		"""
		Serializes this `ClassAnnotation` into a `ClassAnnotationJson`.
		"""

		return {
			"instances": [instance.to_json() for instance in self.instances],
			"multiInstances": [multi_instance.to_json() for multi_instance in self.multi_instances]
		}
