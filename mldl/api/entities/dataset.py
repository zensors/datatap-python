from typing import Generator, List, overload

from mldl.droplet import Annotation
from mldl.template import AnnotationTemplate
from mldl.utils import basic_repr

from ..endpoints import ApiEndpoints
from ..types import JsonDataset

class Dataset:
    _endpoints: ApiEndpoints

    name: str
    uid: str
    database: str
    splits: List[str]
    template: AnnotationTemplate

    @staticmethod
    def from_json(endpoints: ApiEndpoints, json: JsonDataset):
        return Dataset(
            endpoints,
            name = json["name"],
            uid = json["uid"],
            database = json["database"],
            splits = json["splits"],
            template = AnnotationTemplate.from_json(json["template"])
        )

    def __init__(self, endpoints: ApiEndpoints, uid: str, *, name: str, database: str, splits: List[str], template: AnnotationTemplate):
        self._endpoints = endpoints
        self.name = name
        self.uid = uid
        self.database = database
        self.splits = splits
        self.template = template

    @overload
    def stream_split(self, split: str) -> Generator[Annotation, None, None]: ...
    @overload
    def stream_split(self, split: str, chunk: int, nchunks: int) -> Generator[Annotation, None, None]: ...
    def stream_split(self, split: str, chunk: int = 0, nchunks: int = 1):
        return self._endpoints.dataset.stream_split(self.database, self.uid, split, chunk, nchunks)


    def __repr__(self):
        return basic_repr("Dataset", self.uid, name = self.name, database = self.database, splits = self.splits)

