from __future__ import annotations

from typing import Any, Mapping, Optional, Sequence

import PIL.Image

from ..utils import basic_repr
from .camera_metadata import CameraMetadata


class Image:
	paths: Sequence[str]
	hash: Optional[str]
	camera_metadata: Optional[CameraMetadata]

	_pil_image: Optional[PIL.Image.Image]

	@staticmethod
	def from_json(json: Mapping[str, Any]):
		return Image(
			paths = json["paths"],
			hash = json.get("hash"),
			camera_metadata = CameraMetadata.from_json(json["cameraMetadata"]) if "cameraMetadata" in json else None
		)

	@staticmethod
	def from_pil(pil_image: PIL.Image.Image):
		image = Image(
			paths = [],
		)
		image._pil_image = pil_image
		return image

	def __init__(self, *, paths: Sequence[str], hash: Optional[str] = None, camera_metadata: Optional[CameraMetadata] = None):
		self.paths = paths
		self.hash = hash
		self.camera_metadata = camera_metadata
		# PIL Images aren't part of the standard API, so we require that you call [from_pil] to load them in
		self._pil_image = None

	def __repr__(self):
		return basic_repr("Image", paths = self.paths, hash = self.hash, camera_metadata = self.camera_metadata)

	def __eq__(self, other: Any):
		if not isinstance(other, Image):
			return NotImplemented
		return self.paths == other.paths and self.camera_metadata == other.camera_metadata

	def get_cached_image(self) -> Optional[PIL.Image.Image]:
		return self._pil_image
