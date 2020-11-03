from __future__ import annotations

from typing import Any, Dict, Optional

from ..utils import basic_repr
from .instance_template import InstanceTemplate
from .multi_instance_template import MultiInstanceTemplate


class ClassAnnotationTemplate():
	instances: Optional[InstanceTemplate]
	multi_instances: Optional[MultiInstanceTemplate]

	def __init__(
		self,
		*,
		instances: Optional[InstanceTemplate] = None,
		multi_instances: Optional[MultiInstanceTemplate] = None
	):
		self.instances = instances
		self.multi_instances = multi_instances

	def to_json(self):
		json = {}
		if self.instances is not None: json["instances"] = self.instances.to_json()
		if self.multi_instances is not None: json["multiInstances"] = self.multi_instances.to_json()
		return json

	@staticmethod
	def from_json(json: Dict[str, Any]):
		instances = InstanceTemplate.from_json(json["instances"]) if "instances" in json else None
		multi_instances = MultiInstanceTemplate.from_json(json["multiInstances"]) if "multiInstances" in json else None
		return ClassAnnotationTemplate(instances=instances, multi_instances=multi_instances)

	def __repr__(self):
		return basic_repr(
			"ClassAnnotationTemplate",
			instances = self.instances,
			multi_instances = self.multi_instances
		)
