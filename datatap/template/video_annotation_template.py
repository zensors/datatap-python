from __future__ import annotations

from typing_extensions import Literal, TypedDict

from ..utils import basic_repr
from .frame_annotation_template import (FrameAnnotationTemplate,
                                        FrameAnnotationTemplateJson)


class VideoAnnotationTemplateJson(TypedDict):
	"""
	The serialized JSON representation of a video annotation template.
	"""

	kind: Literal["VideoAnnotationTemplate"]
	frames: FrameAnnotationTemplateJson

class VideoAnnotationTemplate():
	"""
	Describes how a `VideoAnnotation` is structured.

	It consists only of a `FrameAnnotationTemplate` that describes its frames.
	"""

	frames: FrameAnnotationTemplate
	"""
	A `FrameAnnotationTemplate` that describes how the frames are structured.
	"""

	def __init__(self, *, frames: FrameAnnotationTemplate):
		self.frames = frames

	def to_json(self) -> VideoAnnotationTemplateJson:
		"""
		Serializes this object to JSON.
		"""
		return {
			"kind": "VideoAnnotationTemplate",
			"frames": self.frames.to_json()
		}

	@staticmethod
	def from_json(json: VideoAnnotationTemplateJson) -> VideoAnnotationTemplate:
		"""
		Deserializes a JSON object into a `VideoAnnotationTemplate`.
		"""
		return VideoAnnotationTemplate(
			frames = FrameAnnotationTemplate.from_json(json["frames"])
		)

	def __repr__(self) -> str:
		return basic_repr(
			"VideoAnnotationTemplate",
			frames = self.frames
		)
