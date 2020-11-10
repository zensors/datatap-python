from typing import List

from .request import ApiNamespace
from ..types import JsonDatabase

class Database(ApiNamespace):
    def list(self) -> List[JsonDatabase]:
        return self.get[List[JsonDatabase]]("/database")

    def query(self, database: str) -> JsonDatabase:
        return self.get[JsonDatabase](f"/database/{database}")