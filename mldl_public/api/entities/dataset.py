from typing import Generator, List, overload

from mldl_public.droplet import ImageAnnotation
from mldl_public.template import ImageAnnotationTemplate
from mldl_public.utils import basic_repr

from ..endpoints import ApiEndpoints
from ..types import JsonDataset

class Dataset:
    _endpoints: ApiEndpoints

    name: str
    uid: str
    database: str
    splits: List[str]
    template: ImageAnnotationTemplate

    @staticmethod
    def from_json(endpoints: ApiEndpoints, json: JsonDataset):
        return Dataset(
            endpoints,
            name = json["name"],
            uid = json["uid"],
            database = json["database"],
            splits = json["splits"],
            template = ImageAnnotationTemplate.from_json(json["template"])
        )

    def __init__(self, endpoints: ApiEndpoints, uid: str, *, name: str, database: str, splits: List[str], template: ImageAnnotationTemplate):
        self._endpoints = endpoints
        self.name = name
        self.uid = uid
        self.database = database
        self.splits = splits
        self.template = template

    @overload
    def stream_split(self, split: str) -> Generator[ImageAnnotation, None, None]: ...
    @overload
    def stream_split(self, split: str, chunk: int, nchunks: int) -> Generator[ImageAnnotation, None, None]: ...
    def stream_split(self, split: str, chunk: int = 0, nchunks: int = 1):
        for droplet in self._endpoints.dataset.stream_split(self.database, self.uid, split, chunk, nchunks):
            yield ImageAnnotation.from_json(droplet)


    def __repr__(self):
        return basic_repr("Dataset", self.uid, name = self.name, database = self.database, splits = self.splits)

