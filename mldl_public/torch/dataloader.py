from __future__ import annotations

from os import cpu_count
from typing import Callable, Dict, Generator, Optional, TypeVar, cast, TYPE_CHECKING

import PIL.Image
import torchvision.transforms.functional as TF
from torch.utils.data import DataLoader as TorchDataLoader

from mldl_public.api.entities import DatasetVersion

from .dataset import IterableDataset, DatasetBatch, collate

_T = TypeVar("_T")

if TYPE_CHECKING:
    class DataLoader(TorchDataLoader[_T]):
        """
        This is an ambient redeclaration of the dataloader class that
        has properly typed iter methods
        """
        def __iter__(self) -> Generator[_T, None, None]: ...
else:
    DataLoader = TorchDataLoader

def batched_dataloader(
    version: DatasetVersion,
    split: str,
    batch_size: int = 1,
    num_workers: int = cpu_count() or 0,
    *,
    image_transform: Callable[[PIL.Image.Image], _T] = TF.to_tensor,
    class_mapping: Optional[Dict[str, int]] = None,
) -> DataLoader[DatasetBatch[_T]]:

    dataset = IterableDataset(version, split, image_transform = image_transform, class_mapping = class_mapping)
    dataloader = cast(
        DataLoader[DatasetBatch[_T]],
        DataLoader(
            dataset,
            batch_size,
            collate_fn=collate,
            num_workers=num_workers,
        )
    )

    return dataloader
