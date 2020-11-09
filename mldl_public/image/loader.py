import io
import sys

import boto3
import fsspec
import PIL.Image as Image

from mldl_public.droplet import ImageAnnotation

def get_s3_client():
	return boto3.resource("s3")

def load_image_from_annotation(annotation: ImageAnnotation, quiet: bool = False, retries: int = 2) -> Image.Image:
	cached_image = annotation.image.get_cached_image()
	if cached_image is not None:
		return cached_image

	paths = annotation.image.paths

	for path in paths:
		for i in range(retries):
			try:
				if path.startswith("s3://"):
					parts = path[5:].split("/")
					obj = get_s3_client().Object(parts[0], "/".join(parts[1:]))
					body = obj.get()["Body"]
					body.set_socket_timeout(10)
					image_data = io.BytesIO(body.read())
				else:
					with fsspec.open(path, "rb") as f:
						image_data = io.BytesIO(f.read())

				image = Image.open(image_data)
				return image

			except FileNotFoundError:
				print(f"Image at {path} not found, trying next path", file=sys.stderr)
				break

			except Exception as e:
				if not quiet and i < retries - 1:
					print(f"Cannot load image {path}, with error {str(e)}, retry ({i + 1}/{retries - 1})", file = sys.stderr)

	raise FileNotFoundError(f"Image cannot be loaded, all {len(paths)} candidate(s) failed")
