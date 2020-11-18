from __future__ import annotations
from typing import List

from mldl_public.utils import basic_repr

from .dataset import DatasetVersion, Dataset
from ..endpoints import ApiEndpoints
from ..types import JsonDatabase, JsonDatabaseOptions

class Database:
    """
    Represents a database. This database could either be the public database,
    or a user's private database that they have connected to the MLDL platform.

    This class provides utilites for viewing and updating the database's
    configuration, as well as inspecting its contents.
    """
    _endpoints: ApiEndpoints

    uid: str
    """
    The UID of this database.
    """

    name: str
    """
    The name of this database.
    """

    connection_options: JsonDatabaseOptions
    """
    How this database is configured. Sensitive details, such as database
    credentials, are omitted.
    """

    @staticmethod
    def from_json(endpoints: ApiEndpoints, json: JsonDatabase) -> Database:
        """
        Creates a `Database` from a `JsonDatabase`.
        """
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
        """
        Returns a list of all `Dataset`s that are stored in this database.
        """
        return [
            Dataset.from_json(self._endpoints, dataset_json)
            for dataset_json in self._endpoints.dataset.list(self.uid)
        ]

    def get_dataset_by_uid(self, dataset_uid: str) -> DatasetVersion:
        """
        Queries an individual `DatasetVersion` by UID.
        """
        return DatasetVersion.from_json(
            self._endpoints,
            self._endpoints.dataset.query(self.uid, dataset_uid)
        )

    def __repr__(self):
        return basic_repr("Database", self.uid, name = self.name)
