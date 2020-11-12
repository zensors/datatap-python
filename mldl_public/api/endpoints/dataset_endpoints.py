from typing import Any, Dict, Generator, List

from .request import ApiNamespace
from ..types import JsonDatasetVersion, JsonDataset

class Dataset(ApiNamespace):
    def list(self, database_uid: str) -> List[JsonDataset]:
        return self.get[List[JsonDataset]](f"/database/{database_uid}/dataset")

    def query(self, database_uid: str, dataset_uid: str) -> JsonDatasetVersion:
        return self.get[JsonDatasetVersion](f"/database/{database_uid}/dataset/{dataset_uid}")

    def stream_split(self, database_uid: str, dataset_uid: str, split: str, chunk: int, nchunks: int) -> Generator[Dict[str, Any], None, None]:
        if chunk < 0 or chunk >= nchunks:
            raise Exception(f"Invalid chunk specification. {chunk} must be in the range [0, {nchunks})")

        yield from self.stream[Dict[str, Any]](
            f"/database/{database_uid}/dataset/{dataset_uid}/split/{split}/stream",
            { "chunk": str(chunk), "nchunks": str(nchunks) }
        )

