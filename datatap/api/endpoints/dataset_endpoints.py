from __future__ import annotations
from datatap.api.types.dataset import JsonDataset

import tempfile
import ctypes
from typing import Generator
from multiprocessing import Array, set_start_method

from datatap.droplet import ImageAnnotationJson
from datatap.utils import CacheGenerator

from .request import ApiNamespace

set_start_method("spawn", force = True)
process_directory_value = Array(ctypes.c_char, tempfile.mkdtemp(prefix="datatap-").encode("ascii"))
process_directory: str = process_directory_value.value.decode("ascii")

class Dataset(ApiNamespace):
    """
    Raw API for interacting with dataset endpoints.
    """

    def query(self, database_uid: str, namespace: str, name: str, tag: str) -> JsonDataset:
        """
        Queries the database for a dataset with given `namespace`, `name`, and `tag`.
        Returns a `JsonDataset`.
        """
        return self.get[JsonDataset](f"/database/{database_uid}/repository/{namespace}/{name}/{tag}")

    def stream_split(
        self,
        *,
        database_uid: str,
        namespace: str,
        name: str,
        uid: str,
        split: str,
        chunk: int,
        nchunks: int
    ) -> Generator[ImageAnnotationJson, None, None]:
        """
        Streams a split of a dataset. Required to stream are the `database_uid`, the full path of the daataset, and the
        `split`. Additionally, since this endpoint automatically shards the split, you must provide a chunk number
        (`chunk`) and the total number of chunks in the shard (`nchunks`).

        The result is a generator of `ImageAnnotationJson`s.
        """
        if chunk < 0 or chunk >= nchunks:
            raise Exception(f"Invalid chunk specification. {chunk} must be in the range [0, {nchunks})")

        dir_name = f"{process_directory}/{namespace}-{name}-{uid}-{split}-{nchunks}"
        file_name = f"{dir_name}/chunk-{chunk}.jsonl"

        def create_stream():
            return self.stream[ImageAnnotationJson](
                f"/database/{database_uid}/repository/{namespace}/{name}/{uid}/split/{split}/stream",
                { "chunk": str(chunk), "nchunks": str(nchunks) }
            )

        return CacheGenerator(file_name, create_stream)