from __future__ import annotations

import sys
from io import BytesIO
from typing import Optional, Sequence

import PIL.Image
from typing_extensions import TypedDict

try:
	import boto3
except ImportError:
	boto3 = None

try:
	import requests
except ImportError:
	requests = None

from ..utils import basic_repr

class _ImageJsonOptional(TypedDict, total = False):
	uid: str

class ImageJson(_ImageJsonOptional, TypedDict):
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

	uid: Optional[str]
	"""
	A unique ID for this image.
	"""

	paths: Sequence[str]
	"""
	A sequence of URIs where this image can be found. The loader
	will try them in order until it finds one it can load.

	Supported schemes include `http(s):`, `s3:`
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
		self.uid = uid
		self.paths = paths
		self._pil_image = None

	def __repr__(self) -> str:
		return basic_repr("Image", uid = self.uid, paths = self.paths)

	def __eq__(self, other: Image) -> bool:
		if not isinstance(other, Image): # type: ignore - pyright complains about the isinstance check being redundant
			return NotImplemented
		return self.paths == other.paths

	def load(self, quiet: bool = False, attempts: int = 3) -> BytesIO:
		"""
		Attempts to load the image file specified by this reference.
		Resolution happpens in this order:

		1. Load from an internal cache (either from a previous load, or from `from_pil`)
		2. Try loading every path in order, returning once one loads

		Warning! `load` may attempt to read from the local file system or from private
		networks. Please ensure that the annotation you are loading is trusted.
		"""
		for path in self.paths:
			for i in range(attempts):
				try:
					scheme, file_name, *_ = path.split(":")
					if scheme.lower() == "s3" and boto3 is not None:
						bucket_name, *path_components = [
							component
							for component in file_name.split("/")
							if component != ""
						]
						path_name = "/".join(path_components)

						s3 = boto3.resource("s3") # type: ignore
						file_obj = s3.Object(bucket_name, path_name) # type: ignore
						data: bytes = file_obj.get()["Body"].read() # type: ignore
					elif scheme.lower() in ["http", "https"] and requests is not None:
						response = requests.get(path)
						data = response.content
					else:
						raise NotImplementedError(f"Unsupported scheme: {scheme}")

					return BytesIO(data)
				except Exception as e:
					if not quiet:
						print(f"Cannot load image {path}, with error {str(e)}, attempt ({i + 1}/{attempts})", file = sys.stderr)

		raise FileNotFoundError("All paths for image failed to load", self.paths)

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

		return PIL.Image.open(self.load(quiet, attempts))

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
