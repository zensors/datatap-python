from typing import List, Dict, Any
from typing_extensions import TypedDict

class JsonDatasetVersion(TypedDict):
    """
    The API type of a dataset version.
    """
    name: str
    uid: str
    database: str
    splits: List[str]
    template: Dict[str, Any] # needs to be decoded by the annotation template class

