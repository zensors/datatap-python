from datatap.droplet.bounding_box import BoundingBox
from typing import Dict, List

import torch
import torchvision.transforms.functional as TF

from datatap.geometry import Point, Rectangle
from datatap.droplet import Instance, ClassAnnotation, ImageAnnotation, Image

def tensor_to_rectangle(tensor: torch.Tensor) -> Rectangle:
    """
    Expects a tensor of dimensionality `torch.Size([4])` in `xyxy` format
    """
    return Rectangle(
        Point(float(tensor[0]), float(tensor[1]), clip = True),
        Point(float(tensor[2]), float(tensor[3]), clip = True),
    )

def torch_to_image_annotation(
    image: torch.Tensor,
    class_map: Dict[str, int],
    *,
    labels: torch.Tensor,
    boxes: torch.Tensor,
    scores: torch.Tensor,
    serialize_image: bool = False,
) -> ImageAnnotation:
    """
    Creates an `ImageAnnotation` from a canonical tensor representation.

    This function assumes the following,

    1. Image is of dimensionality `(..., height, width)`
    2. Labels are an `int`/`uint` tensor of size `[n]`
    3. Scores are a `float` tensor of size `[n]`
    3. Boxes are a `float` tensor of size `[n, 4]`
    """
    inverted_class_map = {
        i: cls
        for cls, i in class_map.items()
    }

    height, width = image.shape[-2:]

    # First construct the image. If we are asked to serialize it, then
    # use the tensor to construct a cached PIL image
    if serialize_image:
        pil_image = TF.to_pil_image(image, "RGB")
        droplet_image = Image.from_pil(pil_image)
    else:
        droplet_image = Image(paths = [])

    # Then, compute each of the class annotations
    class_annotations: Dict[str, List[Instance]] = {}

    boxes = boxes.cpu() / torch.tensor([width, height, width, height])

    for i, label in enumerate(labels.cpu()):
        class_name = inverted_class_map.get(int(label))
        if class_name is None:
            continue

        if class_name not in class_annotations:
            class_annotations[class_name] = []

        class_annotations[class_name].append(
            Instance(
                bounding_box = BoundingBox(
                    tensor_to_rectangle(boxes[i]),
                    confidence = float(scores[i]),
                )
            )
        )

    # Finally, construct the image annotation

    return ImageAnnotation(
        image = droplet_image,
        classes = {
            cls: ClassAnnotation(instances = instances, multi_instances = [])
            for cls, instances in class_annotations.items()
        }
    )