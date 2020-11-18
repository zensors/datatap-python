from typing import List, Optional
from typing_extensions import TypedDict

from .dataset_version import JsonDatasetVersion

class JsonDataset(TypedDict):
    """
    The API type of a dataset.
    """
    database: str
    name: str
    dataset: Optional[JsonDatasetVersion]
    previousValues: List[str]

