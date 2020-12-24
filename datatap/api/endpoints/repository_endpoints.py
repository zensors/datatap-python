from __future__ import annotations

from typing import List
from .request import ApiNamespace
from ..types import JsonRepository

class Repository(ApiNamespace):
    """
    Raw API for interacting with repository endpoints.
    """
    def list(self, database_uid: str) -> List[JsonRepository]:
        """
        Returns a list of `JsonRepository`s in the database specified by `database_uid`.
        """
        return self.get[List[JsonRepository]](f"/database/{database_uid}/repository")

    def query(self, database_uid: str, namespace: str, name: str) -> JsonRepository:
        """
        Queries the database for the repository with a given `namespace` and `name`, and
        returns the corresponding `JsonRepository` list.
        """
        return self.get[JsonRepository](f"/database/{database_uid}/repository/{namespace}/{name}")
