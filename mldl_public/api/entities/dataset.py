from __future__ import annotations

from typing import List, Optional
from mldl_public.utils import basic_repr, OrNullish

from .dataset_version import DatasetVersion
from ..endpoints import ApiEndpoints
from ..types import JsonDataset

class Dataset:
    _endpoints: ApiEndpoints

    name: str
    database: str
    latest_version: Optional[DatasetVersion]
    previous_values: List[str]

    @staticmethod
    def from_json(endpoints: ApiEndpoints, json: JsonDataset) -> Dataset:
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
        return [
            DatasetVersion.from_json(self._endpoints, self._endpoints.dataset.query(self.database, dataset_uid))
            for dataset_uid in self.previous_values
        ]

    def __repr__(self) -> str:
        return basic_repr("Dataset", name = self.name, database = self.database, previous_values = self.previous_values, latest_version = self.latest_version)
