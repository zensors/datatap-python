from typing import Any, Dict, List

from .request import ApiNamespace

class ApiDataset:
    name: str
    uid: str
    database: str
    databaseSplits: List[str]
    template: Dict[str, Any] # needs to be decoded by the annotation template class

class ApiDatasetReference:
    database: str
    name: str
    dataset: ApiDataset
    previousValues: List[str]

class Dataset(ApiNamespace):
    def list(self, database_uid: str):
        return self.get[List[ApiDatasetReference]](f"/database/{database_uid}/dataset")

    def stream_split(self, database_uid: str, dataset_uid: str, split: str, chunk: int, nchunks: int):
        if chunk < 0 or chunk >= nchunks:
            raise Exception(f"Invalid chunk specification. {chunk} must be in the range [0, {nchunks})")

        yield from self.stream[Dict[str, Any]](
            f"/database/{database_uid}/dataset/{dataset_uid}/split/{split}/stream",
            { "chunk": str(chunk), "nchunks": str(nchunks) }
        )

