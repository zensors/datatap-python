from __future__ import annotations

from typing import Optional

from typing_extensions import TypedDict

from ..utils import basic_repr
from .instance_template import InstanceTemplate, InstanceTemplateJson
from .multi_instance_template import MultiInstanceTemplate, MultiInstanceTemplateJson

class ClassAnnotationTemplateJson(TypedDict, total=False):
	"""
	The serialized JSON representation of a class annotation template.
	"""

	instances: InstanceTemplateJson
	multiInstances: MultiInstanceTemplateJson

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

	def to_json(self) -> ClassAnnotationTemplateJson:
		"""
		Serializes this object into JSON.
		"""
		json = ClassAnnotationTemplateJson()
		if self.instances is not None: json["instances"] = self.instances.to_json()
		if self.multi_instances is not None: json["multiInstances"] = self.multi_instances.to_json()
		return json

	@staticmethod
	def from_json(json: ClassAnnotationTemplateJson) -> ClassAnnotationTemplate:
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
