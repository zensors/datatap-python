from __future__ import annotations

import sys
from io import BytesIO
from typing import Any, Mapping, Optional, Sequence

import fsspec
import PIL.Image

from ..utils import basic_repr
from .camera_metadata import CameraMetadata


class Image:
	paths: Sequence[str]
	hash: Optional[str]
	camera_metadata: Optional[CameraMetadata]

	_pil_image: Optional[PIL.Image.Image]

	@staticmethod
	def from_json(json: Mapping[str, Any]) -> Image:
		return Image(
			paths = json["paths"],
			hash = json.get("hash"),
			camera_metadata = CameraMetadata.from_json(json["cameraMetadata"]) if "cameraMetadata" in json else None
		)

	@staticmethod
	def from_pil(pil_image: PIL.Image.Image) -> Image:
		image = Image(
			paths = [],
		)
		image._pil_image = pil_image
		return image

	def __init__(self, *, paths: Sequence[str], hash: Optional[str] = None, camera_metadata: Optional[CameraMetadata] = None):
		self.paths = paths
		self.hash = hash
		self.camera_metadata = camera_metadata
		self._pil_image = None

	def __repr__(self) -> str:
		return basic_repr("Image", paths = self.paths, hash = self.hash, camera_metadata = self.camera_metadata)

	def __eq__(self, other: Any) -> bool:
		if not isinstance(other, Image):
			return NotImplemented
		return self.paths == other.paths and self.camera_metadata == other.camera_metadata

	# TODO(mdsavage): consider using functools.cache here if we upgrade to Python >= 3.9
	def get_pil_image(self, quiet: bool = False, attempts: int = 3) -> PIL.Image.Image:
		if self._pil_image is not None:
			return self._pil_image

		for path in self.paths:
			for i in range(attempts):
				try:
					with fsspec.open(path) as f:
						self._pil_image = PIL.Image.open(BytesIO(f.read()))
						return self._pil_image
				except Exception as e:
					if not quiet:
						print(f"Cannot load image {path}, with error {str(e)}, attempt ({i + 1}/{attempts})", file = sys.stderr)

		raise FileNotFoundError("All paths for image failed to load")
