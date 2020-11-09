from typing import Union
from typing_extensions import Literal, TypedDict

class JsonDatabaseOptionsDirect(TypedDict):
    kind: Literal["direct"]
    protocol: Union[Literal["neo4j"], Literal["neo4j+s"]]
    host: str
    port: int

JsonDatabaseOptions = Union[JsonDatabaseOptionsDirect]

class JsonDatabase(TypedDict):
    uid: str
    name: str
    connectionOptions: JsonDatabaseOptions

