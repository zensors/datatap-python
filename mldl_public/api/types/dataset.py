from typing import List, Dict, Any
from typing_extensions import TypedDict

class JsonDataset(TypedDict):
    name: str
    uid: str
    database: str
    splits: List[str]
    template: Dict[str, Any] # needs to be decoded by the annotation template class

