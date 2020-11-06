from typing import Union, List
from typing_extensions import Literal, TypedDict

from .request import ApiNamespace

class ApiDatabaseOptionsDirect(TypedDict):
    kind: Literal["direct"]
    protocol: Union[Literal["neo4j"], Literal["neo4j+s"]]
    host: str
    port: int

class ApiDatabase(TypedDict):
    uid: str
    name: str
    connectionOptions: Union[ApiDatabaseOptionsDirect]

class Database(ApiNamespace):
    def list(self):
        return self.get[List[ApiDatabase]]("/database")

    def query(self, database: str):
        return self.get[ApiDatabase](f"/database/{database}")