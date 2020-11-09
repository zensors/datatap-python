from __future__ import annotations

from typing import Any, Dict

from ..utils import basic_repr
from .image_annotation_template import ImageAnnotationTemplate


class VideoAnnotationTemplate():
	frames: ImageAnnotationTemplate

	def __init__(self, *, frames: ImageAnnotationTemplate):
		self.frames = frames

	def to_json(self):
		return { "frames": self.frames.to_json() }

	@staticmethod
	def from_json(json: Dict[str, Any]):
		frames = ImageAnnotationTemplate.from_json(json["frames"])
		return VideoAnnotationTemplate(frames=frames)

	def __repr__(self):
		return basic_repr(
			"VideoAnnotationTemplate",
			frames = self.frames
		)
