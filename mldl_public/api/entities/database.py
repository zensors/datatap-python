from __future__ import annotations
from typing import List

from mldl_public.utils import basic_repr

from .dataset import DatasetVersion, Dataset
from ..endpoints import ApiEndpoints
from ..types import JsonDatabase, JsonDatabaseOptions

class Database:
    _endpoints: ApiEndpoints

    uid: str
    name: str
    connection_options: JsonDatabaseOptions

    @staticmethod
    def from_json(endpoints: ApiEndpoints, json: JsonDatabase) -> Database:
        return Database(
            endpoints,
            uid = json["uid"],
            name = json["name"],
            connection_options = json["connectionOptions"]
        )

    def __init__(self, endpoints: ApiEndpoints, uid: str, *, name: str, connection_options: JsonDatabaseOptions):
        self._endpoints = endpoints
        self.uid = uid
        self.name = name
        self.connection_options = connection_options

    def get_dataset_list(self) -> List[Dataset]:
        return [
            Dataset.from_json(self._endpoints, dataset_json)
            for dataset_json in self._endpoints.dataset.list(self.uid)
        ]

    def get_dataset_by_uid(self, dataset_uid: str) -> DatasetVersion:
        return DatasetVersion.from_json(
            self._endpoints,
            self._endpoints.dataset.query(self.uid, dataset_uid)
        )

    def __repr__(self):
        return basic_repr("Database", self.uid, name = self.name)
