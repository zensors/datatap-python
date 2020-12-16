from __future__ import annotations

from datetime import datetime
from typing import Sequence

from datatap.utils import basic_repr

from .dataset import Dataset
from ..types import JsonRepository, JsonSplit, JsonTag
from ..endpoints import ApiEndpoints

class Split:
    """
    Represents the splits available for a given dataset.
    """

    split: str
    """
    The kind of the split (e.g, "training" or "validation").
    """

    annotation_count: int
    """
    The number of annotations available in this split.
    """

    @staticmethod
    def from_json(json: JsonSplit) -> Split:
        """
        Creates a `Split` from a `JsonSplit`
        """
        return Split(json["split"], json["annotationCount"])

    def __init__(self, split: str, annotation_count: int):
        self.split = split
        self.annotation_count = annotation_count

    def __repr__(self) -> str:
        return basic_repr("Split", self.split, annotation_count = self.annotation_count)

class Tag:
    """
    Represents a single tag that may be accessed in this repository.
    """

    tag: str
    """
    A slug representing this tag (such as "latest").
    """

    dataset: str
    """
    The uid of the dataset to which this tag points.
    """

    updated_at: datetime
    """
    When this tag was most recently updated.
    """

    splits: Sequence[Split]
    """
    A list of splits available on this tag.
    """

    @staticmethod
    def from_json(json: JsonTag) -> Tag:
        """
        Creates a `Tag` from a `JsonTag`.
        """
        return Tag(
            json["tag"],
            json["dataset"],
            datetime.fromtimestamp(json["updatedAt"] / 1000),
            [Split.from_json(split) for split in json["splits"]]
        )

    def __init__(self, tag: str, dataset: str, updated_at: datetime, splits: Sequence[Split]):
        self.tag = tag
        self.dataset = dataset
        self.updated_at = updated_at
        self.splits = splits

    def __repr__(self) -> str:
        return basic_repr("Tag", self.tag, dataset = self.dataset, splits = self.splits)

class Repository:
    """
    Represents a repository that contains one or more datasets.
    """
    _endpoints: ApiEndpoints
    _database: str

    name: str
    """
    The name of this repository.
    """

    namespace: str
    """
    The namespace of this repository.
    """

    tags: Sequence[Tag]
    """
    The tags available for this repository.
    """

    @staticmethod
    def from_json(endpoints: ApiEndpoints, database: str, json: JsonRepository) -> Repository:
        """
        Creates a `Dataset` from a `JsonDataset`.
        """
        return Repository(
            endpoints,
            database,
            name = json["name"],
            namespace = json["namespace"],
            tags = [Tag.from_json(tag) for tag in json["tags"]],
        )

    def __init__(self, endpoints: ApiEndpoints, database: str, *, name: str, namespace: str, tags: Sequence[Tag]):
        self._endpoints = endpoints
        self._database = database
        self.name = name
        self.namespace = namespace
        self.tags = tags

    def get_dataset(self, tag: str) -> Dataset:
        """
        Fetches dataset by its tag (or UID).
        """
        return Dataset.from_json(
            self._endpoints,
            self._endpoints.dataset.query(self._database, self.namespace, self.name, tag)
        )

    def __repr__(self) -> str:
        return basic_repr("Repository", name = self.name, namespace = self.namespace, tags = [tag.tag for tag in self.tags])
