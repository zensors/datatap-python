from __future__ import annotations

from typing import Generator, List, overload

from datatap.droplet import ImageAnnotation
from datatap.template import ImageAnnotationTemplate
from datatap.utils import basic_repr

from ..endpoints import ApiEndpoints
from ..types import JsonDatasetVersion

class DatasetVersion:
    """
    Represents a concrete version of a dataset. Unlike `Dataset`s, which can update
    to refer to a new version, `DatasetVersion`s cannot be changed once they're created.

    For reproducable training, ensure that you store the specific `DatasetVersion` used
    during training.
    """
    _endpoints: ApiEndpoints

    uid: str
    """
    This UID of this `DatasetVersion`.
    """

    database: str
    """
    The UID of the database in which this dataset lives.
    """

    splits: List[str]
    """
    A list of all the splits that this `DatasetVersion` has. By default, this will be
    `["training", "validation"]`.
    """

    template: ImageAnnotationTemplate
    """
    The `ImageAnnotationTemplate` that all annotations in this dataset version adhere to.
    """

    @staticmethod
    def from_json(endpoints: ApiEndpoints, json: JsonDatasetVersion) -> DatasetVersion:
        """
        Creates a new `DatasetVersion` from a `JsonDatasetVersion`.
        """
        return DatasetVersion(
            endpoints,
            uid = json["uid"],
            database = json["database"],
            splits = json["splits"],
            template = ImageAnnotationTemplate.from_json(json["template"])
        )

    def __init__(self, endpoints: ApiEndpoints, uid: str, *, database: str, splits: List[str], template: ImageAnnotationTemplate):
        self._endpoints = endpoints
        self.uid = uid
        self.database = database
        self.splits = splits
        self.template = template

    @overload
    def stream_split(self, split: str) -> Generator[ImageAnnotation, None, None]: ...
    @overload
    def stream_split(self, split: str, chunk: int, nchunks: int) -> Generator[ImageAnnotation, None, None]: ...
    def stream_split(self, split: str, chunk: int = 0, nchunks: int = 1) -> Generator[ImageAnnotation, None, None]:
        """
        Streams a specific split of this dataset from the database. All yielded annotations will be of type
        `ImageAnnotation` and adhere to this dataset version's annotation template.

        If `chunk` and `nchunks` are omitted, then the full split will be streamed. Otherwise, the split will be
        broken into `nchunks` pieces, and only the chunk identified by `chunk` will be streamed.
        """
        for droplet in self._endpoints.dataset.stream_split(self.database, self.uid, split, chunk, nchunks):
            yield ImageAnnotation.from_json(droplet)


    def __repr__(self) -> str:
        return basic_repr("DatasetVersion", self.uid, database = self.database, splits = self.splits)

