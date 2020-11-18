from typing import List

from .request import ApiNamespace
from ..types import JsonDatabase

class Database(ApiNamespace):
    """
    Raw API for interacting with database endpoints.
    """
    def list(self) -> List[JsonDatabase]:
        """
        Returns a list of `JsonDatabase`s that the current user has access to.
        """
        return self.get[List[JsonDatabase]]("/database")

    def query(self, database: str) -> JsonDatabase:
        """
        Returns a specific `JsonDatabase`, identified by UID.
        """
        return self.get[JsonDatabase](f"/database/{database}")