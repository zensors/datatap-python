from typing import Iterable, NewType, Optional

DType = NewType("DType", str)

uint8: DType
int8: DType
int32: DType
int64: DType
float32: DType
float64: DType
string: DType

class TensorShape:
    dims: Optional[Iterable[int]]
    ndims: Optional[int]
    rank: Optional[int]

    def __init__(self, dims: Optional[Iterable[Optional[int]]]) -> TensorShape: ...