from __future__ import annotations
from datatap.api.types.dataset import JsonDataset

import json
import tempfile
import os
import time
import ctypes
from os import path
from typing import Generator, Optional
from threading import Thread, Semaphore
from queue import Queue
from multiprocessing import Array, set_start_method

from datatap.droplet import ImageAnnotationJson
from datatap.utils import DeletableGenerator

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
        tag: str,
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

        # TODO(zwade): change this to UID once we have an endpoint for fetching it
        dir_name = f"{process_directory}/{namespace}-{name}-{split}-{nchunks}"
        file_name = f"{dir_name}/chunk-{chunk}.jsonl"
        tmp_file_name = f"{file_name}.stream"
        os.makedirs(dir_name, exist_ok=True)

        EOF = "EOF"

        # Checks for an authoritative cache, using it if it exists.
        if path.exists(file_name):
            def cache_generator():
                with open(file_name, "r") as f:
                    for line in f.readlines():
                        line = line.strip()
                        if line == "" or line == EOF:
                            continue
                        yield json.loads(line)
                return
            return cache_generator()


        # `sync_queue` is used to synchronize startup and termination of the
        # subprocess, optionally propagating any errors that arise.
        sync_queue: Queue[Optional[Exception]] = Queue()

        # `available_annotations` counts how many lines have been written to
        # the stream file that have not yet been consumed.
        available_annotations = Semaphore()

        # `dead` is a flag that allows us to terminate our stream early
        dead = False

        def stream_target():
            stream = self.stream[ImageAnnotationJson](
                f"/database/{database_uid}/repository/{namespace}/{name}/{tag}/split/{split}/stream",
                { "chunk": str(chunk), "nchunks": str(nchunks) }
            )

            with open(tmp_file_name, "a+") as f:
                sync_queue.put(None)
                try:
                    for element in stream:
                        if dead:
                            raise Exception("Premature termination")

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

        thread = Thread(target = stream_target)
        thread.start()

        def generator():
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

                thread.join()

                error = sync_queue.get()
                if error is not None:
                    # This error came from the data loading subprocess
                    raise error

        def stop_processing():
            # This is a rather gross way of killing it, but unlike `Process`, `Thread`
            # has no `terminate` method.
            nonlocal dead
            dead = True

        return DeletableGenerator(generator(), stop_processing)
