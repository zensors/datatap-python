from __future__ import annotations

from PIL.Image import Image
from mldl.geometry.point import Point
from mldl.geometry.rectangle import Rectangle
from typing import Dict, Mapping, Tuple, Callable

import torch
from mldl.image.loader import load_image_from_annotation
from mldl.droplet import Annotation
from mldl.utils.dask import BagIterator, Bag

def load_one(a: Annotation, id_map: Mapping[str, int]):
	image = load_image_from_annotation(a).convert("RGB")
	w, h = image.size
	boxes = []
	labels = []
	iscrowd = []

	for k, v in a.classes.items():
		for instance in v.instances:
			labels.append(id_map[k])
			bbox: Rectangle = instance.bounding_box
			boxes.append(bbox.normalize().scale((w, h)).to_xyxy_tuple())
			iscrowd.append(0)
		for instance in v.multi_instances:
			labels.append(id_map[k])
			bbox: Rectangle = instance.bounding_box
			boxes.append(bbox.normalize().scale((w, h)).to_xyxy_tuple())
			iscrowd.append(1)
	target = {
		"boxes": torch.as_tensor(boxes, dtype=torch.float32),
		"labels": torch.as_tensor(labels, dtype=torch.int64),
		"iscrowd": torch.as_tensor(iscrowd, dtype=torch.int64),
	}
	return image, target


def load_bag(bag: Bag[Annotation], id_map: Mapping[str, int]):
	iterator = BagIterator(bag)
	curried: Callable[[Annotation], Tuple[Image, Dict[str, torch.Tensor]]] = lambda x: load_one(x, id_map)
	return map(curried, iterator)
