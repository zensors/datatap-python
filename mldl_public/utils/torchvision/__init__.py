from __future__ import annotations

from typing import Callable, Dict, Iterator, Mapping, Tuple

import torch
from mldl_public.droplet import ImageAnnotation
from mldl_public.utils.dask import Bag, BagIterator
from PIL.Image import Image


def load_one(a: ImageAnnotation, id_map: Mapping[str, int]) -> Tuple[Image, Dict[str, torch.Tensor]]:
	image = a.image.get_pil_image().convert("RGB")
	w, h = image.size
	boxes = []
	labels = []
	iscrowd = []

	for k, v in a.classes.items():
		for instance in v.instances:
			if instance.bounding_box is not None:
				labels.append(id_map[k])
				boxes.append(instance.bounding_box.rectangle.normalize().scale((w, h)).to_xyxy_tuple())
				iscrowd.append(0)

		for multi_instance in v.multi_instances:
			if multi_instance.bounding_box is not None:
				labels.append(id_map[k])
				boxes.append(multi_instance.bounding_box.rectangle.normalize().scale((w, h)).to_xyxy_tuple())
				iscrowd.append(1)

	target = {
		"boxes": torch.as_tensor(boxes, dtype=torch.float32),
		"labels": torch.as_tensor(labels, dtype=torch.int64),
		"iscrowd": torch.as_tensor(iscrowd, dtype=torch.int64),
	}
	return image, target


def load_bag(bag: Bag[ImageAnnotation], id_map: Mapping[str, int]) -> Iterator[Tuple[Image, Dict[str, torch.Tensor]]]:
	iterator = BagIterator(bag)
	curried: Callable[[ImageAnnotation], Tuple[Image, Dict[str, torch.Tensor]]] = lambda x: load_one(x, id_map)
	return map(curried, iterator)
