from __future__ import annotations

from typing import Any, Mapping, Optional, Sequence

from ..geometry import Mask
from ..utils import basic_repr
from .annotation import Annotation
from .video import Video


class VideoAnnotation:
	video: Video
	frames: Sequence[Annotation]
	mask: Optional[Mask]

	@staticmethod
	def from_json(json: Mapping[str, Any]):
		return VideoAnnotation(
			frames = [Annotation.from_json(annotation) for annotation in json["frames"]],
			video = Video.from_json(json["video"]),
			mask = Mask.from_json(json["mask"]) if "mask" in json else None
		)

	def __init__(self, *, video: Video, frames: Sequence[Annotation], mask: Optional[Mask] = None):
		self.video = video
		self.frames = frames
		self.mask = mask

		if any(frame.mask != self.mask for frame in self.frames):
			raise ValueError(
				"All frame annotations in a video annotation must have the same mask as the video annotation; "
				+ f"failed on video annotation {repr(self)}"
			)

	def __repr__(self):
		return basic_repr("VideoAnnotation", video = self.video, frames = self.frames, mask = self.mask)

	def __eq__(self, other: Any):
		if not isinstance(other, VideoAnnotation):
			return NotImplemented
		return self.frames == other.frames
