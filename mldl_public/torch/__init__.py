import functools
from typing import Any, Type, TypeVar

from torch.utils.data import IterableDataset, DataLoader

_T = TypeVar("_T")

def allow_generic(cls: Type[_T], type: Any) -> Type[_T]:
    """
    This function is can be monkey patched onto any type to allow it
    to support generics (i.e. Cls[T])

    If you are running into any issues with it, please file a bug
    report with dev@zensors.com
    """
    return cls

def patch_generic_class(cls: Type[Any]):
    setattr(cls, "__class_getitem__", functools.partial(allow_generic, cls))


patch_generic_class(IterableDataset)
patch_generic_class(DataLoader)

