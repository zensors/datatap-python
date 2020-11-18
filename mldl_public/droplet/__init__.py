"""
This module provides classes for working with ML data.  Specifically, it provides methods for creating new ML data
objects, converting ML data objects to and from the JSON droplet format, and manipulating ML data objects.
"""

from .bounding_box import BoundingBox, BoundingBoxJson
from .class_annotation import ClassAnnotation, ClassAnnotationJson
from .image import Image, ImageJson
from .image_annotation import ImageAnnotation, ImageAnnotationJson
from .instance import Instance, InstanceJson
from .keypoint import Keypoint, KeypointJson
from .multi_instance import MultiInstance, MultiInstanceJson
from .segmentation import Segmentation, SegmentationJson

__all__ = [
	"BoundingBox",
	"BoundingBoxJson",
	"ClassAnnotation",
	"ClassAnnotationJson",
	"Image",
	"ImageJson",
	"ImageAnnotation",
	"ImageAnnotationJson",
	"Instance",
	"InstanceJson",
	"Keypoint",
	"KeypointJson",
	"MultiInstance",
	"MultiInstanceJson",
	"Segmentation",
	"SegmentationJson",
]
