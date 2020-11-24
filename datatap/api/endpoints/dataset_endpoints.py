import json
import tempfile
from os import path, makedirs
from typing import Any, Dict, Generator, List, cast

from datatap.droplet import ImageAnnotationJson

from .request import ApiNamespace
from ..types import JsonDatasetVersion, JsonDataset

process_directory = tempfile.mkdtemp(prefix="datatap-")

class Dataset(ApiNamespace):
    """
    Raw API for interacting with dataset endpoints.
    """
    def list(self, database_uid: str) -> List[JsonDataset]:
        """
        Returns a list of `JsonDataset`s in the database specified by `database_uid`.
        """
        return self.get[List[JsonDataset]](f"/database/{database_uid}/dataset")

    def query(self, database_uid: str, dataset_uid: str) -> JsonDatasetVersion:
        """
        Queries a specific `JsonDatasetVersion` by its uid and its database's UID.
        """
        return self.get[JsonDatasetVersion](f"/database/{database_uid}/dataset/{dataset_uid}")

    def stream_split(self, database_uid: str, dataset_uid: str, split: str, chunk: int, nchunks: int) -> Generator[ImageAnnotationJson, None, None]:
        """
        Streams a split of a dataset. Required to stream are the `database_uid`, the `dataset_uid`, and the `split`.
        Additionally, since this endpoint automatically shards the split, you must provide a chunk number (`chunk`)
        and the total number of chunks in the shard (`nchunks`).

        The result is a generator of `ImageAnnotationJson`s.
        """
        if chunk < 0 or chunk >= nchunks:
            raise Exception(f"Invalid chunk specification. {chunk} must be in the range [0, {nchunks})")

        dir_name = f"{process_directory}/{dataset_uid}-{split}-{nchunks}"
        file_name = f"{dir_name}/chunk-{chunk}.jsonl"
        makedirs(dir_name, exist_ok=True)

        if path.exists(file_name):
            with open(file_name, "r") as f:
                for line in f.readlines():
                    line = line.strip()
                    if line == "":
                        continue
                    yield json.loads(line)
            return

        stream = self.stream[Dict[str, Any]](
            f"/database/{database_uid}/dataset/{dataset_uid}/split/{split}/stream",
            { "chunk": str(chunk), "nchunks": str(nchunks) }
        )

        with open(file_name, "w+") as f:
            for element in stream:
                f.write(json.dumps(element))
                f.write("\n")
                yield cast(ImageAnnotationJson, element)
