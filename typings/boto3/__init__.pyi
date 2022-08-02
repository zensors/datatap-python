from io import BytesIO
from typing import Literal, TypedDict


class S3Resource:
	def Object(self, bucket_name: str, path_name: str) -> S3Object: ...

class S3Object:
	def get(self) -> S3ObjectDict: ...

class S3ObjectDict(TypedDict):
	Body: BytesIO

def resource(type: Literal["s3"]) -> S3Resource: ...
