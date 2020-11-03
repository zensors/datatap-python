"""Generates SVG visualizations for a image, with the option of embedding the image"""

import base64
import io
import types
import random
import string
from typing import Optional, Tuple, Sequence, Mapping, cast

from mldl.droplet import Annotation, Instance, MultiInstance, Keypoint
from mldl.geometry import Mask

from . import loader
from .color_map import color_map

def trim(s: str) -> str:
    return "".join(map(str.strip, s.split("\n")))

def gen_id() -> str:
    return "".join([random.choice(string.ascii_lowercase) for i in range(12)])


# TODO(yifangu): Add skeleton support

SVG_TEMPLATE = trim(
    """
<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg width="{w:.0f}" height="{h:.0f}" viewBox="{view_box[0]} {view_box[1]} {view_box[2]} {view_box[3]}" xmlns="http://www.w3.org/2000/svg">
<defs>
{defs}
</defs>
<style>
.name {{
    font-family: monospace;
    font-size: 18px;
}}
.stroke {{
    stroke-width: {stroke_width};
}}
.predicted .stroke {{
    stroke-dasharray: 10,10;
}}
.label-object .keypoints .edge {{
    stroke-opacity: 0.5;
}}
.label-object .keypoints .keypoint .point {{
    fill-opacity: 1;
}}
.label-object .keypoints .keypoint.occluded .point  {{
    fill-opacity: 0;
}}
.label-object .keypoint .name {{
    visibility: hidden;
    stroke: #ffffff;
    stroke-width: 3px;
    paint-order: stroke;
}}
.label-object .keypoint:hover .name {{
    visibility: visible;
}}
.label-object>.name {{
    visibility: hidden;
    stroke: #ffffff;
    stroke-width: 3px;
    paint-order: stroke;
}}
.label-object>.track-id {{
    stroke: #ffffff;
    stroke-width: 8px;
    paint-order: stroke;
    font-size: 20px;
    font-family: monospace;
}}
.label-object:hover>.name {{
    visibility: visible;
}}
.segmentation .polygon {{
    stroke: none !important;
}}
.label-object:hover .segmentation .polygon {{
    stroke: #ffffff !important;
}}
.label-object:hover .keypoints .edge {{
    stroke: #ffffff !important;
    fill: #ffffff !important;
}}
.label-object:hover .keypoints .keypoint .point {{
    stroke: #ffffff !important;
    fill: #ffffff !important;
}}
</style>
{0}
</svg>
"""
)

GROUP_TEMPLATE = trim(
    """
<g class="{class_name}">
{0}
</g>
"""
)

LABEL_OBJECT_COLOR_TEMPLATE = trim(
    """
<style>
    .label-object-{name} .stroke {{
        stroke: rgb({color[0]},{color[1]},{color[2]});
    }}
    .label-object-{name} .fill {{
        fill: rgb({color[0]},{color[1]},{color[2]});
    }}
</style>
"""
)

IMAGE_TEMPLATE = trim(
    """
<image x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" href="data:image/jpeg;base64,{0}" />
"""
)

BOX_OUTLINED_TEMPLATE = trim(
    """
<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" class="stroke" style="fill:none; stroke:#ffffff;" />
<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" class="stroke" style="fill:none;" />
"""
)

BOX_TEMPLATE = trim(
    """
<rect x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" class="stroke" style="fill:rgba(0,0,0,0);" />
"""
)

TEXT_TEMPLATE = trim(
    """
<text x="{x:.0f}" y="{y:.0f}" class="fill {class_name}">{}</text>
"""
)

COLORED_TEXT_TEMPLATE = trim(
  """
<text x="{x:.0f}" y="{y:.0f}" class="fill {class_name}" style="fill: rgb{color}">{}</text>
"""
)

POLYGON_TEMPLATE = trim(
    """
<polygon class="polygon fill stroke" points="{points}" style="fill-opacity:0.3;" />
"""
)

POINT_TEMPLATE = trim(
    """
<ellipse class="stroke fill {class_name}" cx="{cx:.0f}" cy="{cy:.0f}" rx="3" ry="3" style="stroke-width:1" />
"""
)

EDGE_TEMPLATE = trim(
    """
<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" class="stroke {class_name}" style="stroke-width:2;" />
"""
)


