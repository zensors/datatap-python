from typing import Generator, Iterable

import tensorflow as tf

class DistributedDataset:

    def __iter__(self) -> Generator[Iterable[tf.Tensor], None, None]: ...