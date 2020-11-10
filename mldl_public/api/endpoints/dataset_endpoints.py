from typing import Any, Dict, List

from .request import ApiNamespace
from ..types import JsonDatasetReference, JsonDataset

class Dataset(ApiNamespace):
    def list(self, database_uid: str):
        return self.get[List[JsonDatasetReference]](f"/database/{database_uid}/dataset")

    def query(self, database_uid: str, dataset_uid: str):
        return self.get[JsonDataset](f"/database/{database_uid}/dataset/{dataset_uid}")

    def stream_split(self, database_uid: str, dataset_uid: str, split: str, chunk: int, nchunks: int):
        if chunk < 0 or chunk >= nchunks:
            raise Exception(f"Invalid chunk specification. {chunk} must be in the range [0, {nchunks})")

        yield from self.stream[Dict[str, Any]](
            f"/database/{database_uid}/dataset/{dataset_uid}/split/{split}/stream",
            { "chunk": str(chunk), "nchunks": str(nchunks) }
        )