class SvgAnnotation:
    def __init__(self, tag, props = {}, styles = {}, defs = [], children = []):
        self.tag = tag
        self.props = props
        self.styles = styles
        self.defs = defs
        self.children = children

    def render(self, image_width, image_height):
        styles = " ".join(["{}: {};".format(key, value) for (key, value) in self.styles.items()])

        if type(self.props) is types.FunctionType:
            props = { **self.props(image_width, image_height), "style": styles }
        else:
            props = { **self.props, "style": styles }

        props = " ".join(["{}=\"{}\"".format(key, value) for (key, value) in props.items()])

        children = "\n".join([child.render(image_width, image_height) for child in self.children])
        return "<{tag} {props}>{children}</{tag}>".format(tag=self.tag, props=props, children=children)

    def get_defs(self):
        defs = []
        for def_elt in self.defs:
            defs += def_elt.get_defs() + [def_elt]
        for child in self.children:
            defs += child.get_defs()
        return defs


class Line(SvgAnnotation):
    def __init__(self, xyxy_line, color="#4977EA", width=6, dashed=False, start_arrow=False, end_arrow=False):
        self_id = "marker-" + gen_id()

        def props(image_width, image_height):
            points = []
            for point in xyxy_line:
                points.append(f"{point[0] * image_width},{point[1] * image_height}")

            result = {
                "points": " ".join(points)
            }

            if start_arrow:
                result["marker-start"] = f"url(#{self_id})"

            if end_arrow:
                result["marker-end"] = f"url(#{self_id})"

            return result

        styles = {
            "stroke": color,
            "stroke-width": width,
            "fill": "none",
        }

        if dashed:
            styles["stroke-dasharray"] = 16

        defs = []
        if start_arrow or end_arrow:
            defs = [SvgAnnotation(
                "marker",
                {
                    "id": self_id,
                    "viewBox": "0 0 10 10",
                    "refX": "5",
                    "refY": "5",
                    "markerWidth": str(width),
                    "markerHeight": str(width),
                    "orient": "auto-start-reverse",
                },
                {
                    "fill": color
                },
                children=[
                    SvgAnnotation("path", { "d": "M 0 0 L 10 5 L 0 10 z" })
                ],
            )]

        super().__init__("polyline", props, styles, defs, [])


