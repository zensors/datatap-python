from typing import List
from typing_extensions import TypedDict

class JsonSplit(TypedDict):
    split: str
    annotationCount: int

class JsonTag(TypedDict):
    tag: str
    dataset: str
    updatedAt: int
    splits: List[JsonSplit]

class JsonRepository(TypedDict):
    """
    The API type of a repository.
    """
    namespace: str
    name: str
    tags: List[JsonTag]

