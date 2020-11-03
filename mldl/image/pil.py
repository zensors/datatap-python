"""Generates PIL visualizations for a image"""

import io
import os.path

import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont

from typing import Any, Sequence, Optional, Mapping, Tuple, cast

from mldl.droplet import Annotation, Keypoint, Instance, MultiInstance
from mldl.geometry import Point, Polygon, Rectangle, Mask

from . import loader
from .color_map import color_map


def generate_pil(
    annotation: Annotation,
    class_skeletons: Mapping[str, Sequence[Tuple[str, str]]] = {},
    size: Optional[Tuple[int, int]] = None,
    use_image: bool = True
) -> PIL.Image.Image:
    if use_image and size is None:
        image = loader.load_image_from_annotation(annotation)
        size = image.size
    elif use_image and size is not None:
        image = loader.load_image_from_annotation(annotation)
        image = image.resize(size)
    else:
        image = None
        size = (100, 100)
    iw, ih = size
    image = PIL.Image.new("RGBA", size) if image is None else image.convert("RGBA")
    draw: Any = PIL.ImageDraw.Draw(image)
    font = PIL.ImageFont.truetype(os.path.join("assets", "Courier_New.ttf"), 15)

    def draw_point(
        point: Point,
        fill: Optional[str] = None,
        outline: Optional[str] = None,
        width: int = 1,
        r: int = 3
    ):
        draw.ellipse(
            (point.x * iw - r, point.y * ih - r, point.x * iw + r, point.y * ih + r),
            fill=fill,
            outline=outline,
            width=width
        )

    def draw_rectangle(
        rectangle: Rectangle,
        fill: Optional[str] = None,
        outline: Optional[str] = None,
        width: int = 1
    ):
        xy_list = [(point.x * iw, point.y * ih) for point in (rectangle.p1, rectangle.p2)]
        draw.rectangle(xy_list, fill=fill, outline=outline, width=width)

    def draw_polygon(
        polygon: Polygon,
        fill: Optional[str] = None,
        outline: Optional[str] = None,
        width: int = 1
    ):
        xy_list = [(point.x * iw, point.y * ih) for point in polygon.points]
        xy_list.append(xy_list[0])
        draw.line(xy_list, fill=fill, width=width)
        for point in polygon.points:
            draw_point(point, fill=fill, outline=outline, r=width)

    def draw_mask(
        mask: Mask,
        fill: Optional[str] = None,
        outline: Optional[str] = None,
        width: int = 1
    ):
        for polygon in mask.polygons:
            draw_polygon(polygon, fill=fill, outline=outline, width=width)

    def draw_keypoints(
        keypoints: Mapping[str, Optional[Keypoint]],
        keypoint_edges: Optional[Sequence[Tuple[str, str]]],
        fill: Optional[str] = None,
        outline: Optional[str] = None,
        width: int = 1
    ):
        if keypoint_edges is not None:
            for v1, v2 in keypoint_edges:
                if v1 in keypoints and keypoints[v1] is not None and v2 in keypoints and keypoints[v2] is not None:
                    draw.line(
                        [
                            cast(Keypoint, keypoints[v1]).point.x * iw,
                            cast(Keypoint, keypoints[v1]).point.y * ih,
                            cast(Keypoint, keypoints[v2]).point.x * iw,
                            cast(Keypoint, keypoints[v2]).point.y * ih
                        ],
                        fill=fill,
                        width=width
                    )
        for _, kp in keypoints.items():
            if kp is None:
                continue
            draw_point(kp.point, fill=fill, outline=outline, r=width)

    def draw_instance(
        instance: Instance,
        class_name: str
    ):
        color = color_map.update_and_get(class_name, instance.identity)
        color_str = f"rgb({color[0]}, {color[1]}, {color[2]})"
        draw_rectangle(instance.bounding_box, outline=color_str, width=(4 if instance.confidence is None else 2))

        if instance.identity is not None: # tracking
            label = f"ID: {instance.identity}"
        else: # detection
            label = class_name + ("" if instance.confidence is None else f"({instance.confidence}")
        draw.text(
            (instance.bounding_box.p1.x * iw, instance.bounding_box.p1.y * ih),
            label,
            font=font,
            stroke_width=3,
            stroke_fill="rgb(0,0,0)"
        )

        if instance.segmentation is not None:
            draw_mask(instance.segmentation, outline=color_str)

        if instance.keypoints is not None:
            draw_keypoints(instance.keypoints, class_skeletons.get(class_name, None), fill=color_str, width=2)

    def draw_multi_instance(
        multi_instance: MultiInstance,
        class_name: str
    ):
        color = color_map.update_and_get(class_name, None)
        color_str = f"rgb({color[0]}, {color[1]}, {color[2]})"
        draw_rectangle(multi_instance.bounding_box, outline=color_str, width=(4 if multi_instance.confidence is None else 2))

        label = class_name + ("" if multi_instance.confidence is None else f"({multi_instance.confidence}")
        draw.text(
            (instance.bounding_box.p1.x * iw, instance.bounding_box.p1.y * ih),
            label,
            font=font,
            stroke_width=3,
            stroke_fill="rgb(0,0,0)"
        )

        if multi_instance.segmentation is not None:
            draw_mask(multi_instance.segmentation, outline=color_str)

    for class_name in annotation.classes:
        for instance in annotation.classes[class_name].instances:
            draw_instance(instance, class_name)
        for multi_instance in annotation.classes[class_name].multi_instances:
            draw_multi_instance(multi_instance, class_name)

    return image


def save_jpeg(image_file_path: str, *args: Any, **kwargs: Any):
    image = generate_pil(*args, **kwargs).convert("RGB")
    image.save(image_file_path, format="jpeg", quality=75)


def generate_jpeg(*args: Any, **kwargs: Any):
    jpeg_file = io.BytesIO()
    image = generate_pil(*args, **kwargs).convert("RGB")
    image.save(jpeg_file, format="jpeg", quality=75)
    return jpeg_file.getvalue()