def generate_svg(
    annotation: Annotation,
    class_skeletons: Mapping[str, Sequence[Tuple[str, str]]] = {},
    size: Optional[Tuple[int, int]] = None,
    stroke_width: int = 2,
    border: int = 20,
    annotations: Optional[Sequence[SvgAnnotation]] = None,
    use_image: bool = True
):
    if use_image and size is None:
        image = loader.load_image_from_annotation(annotation)
        size = image.size
    elif use_image and size is not None:
        image = loader.load_image_from_annotation(annotation)
        image = image.resize(size)
    elif size is None:
        size = (100, 100)
    iw, ih = size
    elements = []

    if image is not None:
        jpeg_file = io.BytesIO()
        image.save(jpeg_file, format="jpeg", quality=50)
        elements.append(IMAGE_TEMPLATE.format(base64.b64encode(jpeg_file.getvalue()).decode("ascii"), x = 0, y = 0, w = iw, h = ih))

    def segmentation_to_object_group(segmentation: Mask):
        segmentation_group = []
        for polygon in segmentation.polygons:
            points = " ".join(
                map(
                    lambda point: ",".join(
                        (str(point.x * iw), str(point.y * ih))
                    ),
                    polygon.points,
                )
            )
            segmentation_group.append(POLYGON_TEMPLATE.format(points = points))
        return GROUP_TEMPLATE.format("\n".join(segmentation_group), class_name="segmentation")

    def keypoints_to_object_group(keypoints: Mapping[str, Optional[Keypoint]], keypoint_edges: Optional[Sequence[Tuple[str, str]]]):
        keypoint_graph_group = []

        if keypoint_edges is not None:
            for v1, v2 in keypoint_edges:
                if v1 in keypoints and keypoints[v1] is not None and v2 in keypoints and keypoints[v2] is not None:
                    keypoint_graph_group.append(EDGE_TEMPLATE.format(
                        x1 = cast(Keypoint, keypoints[v1]).point.x * iw,
                        y1 = cast(Keypoint, keypoints[v1]).point.y * ih,
                        x2 = cast(Keypoint, keypoints[v2]).point.x * iw,
                        y2 = cast(Keypoint, keypoints[v2]).point.y * ih,
                        class_name = "edge",
                    ))
        for node_name, kp in keypoints.items():
            if kp is None:
                continue
            keypoint_group = []
            x, y = kp.point.x, kp.point.y
            keypoint_group.append(POINT_TEMPLATE.format(cx = x * iw, cy = y * ih, class_name = "point"))
            keypoint_group.append(TEXT_TEMPLATE.format(node_name, x = x * iw + 3, y = y * ih - 3, class_name="name"))
            keypoint_graph_group.append(GROUP_TEMPLATE.format(
                "\n".join(keypoint_group),
                class_name="keypoint occluded" if kp.occluded else "keypoint"
            ))

        return GROUP_TEMPLATE.format("\n".join(keypoint_graph_group), class_name="keypoints")

    def instance_to_object_group(instance: Instance, name: str):
        obj_list = []
        class_name = f"label label-object label-object-{name + str(instance.identity)}"
        color = color_map.update_and_get(name, instance.identity) # add to color map

        xmin = instance.bounding_box.p1.x
        ymin = instance.bounding_box.p1.y
        xmax = instance.bounding_box.p2.x
        ymax = instance.bounding_box.p2.y
        x, y, w, h = xmin * iw, ymin * ih, (xmax - xmin) * iw, (ymax - ymin) * ih

        obj_list.append(BOX_TEMPLATE.format(x = x, y = y, w = w, h = h, class_name = class_name))

        display_name = name
        if instance.confidence is not None:
            display_name = display_name + " ({:1.3})".format(instance.confidence)
            class_name = class_name + " predicted"
        obj_list.append(TEXT_TEMPLATE.format(display_name, x = x, y = y - 3, class_name = "name"))

        if instance.identity is not None:
            obj_list.append(COLORED_TEXT_TEMPLATE.format(
                f"ID: {instance.identity}", x = x, y = y + h + 16, class_name="track-id", color=color
            ))

        if instance.segmentation is not None:
            obj_list.append(segmentation_to_object_group(instance.segmentation))

        if instance.keypoints is not None:
            obj_list.append(keypoints_to_object_group(instance.keypoints, class_skeletons.get(name, None)))

        return GROUP_TEMPLATE.format("\n".join(obj_list), class_name = class_name)

    def multi_instance_to_object_group(multi_instance: MultiInstance, name: str):
        obj_list = []
        class_name = f"label label-object label-object-{name}"
        color = color_map.update_and_get(name, None) # add to color map

        xmin = multi_instance.bounding_box.p1.x
        ymin = multi_instance.bounding_box.p1.y
        xmax = multi_instance.bounding_box.p2.x
        ymax = multi_instance.bounding_box.p2.y
        x, y, w, h = xmin * iw, ymin * ih, (xmax - xmin) * iw, (ymax - ymin) * ih

        obj_list.append(BOX_TEMPLATE.format(x = x, y = y, w = w, h = h, class_name = class_name))

        if multi_instance.confidence is not None:
            name = name + " ({:1.3})".format(multi_instance.confidence)
            class_name = class_name + " predicted"
        obj_list.append(TEXT_TEMPLATE.format("[multi_instance] " + name, x = x, y = y - 3, class_name = "name"))

        if multi_instance.segmentation is not None:
            obj_list.append(segmentation_to_object_group(multi_instance.segmentation))

        return GROUP_TEMPLATE.format("\n".join(obj_list), class_name = class_name)

    for name in annotation.classes:
        for instance in annotation.classes[name].instances:
            elements.append(instance_to_object_group(instance, name))
        for multi_instance in annotation.classes[name].multi_instances:
            elements.append(multi_instance_to_object_group(multi_instance, name))

    # color_map should now be populated
    for (class_name, identity), color in color_map.map.items():
        elements.append(LABEL_OBJECT_COLOR_TEMPLATE.format(name=class_name + str(identity), color=color))

    defs = []
    if annotations is not None:
        annotations_obj = SvgAnnotation("g", { "class": "annotation" }, {}, children=annotations)
        elements.append(annotations_obj.render(iw, ih))
        defs += annotations_obj.get_defs()

    def_string = "\n".join([def_elt.render(iw, ih) for def_elt in defs])

    return SVG_TEMPLATE.format(
        "\n".join(elements),
        w=iw + border * 2,
        h=ih + border * 2,
        view_box=(-border, -border, iw + border * 2, ih + border * 2),
        stroke_width=stroke_width,
        defs=def_string
    )


def save_svg(
    image_file_path: str,
    annotation: Annotation,
    class_skeletons: Mapping[str, Sequence[Tuple[str, str]]] = {},
    size: Optional[Tuple[int, int]] = None,
    stroke_width: int = 2,
    border: int = 20,
    use_image: bool = True
):
    svg = generate_svg(
        annotation, class_skeletons = class_skeletons, size=size,
        stroke_width=stroke_width, border = border, use_image = use_image
    )
    with open(image_file_path, "w") as f:
        f.write(svg)
