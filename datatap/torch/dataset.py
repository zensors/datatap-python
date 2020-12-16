from __future__ import annotations

from typing import Any, Callable, Dict, Generator, List, Optional, Union, overload

import torch
import PIL.Image
import torchvision.transforms.functional as TF
from torch.utils.data import IterableDataset as TorchIterableDataset, get_worker_info # type: ignore

from datatap.droplet import ImageAnnotation
from datatap.api.entities import Dataset

class DatasetElement():
    """
    Represents a single element from the dataset.
    """

    original_annotation: ImageAnnotation
    """
    The original, untransformed annotation.
    """

    image: torch.Tensor
    """
    The image as transformed by the dataset.
    """

    boxes: torch.Tensor
    """
    The bounding boxes. They are specified in xyxy format `(min-x, min-y, max-x, max-y)`.
    """

    labels: torch.Tensor
    """
    The labels. They are a tensor of unsigned integers.
    """

    def __init__(self, original_annotation: ImageAnnotation, image: torch.Tensor, boxes: torch.Tensor, labels: torch.Tensor):
        self.original_annotation = original_annotation
        self.image = image
        self.boxes = boxes
        self.labels = labels

class DatasetBatch():
    """
    Represents a batch of images as produced by a `DataLoader`.
    """

    original_annotations: List[ImageAnnotation]
    """
    The original annotations from this batch.
    """

    images: List[torch.Tensor]
    """
    A list of the images in this batch.
    """

    boxes: List[torch.Tensor]
    """
    A list of all the per-image bounding boxes in this batch.
    """

    labels: List[torch.Tensor]
    """
    A list of all the per-image labels in this batch.
    """

    def __init__(self, original_annotations: List[ImageAnnotation], images: List[torch.Tensor], boxes: List[torch.Tensor], labels: List[torch.Tensor]):
        self.original_annotations = original_annotations
        self.images = images
        self.boxes = boxes
        self.labels = labels

@overload
def collate(elt: DatasetElement) -> DatasetBatch: ...
@overload
def collate(elt: List[DatasetElement]) -> DatasetBatch: ...
def collate(elt: Union[DatasetElement, List[DatasetElement]]) -> DatasetBatch:
    """
    A utility function that collates several `DatasetElement`s into one `DatasetBatch`.
    """
    if not isinstance(elt, List):
        elt = [elt]

    return DatasetBatch(
        [d.original_annotation for d in elt],
        [d.image for d in elt],
        [d.boxes for d in elt],
        [d.labels for d in elt],
    )

class IterableDataset(TorchIterableDataset[DatasetElement]):
    """
    A PyTorch `IterableDataset` that yields all of the annotations from a
    given `DatasetVersion`. Provides functionality for automatically applying
    transforms to images, and then scaling the annotations to the new dimensions.

    Note, it is required that the transformation produce a image tensor of
    dimensionality `[..., H, W]`. One way of doing this is using
    `torchvision.transforms.functional.to_tensor` as the final step of the transform.
    """

    _dataset: Dataset
    _split: str
    _class_mapping: Dict[str, int]
    _class_names: Dict[int, str]
    _device: torch.device

    def __init__(
        self,
        dataset: Dataset,
        split: str,
        class_mapping: Optional[Dict[str, int]] = None,
        image_transform: Callable[[PIL.Image.Image], torch.Tensor] = TF.to_tensor,
        device: torch.device = torch.device("cpu")
    ):
        self._dataset = dataset
        self._split = split
        self._image_transform = image_transform
        self._device = device

        template_classes = dataset.template.classes.keys()
        if class_mapping is not None:
            if set(class_mapping.keys()) != set(template_classes):
                print(
                    "[WARNING]: Potentially invalid class mapping. Provided classes ",
                    set(class_mapping.keys()),
                    " but needed ",
                    set(template_classes)
                )
            self._class_mapping = class_mapping
        else:
            self._class_mapping = {
                cls: i
                for i, cls in enumerate(sorted(template_classes))
            }

        self._class_names = {
            i: cls
            for cls, i in self._class_mapping.items()
        }

    def _get_generator(self):
        worker_info: Optional[Any] = get_worker_info()

        if worker_info is None:
            return self._dataset.stream_split(self._split, 0, 1)
        else:
            num_workers: int = worker_info.num_workers
            worker_id: int = worker_info.id

            return self._dataset.stream_split(self._split, worker_id, num_workers)

    def __iter__(self) -> Generator[DatasetElement, None, None]:
        for annotation in self._get_generator():
            img = annotation.image.get_pil_image(True).convert("RGB")
            transformed_img = self._image_transform(img).to(self._device)
            h, w = transformed_img.shape[-2:]

            instance_boxes = [
                (
                    instance.bounding_box.rectangle.p1.x * w,
                    instance.bounding_box.rectangle.p1.y * h,
                    instance.bounding_box.rectangle.p2.x * w,
                    instance.bounding_box.rectangle.p2.y * h,
                )
                for class_name in annotation.classes.keys()
                for instance in annotation.classes[class_name].instances
                if instance.bounding_box is not None
            ]

            instance_labels = [
                self._class_mapping[class_name]
                for class_name in annotation.classes.keys()
                for _ in annotation.classes[class_name].instances
                if class_name in self._class_mapping
            ]

            target = torch.tensor(instance_boxes).reshape((-1, 4)).to(self._device)
            labels = torch.tensor(instance_labels, dtype = torch.int64).to(self._device)

            element = DatasetElement(annotation, transformed_img, target, labels)

            yield element
