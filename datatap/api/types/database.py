from typing import Union
from typing_extensions import Literal, TypedDict

class JsonDatabaseOptionsDirect(TypedDict):
    """
    Configuration options for a database that the server connects to directly.
    """
    kind: Literal["direct"]
    protocol: Union[Literal["neo4j"], Literal["neo4j+s"]]
    host: str
    port: int

JsonDatabaseOptions = Union[JsonDatabaseOptionsDirect]

class JsonDatabase(TypedDict):
    """
    The API type of a database.
    """
    uid: str
    name: str
    connectionOptions: JsonDatabaseOptions

