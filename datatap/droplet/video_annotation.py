from __future__ import annotations

from typing import Any, Callable, Mapping, Optional, Sequence
from datatap.droplet.video import Video, VideoJson

from typing_extensions import Literal, TypedDict

from ..utils import basic_repr
from .instance import Instance
from .multi_instance import MultiInstance
from .frame_annotation import FrameAnnotation, FrameAnnotationJson


class _VideoAnnotationJsonOptional(TypedDict, total = False):
	uid: str
	metadata: Mapping[str, Any]

class VideoAnnotationJson(_VideoAnnotationJsonOptional, TypedDict):
	"""
	The serialized JSON representation of an video annotation.
	"""

	kind: Literal["VideoAnnotation"]
	video: VideoJson
	frames: Sequence[FrameAnnotationJson]

class VideoAnnotation:
	"""
	A collection of class annotations that annotate a given image.
	"""

	video: Video
	"""
	The video being annotated.
	"""

	uid: Optional[str]
	"""
	A unique identifier for this image annotation.
	"""

	metadata: Optional[Mapping[str, Any]]
	"""
	An optional field for storing metadata on the annotation.
	"""

	@staticmethod
	def from_json(json: Mapping[str, Any]) -> VideoAnnotation:
		"""
		Constructs an `VideoAnnotation` from an `VideoAnnotationJson`.
		"""
		return VideoAnnotation(
			video = Video.from_json(json["video"]),
			frames = [FrameAnnotation.from_json(frame) for frame in json["frames"]],
			uid = json.get("uid"),
			metadata = json.get("metadata")
		)

	def __init__(
		self,
		*,
		video: Video,
		frames: Sequence[FrameAnnotation],
		uid: Optional[str] = None,
		metadata: Optional[Mapping[str, Any]] = None
	):
		self.video = video
		self.frames = frames
		self.uid = uid
		self.metadata = metadata

	def filter_detections(
		self,
		*,
		instance_filter: Callable[[Instance], bool],
		multi_instance_filter: Callable[[MultiInstance], bool]
	) -> VideoAnnotation:
		"""
		Returns a new image annotation consisting only of the instances and
		multi-instances that meet the given constraints.
		"""
		return VideoAnnotation(
			video = self.video,
			frames = [
				frame.filter_detections(
					instance_filter = instance_filter,
					multi_instance_filter = multi_instance_filter
				)
				for frame in self.frames
			],
			uid = self.uid,
			metadata = self.metadata
		)

	def apply_bounding_box_confidence_threshold(self, threshold: float) -> VideoAnnotation:
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

	def apply_segmentation_confidence_threshold(self, threshold: float) -> VideoAnnotation:
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

	def apply_metadata(self, metadata: Mapping[str, Any]) -> VideoAnnotation:
		"""
		Returns a new image annotation with the supplied metadata.
		"""
		return VideoAnnotation(
			video = self.video,
			frames = self.frames,
			uid = self.uid,
			metadata = metadata
		)

	def __repr__(self) -> str:
		return basic_repr(
			"VideoAnnotation",
			uid = self.uid,
			video = self.video,
			frames = self.frames,
			metadata = self.metadata
		)

	def __eq__(self, other: object) -> bool:
		if not isinstance(other, VideoAnnotation):
			return NotImplemented
		return (
			self.video == other.video
			and self.frames == other.frames
			and self.uid == other.uid
			and self.metadata == other.metadata
		)

	def __add__(self, other: VideoAnnotation) -> VideoAnnotation:
		if not isinstance(other, VideoAnnotation): # type: ignore - pyright complains about the isinstance check being redundant
			return NotImplemented

		if len(self.frames) != len(other.frames):
			raise ValueError("Unable to merge VideoAnnotations with different number of frames")

		return VideoAnnotation(
			video = self.video,
			frames = [
				frame1 + frame2
				for frame1, frame2 in zip(self.frames, other.frames)
			],
			uid = self.uid,
			metadata = self.metadata
		)

	def to_json(self) -> VideoAnnotationJson:
		"""
		Serializes this image annotation into an `VideoAnnotationJson`.
		"""
		json: VideoAnnotationJson = {
			"kind": "VideoAnnotation",
			"video": self.video.to_json(),
			"frames": [frame.to_json() for frame in self.frames]
		}

		if self.uid is not None:
			json["uid"] = self.uid

		if self.metadata is not None:
			json["metadata"] = self.metadata

		return json
