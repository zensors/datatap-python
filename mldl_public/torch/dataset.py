from __future__ import annotations

from typing import Any, Callable, Dict, Generator, Generic, List, Optional, TypeVar, Union, overload

import torch
import PIL.Image
import torchvision.transforms.functional as TF
from torch.utils.data import IterableDataset as TorchIterableDataset, get_worker_info # type: ignore

from mldl_public.api.entities import DatasetVersion

_T = TypeVar("_T")

class DatasetElement(Generic[_T]):
    image: _T
    boxes: torch.Tensor
    labels: torch.Tensor

    def __init__(self, image: _T, boxes: torch.Tensor, labels: torch.Tensor):
        self.image = image
        self.boxes = boxes
        self.labels = labels

class DatasetBatch(Generic[_T]):
    images: List[_T]
    boxes: List[torch.Tensor]
    labels: List[torch.Tensor]

    def __init__(self, images: List[_T], boxes: List[torch.Tensor], labels: List[torch.Tensor]):
        self.images = images
        self.boxes = boxes
        self.labels = labels

@overload
def collate(elt: DatasetElement[_T]) -> DatasetBatch[_T]: ...
@overload
def collate(elt: List[DatasetElement[_T]]) -> DatasetBatch[_T]: ...
def collate(elt: Union[DatasetElement[_T], List[DatasetElement[_T]]]) -> DatasetBatch[_T]:
    if not isinstance(elt, List):
        elt = [elt]

    return DatasetBatch(
        [d.image for d in elt],
        [d.boxes for d in elt],
        [d.labels for d in elt],
    )

class IterableDataset(TorchIterableDataset[DatasetElement[_T]]):
    dataset: DatasetVersion
    split: str
    class_mapping: Dict[str, int]
    class_names: Dict[int, str]

    def __init__(
        self,
        dataset: DatasetVersion,
        split: str,
        class_mapping: Optional[Dict[str, int]] = None,
        image_transform: Callable[[PIL.Image.Image], _T] = TF.to_tensor,
    ):
        self.dataset = dataset
        self.split = split
        self.image_transform = image_transform

        template_classes = dataset.template.classes.keys()
        if class_mapping is not None:
            if set(class_mapping.keys()) != set(template_classes):
                raise Exception(
                    "Invalid class mapping. Provided classes ",
                    set(class_mapping.keys()),
                    " but needed ",
                    set(template_classes)
                )
            self.class_mapping = class_mapping
        else:
            self.class_mapping = {
                cls: i
                for i, cls in enumerate(sorted(template_classes))
            }

        self.class_names = {
            i: cls
            for cls, i in self.class_mapping.items()
        }

    def _get_generator(self):
        worker_info: Optional[Any] = get_worker_info()

        if worker_info is None:
            return self.dataset.stream_split(self.split, 0, 1)
        else:
            num_workers: int = worker_info.num_workers
            worker_id: int = worker_info.id

            return self.dataset.stream_split(self.split, worker_id, num_workers)

    def __iter__(self) -> Generator[DatasetElement[_T], None, None]:
        for annotation in self._get_generator():
            print(annotation.image)
            img = annotation.image.get_pil_image(True).convert("RGB")
            w, h = img.size

            instance_boxes = [
                (
                    instance.bounding_box.p1.x * w,
                    instance.bounding_box.p1.y * h,
                    instance.bounding_box.p2.x * w,
                    instance.bounding_box.p2.y * h,
                )
                for class_name in annotation.classes.keys()
                for instance in annotation.classes[class_name].instances
            ]

            instance_labels = [
                self.class_mapping[class_name]
                for class_name in annotation.classes.keys()
                for _ in annotation.classes[class_name].instances
            ]

            target = torch.tensor(instance_boxes).reshape((-1, 4))
            labels = torch.tensor(instance_labels, dtype = torch.int64)

            transformed_img = self.image_transform(img)
            element = DatasetElement(transformed_img, target, labels)

            yield element
