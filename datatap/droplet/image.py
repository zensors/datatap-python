from __future__ import annotations

from typing import Optional, Sequence

import PIL.Image
from typing_extensions import TypedDict

from ..utils import basic_repr
from ._media import Media


class _ImageJsonOptional(TypedDict, total = False):
	uid: str

class ImageJson(_ImageJsonOptional, TypedDict):
	"""
	The serialized JSON representation of an `Image`.
	"""
	paths: Sequence[str]

class Image(Media):
	"""
	The `Image` class contains information about what image was
	labeled by a given annotation. It also includes utilities
	for loading and manipulating images.
	"""

	uid: Optional[str]
	"""
	A unique ID for this image.
	"""

	_pil_image: Optional[PIL.Image.Image]

	@staticmethod
	def from_json(json: ImageJson) -> Image:
		"""
		Creates an `Image` from an `ImageJson`.
		"""
		return Image(uid = json.get("uid", None), paths = json["paths"])

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

	def __init__(self, *, uid: Optional[str] = None, paths: Sequence[str]):
		super().__init__(paths = paths)
		self.uid = uid
		self._pil_image = None

	def __repr__(self) -> str:
		return basic_repr("Image", uid = self.uid, paths = self.paths)

	def __eq__(self, other: object) -> bool:
		if not isinstance(other, Image):
			return NotImplemented
		return self.paths == other.paths

	# TODO(mdsavage): consider using functools.cache here if we upgrade to Python >= 3.9
	def get_pil_image(self, quiet: bool = False, attempts: int = 3, allow_local: bool = False) -> PIL.Image.Image:
		"""
		Attempts to load the image specified by this reference. Resolution happpens in this order:

		1. Load from an internal cache (either from a previous load, or from `from_pil`)
		2. Try loading every path in order, returning once one loads

		Warning! `get_pil_image` may attempt to read from the local file system or from private
		networks. Please ensure that the annotation you are loading is trusted.
		"""
		if self._pil_image is not None:
			return self._pil_image

		return PIL.Image.open(self.load(quiet, attempts, allow_local))

	def to_json(self) -> ImageJson:
		"""
		Serializes this `Image` into an `ImageJson`.
		"""
		json: ImageJson = {
			"paths": self.paths
		}

		if self.uid is not None:
			json["uid"] = self.uid

		return json
