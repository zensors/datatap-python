from __future__ import annotations

import sys
from io import BytesIO
from typing import Sequence

try:
	import boto3
except ImportError:
	boto3 = None

try:
	import requests
except ImportError:
	requests = None

from ..utils import basic_repr

class Media:
	"""
	The `Media` class acts as a base class for all loadable media.
	"""

	paths: Sequence[str]
	"""
	A sequence of URIs where the media can be found. The loader
	will try them in order until it finds one it can load.

	Supported schemes include `http(s):`, `s3:`
	"""

	def __init__(self, *, paths: Sequence[str]):
		self.paths = paths

	def __repr__(self) -> str:
		return basic_repr("Media", paths = self.paths)

	def __eq__(self, other: object) -> bool:
		if not isinstance(other, Media):
			return NotImplemented
		return self.paths == other.paths

	def load(self, quiet: bool = False, attempts: int = 3, allow_local: bool = False) -> BytesIO:
		"""
		Attempts to load the Video file specified by this reference.
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
					elif scheme.lower() == "file" and allow_local:
						with open(file_name, "rb") as file_obj:
							data = file_obj.read()
					else:
						raise NotImplementedError(f"Unsupported scheme: {scheme}")

					return BytesIO(data)
				except Exception as e:
					if not quiet:
						print(f"Cannot load {type(self).__name__} {path}, with error {str(e)}, attempt ({i + 1}/{attempts})", file = sys.stderr)

		raise FileNotFoundError(f"All paths for {type(self).__name__} failed to load", self.paths)
