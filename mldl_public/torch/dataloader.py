from os import cpu_count
from typing import Callable, TypeVar, cast

import PIL.Image
import torchvision.transforms.functional as TF
from torch.utils.data import DataLoader

from mldl_public.api.entities import DatasetVersion

from .dataset import IterableDataset, DatasetBatch, collate

_T = TypeVar("_T")

def batched_dataloader(
    version: DatasetVersion,
    split: str,
    batch_size: int = 1,
    num_workers: int = cpu_count() or 0,
    *,
    image_transform: Callable[[PIL.Image.Image], _T] = TF.to_tensor,
) -> DataLoader[DatasetBatch[_T]]:

    dataset = IterableDataset(version, split, image_transform=image_transform)
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
