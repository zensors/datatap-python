from __future__ import annotations

import sys
from io import BytesIO
from typing import Any, Optional, Sequence

import fsspec
import PIL.Image
from typing_extensions import TypedDict

from ..utils import basic_repr

class ImageJson(TypedDict):
	"""
	The serialized JSON representation of an `Image`.
	"""
	paths: Sequence[str]

class Image:
	"""
	The `Image` class contains information about what image was
	labeled by a given annotation. It also includes utilities
	for loading and manipulating images.
	"""

	paths: Sequence[str]
	"""
	A sequence of URIs where this image can be found. The loader
	will try them in order until it finds one it can load.

	Loading is performed by [fsspec](https://filesystem-spec.readthedocs.io/en/latest/api.html).

	Supported schemes include `http(s):`, `file:`, and `ftp:`, among others.
	Some protocols may require additional packages to be installed (such as
	`s3fs` for the `s3:` scheme).
	"""

	_pil_image: Optional[PIL.Image.Image]

	@staticmethod
	def from_json(json: ImageJson) -> Image:
		"""
		Creates an `Image` from an `ImageJson`.
		"""
		return Image(paths = json["paths"])

	@staticmethod
	def from_pil(pil_image: PIL.Image.Image) -> Image:
		"""
		Creates an `Image` from an existing PIL Image. Note that an
		image created this way will not have any `paths` set, but will
		still be able to load the image via `get_pil_image`.
		"""
		image = Image(
			paths = [],
		)
		image._pil_image = pil_image
		return image

	def __init__(self, *, paths: Sequence[str]):
		self.paths = paths
		self._pil_image = None

	def __repr__(self) -> str:
		return basic_repr("Image", paths = self.paths)

	def __eq__(self, other: Any) -> bool:
		if not isinstance(other, Image):
			return NotImplemented
		return self.paths == other.paths

	# TODO(mdsavage): consider using functools.cache here if we upgrade to Python >= 3.9
	def get_pil_image(self, quiet: bool = False, attempts: int = 3) -> PIL.Image.Image:
		"""
		Attempts to load the image specified by this reference. Resolution happpens in this order:

		1. Load from an internal cache (either from a previous load, or from `from_pil`)
		2. Try loading every path in order, returning once one loads

		Warning! `get_pil_image` may attempt to read from the local file system or from private
		networks. Please ensure that the annotation you are loading is trusted.
		"""
		if self._pil_image is not None:
			return self._pil_image

		for path in self.paths:
			for i in range(attempts):
				try:
					with fsspec.open(path) as f:
						pil_image = PIL.Image.open(BytesIO(f.read()))
						# self._pil_image = pil_image # TODO(mdsavage): figure out if/how we can reenable caching
						return pil_image
				except Exception as e:
					if not quiet:
						print(f"Cannot load image {path}, with error {str(e)}, attempt ({i + 1}/{attempts})", file = sys.stderr)

		raise FileNotFoundError("All paths for image failed to load", self.paths)

	def to_json(self) -> ImageJson:
		"""
		Serializes this `Image` into an `ImageJson`.
		"""
		return {
			"paths": self.paths
		}