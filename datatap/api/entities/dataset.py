from __future__ import annotations

from typing import List, Optional
from datatap.utils import basic_repr, OrNullish

from .dataset_version import DatasetVersion
from ..endpoints import ApiEndpoints
from ..types import JsonDataset

class Dataset:
    """
    Represents a dataset that has been created with a given template and options.

    If any versions of this dataset have been instantiated, then `latest_version`
    will refer to the most recent one. All others will be found in `previous_values`.
    """
    _endpoints: ApiEndpoints

    name: str
    """
    The name of this dataset.
    """

    database: str
    """
    The UID of the database in which this dataset lives.
    """

    latest_version: Optional[DatasetVersion]
    """
    The latest version of this dataset, or `None` if no versions exist.
    """

    previous_values: List[str]
    """
    If more than one `DatasetVersion` has been built for this dataset, then `previous_values`
    will hold the UIDs of all versions that are not the latest.
    """

    @staticmethod
    def from_json(endpoints: ApiEndpoints, json: JsonDataset) -> Dataset:
        """
        Creates a `Dataset` from a `JsonDataset`.
        """
        return Dataset(
            endpoints,
            name = json["name"],
            database = json["database"],
            latest_version = OrNullish.bind(json.get("dataset", None), lambda x: DatasetVersion.from_json(endpoints, x)),
            previous_values = json["previousValues"]
        )

    def __init__(self, endpoints: ApiEndpoints, *, name: str, database: str, latest_version: Optional[DatasetVersion], previous_values: List[str]):
        self._endpoints = endpoints
        self.name = name
        self.database = database
        self.latest_version = latest_version
        self.previous_values = previous_values

    def get_previous_datasets(self) -> List[DatasetVersion]:
        """
        Fetches all of the former dataset versions from the server.
        """
        return [
            DatasetVersion.from_json(self._endpoints, self._endpoints.dataset.query_by_uid(self.database, dataset_uid))
            for dataset_uid in self.previous_values
        ]

    def __repr__(self) -> str:
        return basic_repr("Dataset", name = self.name, database = self.database, previous_values = self.previous_values, latest_version = self.latest_version)
