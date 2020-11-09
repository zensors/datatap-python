from typing import List

from .request import ApiNamespace
from ..types import JsonDatabase

class Database(ApiNamespace):
    def list(self):
        return self.get[List[JsonDatabase]]("/database")

    def query(self, database: str):
        return self.get[JsonDatabase](f"/database/{database}")