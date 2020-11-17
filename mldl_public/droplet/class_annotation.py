from __future__ import annotations

from typing import Any, Sequence

from typing_extensions import TypedDict

from ..utils import basic_repr
from .instance import Instance, InstanceJson
from .multi_instance import MultiInstance, MultiInstanceJson

class ClassAnnotationJson(TypedDict, total = False):
	instances: Sequence[InstanceJson]
	multiInstances: Sequence[MultiInstanceJson]

class ClassAnnotation:
	instances: Sequence[Instance]
	multi_instances: Sequence[MultiInstance]

	@staticmethod
	def from_json(json: ClassAnnotationJson) -> ClassAnnotation:
		return ClassAnnotation(
			instances = [Instance.from_json(instance) for instance in json["instances"]] if "instances" in json else [],
			multi_instances = [MultiInstance.from_json(multi_instance) for multi_instance in json["multiInstances"]] if "multiInstances" in json else []
		)

	def __init__(self, *, instances: Sequence[Instance], multi_instances: Sequence[MultiInstance] = []):
		self.instances = instances
		self.multi_instances = multi_instances

	def apply_confidence_threshold(self, threshold: float) -> ClassAnnotation:
			instances = [
				instance
				for instance in self.instances
				if instance.confidence is None or instance.confidence >= threshold
			]
			multi_instances = [
				multi_instance
				for multi_instance in self.multi_instances
				if multi_instance.confidence is None or multi_instance.confidence >= threshold
			]

			return ClassAnnotation(
				instances = instances,
				multi_instances = multi_instances,
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
		return {
			"instances": [instance.to_json() for instance in self.instances],
			"multiInstances": [multi_instance.to_json() for multi_instance in self.multi_instances]
		}
