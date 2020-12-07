import json
import tempfile
import os
import time
from os import path
from typing import Generator, List, Optional
from multiprocessing import Process, Semaphore, Queue

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

        # We can't just naively stream from the server, unfortunately. Due to the sheer
        # volume of data, and the fact that training can be such a slow process, if we
        # try to stream the data directly from server to training process, we will end
        # up filling the OS' buffer, causing significant backpressure for the server.
        #
        # Likewise, we cannot necessarily stream from the server into a local buffer,
        # as a large dataset could be greater than our available RAM.
        #
        # As a result, this method streams data from the server to a temp file in a
        # subprocess. The main process then streams from that tempfile to the consumer
        # of the stream. Finally, once all data has been read, the main process stores
        # the stream file as an authoritative cache file for this particular stream.
        # Subsequent calls to this function with the same arguments will then pull from
        # that file.
        #
        # Please note that as a result of file-system accesses, streaming in this manner
        # incurs a non-trivial performance cost. For production training jobs, it is
        # recommended that this function be used with a data-loader capable of running
        # on multiple threads.

        dir_name = f"{process_directory}/{dataset_uid}-{split}-{nchunks}"
        file_name = f"{dir_name}/chunk-{chunk}.jsonl"
        tmp_file_name = f"{file_name}.stream"
        os.makedirs(dir_name, exist_ok=True)

        EOF = "EOF"

        # Checks for an authoritative cache, using it if it exists.
        if path.exists(file_name):
            with open(file_name, "r") as f:
                for line in f.readlines():
                    line = line.strip()
                    if line == "" or line == EOF:
                        continue
                    yield json.loads(line)
            return


        # `sync_queue` is used to synchronize startup and termination of the
        # subprocess, optionally propagating any errors that arise.
        sync_queue: Queue[Optional[Exception]] = Queue()

        # `available_annotations` counts how many lines have been written to
        # the stream file that have not yet been consumed.
        available_annotations = Semaphore()

        def stream_target():
            stream = self.stream[ImageAnnotationJson](
                f"/database/{database_uid}/dataset/{dataset_uid}/split/{split}/stream",
                { "chunk": str(chunk), "nchunks": str(nchunks) }
            )

            sync_queue.put(None)
            with open(tmp_file_name, "a+") as f:
                try:
                    for element in stream:
                        # We want to prioritize reading quickly, so after we write, we
                        # flush to the disk.
                        #
                        # (Note that we do not synchronize, as `fsync` incurs a 10x
                        # slowdown)
                        f.write(json.dumps(element) + "\n")
                        f.flush()
                        # We then "release" our semaphore to indicate that we've made a
                        # new asset available to the consumer
                        available_annotations.release()

                    sync_queue.put(None)
                except Exception as e:
                    sync_queue.put(e)
                finally:
                    # We explicitly write "EOF" at the end of the stream, since we
                    # otherwise would not be able to distinguish between the actual
                    # EOF and an incomplete write.
                    f.write(EOF + "\n")
                    f.flush()
                    available_annotations.release()

        proc = Process(target = stream_target)
        proc.start()

        sync_queue.get()
        with open(tmp_file_name, "r") as f:
            while True:
                available_annotations.acquire()

                line = ""
                c = 0
                while line == "" or line[-1] != "\n":
                    # Busy loop to wait for the file write.
                    #
                    # If we're eagerly fetching a large portion of the stream
                    # we may become bottlenecked by file synchronization. In
                    # this case, we implement a simple backoff to avoid
                    # unnecessarily hammering the file system.
                    line += f.readline()
                    c += 1
                    if c > 10:
                        time.sleep(0.005)

                data = line.strip()
                if data == EOF:
                    break

                yield json.loads(data)

            proc.join()

            error = sync_queue.get()
            if error is not None:
                # This error came from the data loading subprocess
                raise error
