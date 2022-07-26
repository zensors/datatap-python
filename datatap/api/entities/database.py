from __future__ import annotations
from datatap.api.entities.dataset import AnyDataset
from typing import Any, List, overload

from datatap.utils import basic_repr

from .repository import Repository
from ..endpoints import ApiEndpoints
from ..types import JsonDatabase, JsonDatabaseOptions

class Database:
    """
    Represents a database. This database could either be the public database,
    or a user's private database that they have connected to the dataTap
    platform.

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

    def get_repository_list(self) -> List[Repository]:
        """
        Returns a list of all `Repository`s that are stored in this database.
        """
        return [
            Repository.from_json(self._endpoints, self.uid, repository_json)
            for repository_json in self._endpoints.repository.list(self.uid)
        ]


    @overload
    def get_repository(self, slug: str) -> Repository: ...
    @overload
    def get_repository(self, namespace: str, name: str) -> Repository: ...
    def get_repository(self, *args: str, **kwargs: Any) -> Repository:
        """
        Queries a `Repository` by its namespace and name, or via its slug (namespace/name).
        """
        if len(kwargs) > 0:
            raise ValueError("get_repository is positional-only")
        elif len(args) == 1:
            namespace, name = args[0].split("/")
        else:
            namespace, name = args

        return Repository.from_json(self._endpoints, self.uid, self._endpoints.repository.query(self.uid, namespace, name))

    @overload
    def get_dataset(self, slug: str) -> AnyDataset: ...
    @overload
    def get_dataset(self, namespace: str, name: str, tag: str) -> AnyDataset: ...
    def get_dataset(self, *args: str, **kwargs: Any) -> AnyDataset:
        """
        Queries a `Dataset` by its namespace, name, and tag, or via its slug (namespace/name:tag).
        """
        if len(kwargs) > 0:
            raise ValueError("get_repository is positional-only")
        elif len(args) == 1:
            repo_slug, tag = args[0].split(":")
            repo = self.get_repository(repo_slug)
        else:
            namespace, name, tag = args
            repo = self.get_repository(namespace, name)

        return repo.get_dataset(tag)

    def __repr__(self):
        return basic_repr("Database", self.uid, name = self.name)
