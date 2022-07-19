from __future__ import annotations

from typing import Optional, Sequence

from typing_extensions import TypedDict

from ..utils import basic_repr
from .image import Image, ImageJson


class VideoJson(TypedDict, total = False):
	"""
	The serialized JSON representation of an `Video`.
	"""

	uid: str
	paths: Sequence[str]
	frames: Sequence[ImageJson]


class Video:
	"""
	The `Video` class contains information about what Video was
	labeled by a given annotation. It also includes utilities
	for loading and manipulating Videos.
	"""

	uid: Optional[str]
	"""
	A unique ID for this Video.
	"""

	paths: Optional[Sequence[str]]
	"""
	A sequence of URIs where the media can be found. The loader
	will try them in order until it finds one it can load.

	Supported schemes include `http(s):`, `s3:`
	"""

	frames: Optional[Sequence[Image]]
	"""
	A sequence of images representing the video.
	"""

	@staticmethod
	def from_json(json: VideoJson) -> Video:
		"""
		Creates an `Video` from an `VideoJson`.
		"""
		return Video(
			uid = json.get("uid"),
			paths = json.get("paths"),
			frames = [Image.from_json(frame) for frame in json["frames"]] if "frames" in json else None
		)

	def __init__(
		self,
		*,
		uid: Optional[str] = None,
		paths: Optional[Sequence[str]] = None,
		frames: Optional[Sequence[Image]] = None
	):
		self.uid = uid
		self.paths = paths
		self.frames = frames

	def __repr__(self) -> str:
		return basic_repr("Video", uid = self.uid, paths = self.paths, frames = self.frames)

	def __eq__(self, other: object) -> bool:
		if not isinstance(other, Video):
			return NotImplemented
		return self.paths == other.paths

	def to_json(self) -> VideoJson:
		"""
		Serializes this `Video` into an `VideoJson`.
		"""
		json: VideoJson = {}

		if self.uid is not None:
			json["uid"] = self.uid

		if self.paths is not None:
			json["paths"] = self.paths

		if self.frames is not None:
			json["frames"] = [frame.to_json() for frame in self.frames]

		return json
