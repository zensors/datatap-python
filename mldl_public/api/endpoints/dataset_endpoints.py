import random
import json
import tempfile
from os import path, makedirs
from typing import Any, Dict, Generator, List

from .request import ApiNamespace
from ..types import JsonDatasetVersion, JsonDataset

process_directory = tempfile.mkdtemp(prefix="mldl-")

class Dataset(ApiNamespace):
    def list(self, database_uid: str) -> List[JsonDataset]:
        return self.get[List[JsonDataset]](f"/database/{database_uid}/dataset")

    def query(self, database_uid: str, dataset_uid: str) -> JsonDatasetVersion:
        return self.get[JsonDatasetVersion](f"/database/{database_uid}/dataset/{dataset_uid}")

    def stream_split(self, database_uid: str, dataset_uid: str, split: str, chunk: int, nchunks: int) -> Generator[Dict[str, Any], None, None]:
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
                yield element
