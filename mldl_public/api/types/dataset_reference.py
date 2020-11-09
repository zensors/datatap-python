from typing import List, Optional
from typing_extensions import TypedDict

from .dataset import JsonDataset

class JsonDatasetReference(TypedDict):
    database: str
    name: str
    dataset: Optional[JsonDataset]
    previousValues: List[str]

