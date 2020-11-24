from __future__ import annotations

from typing import Any, Dict, Optional

from ..utils import basic_repr
from .instance_template import InstanceTemplate
from .multi_instance_template import MultiInstanceTemplate


class ClassAnnotationTemplate():
	"""
	A `ClassAnnotationTemplate` describes what each class should provide.

	In practice, most of the specification is delegated to its constituent tepmlates,
	`instances` and `multi_instances`.
	"""

	instances: Optional[InstanceTemplate]
	"""
	An `InstanceTemplate` that describes how instances are structured.
	"""

	multi_instances: Optional[MultiInstanceTemplate]
	"""
	A `MultiInstanceTemplate` that describes how multi instances are structured.
	"""

	def __init__(
		self,
		*,
		instances: Optional[InstanceTemplate] = None,
		multi_instances: Optional[MultiInstanceTemplate] = None
	):
		self.instances = instances
		self.multi_instances = multi_instances

	def to_json(self) -> Dict[str, Any]:
		"""
		Serializes this object into JSON.
		"""
		json = {}
		if self.instances is not None: json["instances"] = self.instances.to_json()
		if self.multi_instances is not None: json["multiInstances"] = self.multi_instances.to_json()
		return json

	@staticmethod
	def from_json(json: Dict[str, Any]) -> ClassAnnotationTemplate:
		"""
		Deserializes a JSON object into a `ClassAnnotationTemplate`.
		"""
		instances = InstanceTemplate.from_json(json["instances"]) if "instances" in json else None
		multi_instances = MultiInstanceTemplate.from_json(json["multiInstances"]) if "multiInstances" in json else None
		return ClassAnnotationTemplate(instances=instances, multi_instances=multi_instances)

	def __repr__(self) -> str:
		return basic_repr(
			"ClassAnnotationTemplate",
			instances = self.instances,
			multi_instances = self.multi_instances
		)
