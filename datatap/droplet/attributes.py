from __future__ import annotations

from typing import Optional, Sequence, Union

from typing_extensions import TypedDict

from ..utils import basic_repr

class _AttributeValueOptional(TypedDict, total = False):
	confidence: float

class AttributeValueJson(_AttributeValueOptional, TypedDict):
	"""
	The serialized JSON representation of an attribute candidate value.
	"""
	value: str

AttributeValuesJson = Union[Sequence[AttributeValueJson], str]

class AttributeValue:
	value: str
	confidence: Optional[float]

	def __init__(self, value: str, *, confidence: Optional[float] = None) -> None:
		self.value = value
		self.confidence = confidence

	def to_json(self) -> AttributeValueJson:
		json = AttributeValueJson(value=self.value)
		if self.confidence is not None:
			json["confidence"] = self.confidence
		return json

	@staticmethod
	def from_json(json: AttributeValueJson) -> AttributeValue:
		return AttributeValue(json["value"], confidence=json.get("confidence"))

class AttributeValues:
	content: Sequence[AttributeValue]

	@staticmethod
	def from_json(json: AttributeValuesJson) -> AttributeValues:
		"""
		Constructs a `AttributeValues` from a `AttributeValuesJson`.
		"""
		if isinstance(json, str):
			return AttributeValues([AttributeValue(json)])
		return AttributeValues([AttributeValue.from_json(c) for c in json])

	def __init__(self, content: Sequence[AttributeValue]):
		self.content = content

	def __repr__(self) -> str:
		return basic_repr("AttributeValues", self.content)

	def to_json(self) -> Sequence[AttributeValueJson]:
		return [c.to_json() for c in self.content]

	def most_likely(self) -> Optional[AttributeValue]:
		"""
		Returns the most likely value of this specific attribute
		"""
		if len(self.content) == 0:
			return None

		return max(self.content, key=lambda c: c.confidence or 1.0)
