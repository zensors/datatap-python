from typing import Callable, Generator, Iterable, List, TypeVar, NewType

import tensorflow as tf

_T = TypeVar("_T")

DTypeDeepIterable = tf.DType | Iterable["DTypeDeepIterable"]
TensorShapeDeepIterable = tf.TensorShape | Iterable["TensorShapeDeepIterable"]

_V = TypeVar("_V")

class Dataset:
    @staticmethod
    def from_generator(
        gen: Callable[[_T], Generator[Iterable[tf.Tensor], None, None]] | Callable[[], Generator[Iterable[tf.Tensor], None, None]],
        output_type: DTypeDeepIterable = ...,
        output_shapes: TensorShapeDeepIterable = ...,
        args: _T = ...
    ) -> Dataset: ...

    def __iter__(self) -> Generator[Iterable[tf.Tensor], None, None]: ...

    def map(self, map_fn: Callable[..., Iterable[tf.Tensor]], num_parallel_calls: int = ..., deterministic: bool = ...) -> Dataset: ...
    def prefetch(self, buffer_size: int) -> Dataset: ...