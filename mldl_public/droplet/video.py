from __future__ import annotations

from typing import Any, Mapping, Optional, Sequence

from ..utils import basic_repr
from .camera_metadata import CameraMetadata


class Video:
	paths: Sequence[str]
	hash: Optional[str]
	name: Optional[str]
	camera_metadata: Optional[CameraMetadata]

	@staticmethod
	def from_json(json: Mapping[str, Any]):
		return Video(
			paths = json["paths"],
			hash = json.get("hash"),
			name = json.get("name")
		)

	def __init__(
		self,
		*,
		paths: Sequence[str],
		hash: Optional[str] = None,
		name: Optional[str] = None,
		camera_metadata: Optional[CameraMetadata] = None
	):
		self.paths = paths
		self.name = name
		self.hash = hash
		self.name = name
		self.camera_metadata = camera_metadata

	def __repr__(self):
		return basic_repr(
			"Video",
			paths = self.paths,
			hash = self.hash,
			name = self.name,
			camera_metadata = self.camera_metadata
		)
