from __future__ import annotations
from datatap.api.types.dataset import JsonDatasetRepository

from typing import Generator, Generic, List, TypeVar, Union, overload

from datatap.droplet import ImageAnnotation, VideoAnnotation
from datatap.template import ImageAnnotationTemplate, VideoAnnotationTemplate
from datatap.utils import basic_repr

from ..endpoints import ApiEndpoints
from ..types import JsonDataset

T = TypeVar("T", ImageAnnotationTemplate, VideoAnnotationTemplate)

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

class Dataset(Generic[T]):
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

    template: T
    """
    The template that all annotations in this dataset version adhere to.
    """

    @staticmethod
    def from_json(endpoints: ApiEndpoints, json: JsonDataset) -> AnyDataset:
        """
        Creates a new `Dataset` from a `JsonDataset`.
        """
        template_json = json["template"]
        template: Union[ImageAnnotationTemplate, VideoAnnotationTemplate]

        if template_json["kind"] == "ImageAnnotationTemplate":
            template = ImageAnnotationTemplate.from_json(template_json)
        elif template_json["kind"] == "VideoAnnotationTemplate":
            template = VideoAnnotationTemplate.from_json(template_json)
        else:
            raise ValueError(f"Unknown template kind: {template_json['kind']}")

        return Dataset(
            endpoints,
            uid = json["uid"],
            database = json["database"],
            repository = DatasetRepository.from_json(json["repository"]),
            splits = json["splits"],
            template = template
        )

    def __init__(
        self,
        endpoints: ApiEndpoints,
        uid: str,
        *,
        database: str,
        repository: DatasetRepository,
        splits: List[str],
        template: Union[ImageAnnotationTemplate, VideoAnnotationTemplate]
    ):
        self._endpoints = endpoints
        self.uid = uid
        self.database = database
        self.repository = repository
        self.splits = splits
        self.template = template

    @overload
    def stream_split(
        self: Dataset[ImageAnnotationTemplate],
        split: str
    ) -> Generator[ImageAnnotation, None, None]: ...
    @overload
    def stream_split(
        self: Dataset[ImageAnnotationTemplate],
        split: str,
        chunk: int,
        nchunks: int
    ) -> Generator[ImageAnnotation, None, None]: ...
    @overload
    def stream_split(
        self: Dataset[VideoAnnotationTemplate],
        split: str
    ) -> Generator[VideoAnnotation, None, None]: ...
    @overload
    def stream_split(
        self: Dataset[VideoAnnotationTemplate],
        split: str,
        chunk: int,
        nchunks: int
    ) -> Generator[VideoAnnotation, None, None]: ...
    def stream_split(
        self,
        split: str,
        chunk: int = 0,
        nchunks: int = 1
    ) -> Generator[Union[ImageAnnotation, VideoAnnotation], None, None]:
        """
        Streams a specific split of this dataset from the database. All yielded annotations will adhere to this
        dataset's annotation template.

        If `chunk` and `nchunks` are omitted, then the full split will be streamed. Otherwise, the split will be
        broken into `nchunks` pieces, and only the chunk identified by `chunk` will be streamed.
        """
        for droplet in self._endpoints.dataset.stream_split(
            database_uid = self.database,
            namespace = self.repository.namespace,
            name = self.repository.name,
            uid = self.uid,
            split = split,
            chunk = chunk,
            nchunks = nchunks,
        ):
            if isinstance(self.template, ImageAnnotationTemplate):
                yield ImageAnnotation.from_json(droplet)
            elif isinstance(self.template, VideoAnnotationTemplate): # type: ignore - isinstance is excessive
                yield VideoAnnotation.from_json(droplet)
            else:
                raise ValueError(f"Unknown template kind: {type(self.template)}")

    def get_stable_identifier(self) -> str:
        return f"{self.repository.namespace}/{self.repository.name}:{self.uid}"

    def __repr__(self) -> str:
        return basic_repr(
            "Dataset",
            self.get_stable_identifier(),
            database = self.database,
            splits = self.splits
        )

AnyDataset = Union[Dataset[ImageAnnotationTemplate], Dataset[VideoAnnotationTemplate]]
