from mldl.utils import basic_repr

from .dataset_reference import DatasetReference, Dataset
from ..endpoints import ApiEndpoints
from ..types import JsonDatabase, JsonDatabaseOptions

class Database:
    _endpoints: ApiEndpoints

    uid: str
    name: str
    connection_options: JsonDatabaseOptions

    @staticmethod
    def from_json(endpoints: ApiEndpoints, json: JsonDatabase):
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

    def get_dataset_list(self):
        return [
            DatasetReference.from_json(self._endpoints, dataset_json)
            for dataset_json in self._endpoints.dataset.list(self.uid)
        ]

    def get_dataset_by_uid(self, dataset_uid: str):
        return Dataset.from_json(
            self._endpoints,
            self._endpoints.dataset.query(self.uid, dataset_uid)
        )

    def __repr__(self):
        return basic_repr("Database", self.uid, name = self.name)
