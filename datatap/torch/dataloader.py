from __future__ import annotations

from os import cpu_count
from typing import Callable, Dict, Generator, Optional, TypeVar, cast, TYPE_CHECKING

import torch
import PIL.Image
import torchvision.transforms.functional as TF
from torch.utils.data import DataLoader as TorchDataLoader

from datatap.api.entities import Dataset

from .dataset import IterableDataset, DatasetBatch, collate

_T = TypeVar("_T")

if TYPE_CHECKING:
    class DataLoader(TorchDataLoader[_T]):
        """
        This is an ambient redeclaration of the dataloader class that
        has properly typed iter methods.
        """
        def __iter__(self) -> Generator[_T, None, None]: ...
else:
    DataLoader = TorchDataLoader

def create_dataloader(
    dataset: Dataset,
    split: str,
    batch_size: int = 1,
    num_workers: int = cpu_count() or 0,
    *,
    image_transform: Callable[[PIL.Image.Image], torch.Tensor] = TF.to_tensor,
    class_mapping: Optional[Dict[str, int]] = None,
    device: torch.device = torch.device("cpu")
) -> DataLoader[DatasetBatch]:
    """
    Creates a PyTorch `Dataloader` that yields batches of annotations.

    This `Dataloader` is using `datatap.torch.Dataset` under the hood, so
    all of the same restrictions apply, most notably that the `image_transform`
    function must ultimately return a `torch.Tensor` of dimensionality
    `(..., H, W)`.
    """
    if torch.multiprocessing.get_start_method(allow_none = True) is None:
        torch.multiprocessing.set_start_method("spawn")

    torch_dataset = IterableDataset(dataset, split, image_transform = image_transform, class_mapping = class_mapping, device = device)
    dataloader = cast(
        DataLoader[DatasetBatch],
        DataLoader(
            torch_dataset,
            batch_size,
            collate_fn = collate, # type: ignore (Torch's types are off)
            num_workers = num_workers,
        )
    )

    return dataloader
