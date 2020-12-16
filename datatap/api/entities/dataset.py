from __future__ import annotations
from datatap.api.types.dataset import JsonDatasetRepository

from typing import Generator, List, overload

from datatap.droplet import ImageAnnotation
from datatap.template import ImageAnnotationTemplate
from datatap.utils import basic_repr

from ..endpoints import ApiEndpoints
from ..types import JsonDataset

class DatasetRepository:
    """
    An object representing the repository a dataset came from.
    """

    name: str
    """
    The name of the repository.
    """

    namespace: str
    """
    The namespace of the repository.
    """

    @staticmethod
    def from_json(json: JsonDatasetRepository) -> DatasetRepository:
        """
        Creates a new `DatasetRepository` from a `JsonDatasetRepository`.
        """
        return DatasetRepository(name = json["name"], namespace = json["namespace"])

    def __init__(self, *, name: str, namespace: str):
        self.name = name
        self.namespace = namespace

class Dataset:
    """
    Represents a concrete version of a dataset. Critically, `Dataset`s cannot be changed
    once they're created.

    For reproducable training, ensure that you store the specific `Dataset` used
    during training.
    """
    _endpoints: ApiEndpoints

    uid: str
    """
    The UID of this `Dataset`.
    """

    database: str
    """
    The UID of the database in which this dataset lives.
    """

    repository: DatasetRepository
    """
    The repository this dataset belongs to.
    """

    splits: List[str]
    """
    A list of all the splits that this dataset has. By default, this will be
    `["training", "validation"]`.
    """

    template: ImageAnnotationTemplate
    """
    The `ImageAnnotationTemplate` that all annotations in this dataset version adhere to.
    """

    @staticmethod
    def from_json(endpoints: ApiEndpoints, json: JsonDataset) -> Dataset:
        """
        Creates a new `Dataset` from a `JsonDataset`.
        """
        return Dataset(
            endpoints,
            uid = json["uid"],
            database = json["database"],
            repository = DatasetRepository.from_json(json["repository"]),
            splits = json["splits"],
            template = ImageAnnotationTemplate.from_json(json["template"])
        )

    def __init__(
        self,
        endpoints: ApiEndpoints,
        uid: str,
        *,
        database: str,
        repository: DatasetRepository,
        splits: List[str],
        template: ImageAnnotationTemplate
    ):
        self._endpoints = endpoints
        self.uid = uid
        self.database = database
        self.repository = repository
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
        for droplet in self._endpoints.dataset.stream_split(
            database_uid = self.database,
            namespace = self.repository.namespace,
            name = self.repository.name,
            tag = self.uid,
            split = split,
            chunk = chunk,
            nchunks = nchunks,
        ):
            yield ImageAnnotation.from_json(droplet)


    def __repr__(self) -> str:
        return basic_repr("Dataset", self.uid, database = self.database, splits = self.splits)

