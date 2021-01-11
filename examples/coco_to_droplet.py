"""
Converts a COCO-like dataset into the Droplet format.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass
from enum import IntEnum
from typing import (Dict, List, Mapping, Optional, Sequence, SupportsBytes,
                    Tuple, Union, cast)

import numpy as np
import PIL.Image
import pycocotools.mask
import skimage.measure
from datatap.droplet import (BoundingBox, ClassAnnotation, Image,
                             ImageAnnotation, Instance, Keypoint,
                             MultiInstance, Segmentation)
from datatap.geometry import Mask, Point, Polygon, Rectangle
from datatap.template import (ClassAnnotationTemplate, ImageAnnotationTemplate,
                              InstanceTemplate, MultiInstanceTemplate)
from typing_extensions import Literal, TypedDict

################################ COCO Datatypes ################################

class CocoRle(TypedDict):
	counts: Sequence[int]
	size: Tuple[int, int]

CocoBox = Tuple[float, float, float, float]
CocoPolygon = Sequence[float]
CocoMask = Sequence[CocoPolygon]

class CocoKeypointVisibility(IntEnum):
	Missing = 0
	Occluded = 1
	Visible = 2

class CocoIsCrowd(IntEnum):
	Instance = 0
	MultiInstance = 1

class CocoInstanceAnnotationOptional(TypedDict, total = False):
	keypoints: Sequence[int]
	num_keypoints: Sequence[int]

class CocoInstanceAnnotation(CocoInstanceAnnotationOptional, TypedDict):
	id: int
	image_id: int
	category_id: int
	segmentation: CocoMask
	bbox: CocoBox
	iscrowd: Literal[CocoIsCrowd.Instance]

class CocoMultiInstanceAnnotation(TypedDict):
	id: int
	image_id: int
	category_id: int
	segmentation: CocoRle
	bbox: CocoBox
	iscrowd: Literal[CocoIsCrowd.MultiInstance]

CocoAnnotation = Union[CocoInstanceAnnotation, CocoMultiInstanceAnnotation]

class CocoImage(TypedDict):
	id: int
	width: int
	height: int
	coco_url: str
	flickr_url: str

class CocoCategoryOptional(TypedDict, total = False):
	keypoints: Sequence[str]

class CocoCategory(CocoCategoryOptional, TypedDict):
	id: int
	name: str

class CocoDataset(TypedDict):
	images: Sequence[CocoImage]
	annotations: Sequence[CocoAnnotation]
	categories: Sequence[CocoCategory]

############################## Conversion methods ##############################

@dataclass
class ConversionOptions:
	clip: bool
	rle_downsample_size: int

def convert_bounding_box(
	bbox: CocoBox,
	image: CocoImage,
	options: ConversionOptions
) -> BoundingBox:
	x1, y1, w, h = bbox
	x2 = x1 + w
	y2 = y1 + h

	return BoundingBox(
		Rectangle(
			Point(x1 / image["width"], y1 / image["height"], clip = options.clip),
			Point(x2 / image["width"], y2 / image["height"], clip = options.clip)
		)
	)

def convert_mask(
	coco_mask: CocoMask,
	image: CocoImage,
	options: ConversionOptions
) -> Segmentation:
	"""
	Converts the given COCO mask to a Droplet segmentation.
	"""

	return Segmentation(
		Mask([
			Polygon([
				Point(
					coco_polygon[i] / image["width"],
					coco_polygon[i + 1] / image["height"],
					clip = options.clip
				)
				for i in range(0, len(coco_polygon), 2)
			])
			for coco_polygon in coco_mask
		])
	)

def convert_rle(
	coco_rle: CocoRle,
	options: ConversionOptions
) -> Segmentation:
	"""
	Converts the given COCO RLE segmentation to a Droplet segmentation.

	Note that this requires converting it to a polygon-based segmentation, since
	Droplet only supports polygonal segmentations.  We do this by converting it
	to a low-res PIL image, and then approximating the resulting polygons.
	"""

	# decode the mask to a numpy array of 0s and 1s
	mask_as_numpy = pycocotools.mask.decode(
		pycocotools.mask.frPyObjects(coco_rle, coco_rle["size"][0], coco_rle["size"][1])
	)

	# turn the numpy array into an image for downsampling
	# TODO(mdsavage): investigate the types here; I'm not certain that this is accurate
	mask_as_pil = PIL.Image.fromarray(
		cast(SupportsBytes, mask_as_numpy * 255),
		"L"
	)

	# downsample the image
	mask_as_pil = mask_as_pil.resize(
		(options.rle_downsample_size, options.rle_downsample_size),
		resample = PIL.Image.BOX
	)

	# convert back to a numpy array
	mask_as_numpy = (
		np.array(mask_as_pil.getdata())
			.reshape((options.rle_downsample_size, options.rle_downsample_size))
			.transpose(1, 0)
	)

	# find the contours
	polygons = skimage.measure.find_contours(mask_as_numpy, 128)

	# downsize from our downsample size to 1x1
	polygons = [cast(np.ndarray, polygon / options.rle_downsample_size) for polygon in polygons]

	# produce approximated polygons to reduce the number of points
	polygons = [
		skimage.measure.approximate_polygon(polygon, 0.005)
		for polygon in polygons
	]

	# drop polygons with fewer than 3 points
	polygons = [
		polygon
		for polygon in polygons
		if len(polygon) >= 3
	]

	return Segmentation(
		Mask([
			Polygon([
				Point(
					point[0],
					point[1],
					clip = options.clip
				)
				for point in polygon
			])
			for polygon in polygons
		])
	)

def convert_keypoint(
	keypoint: Sequence[int], # of length 3
	image: CocoImage,
	options: ConversionOptions
) -> Optional[Keypoint]:
	"""
	Converts a single COCO keypoint to the Droplet format.
	"""

	if keypoint[2] == CocoKeypointVisibility.Missing:
		return None

	return Keypoint(
		Point(keypoint[0] / image["width"], keypoint[1] / image["height"], clip = options.clip),
		occluded = (keypoint[2] == CocoKeypointVisibility.Occluded)
	)

def convert_keypoints(
	coco: CocoInstanceAnnotation,
	image: CocoImage,
	category: CocoCategory,
	options: ConversionOptions
) -> Mapping[str, Optional[Keypoint]]:
	"""
	Converts all of the keypoints of the given instance to the Droplet format.
	"""

	# Ensure that the given instance/category have keypoints
	assert coco["keypoints"] is not None
	assert category["keypoints"] is not None

	return {
		kp_name: convert_keypoint(
			coco["keypoints"][3 * i : 3 * (i + 1)],
			image,
			options
		)
		for i, kp_name in enumerate(category["keypoints"])
	}

def convert_instance(
	coco: CocoInstanceAnnotation,
	image: CocoImage,
	category: CocoCategory,
	options: ConversionOptions
) -> Instance:
	"""
	Converts the given COCO instance to a Droplet instance.
	"""

	try:
		return Instance(
			bounding_box = convert_bounding_box(coco["bbox"], image, options),
			segmentation = convert_mask(coco["segmentation"], image, options),
			keypoints = convert_keypoints(coco, image, category, options) if "keypoints" in coco else None
		)
	except Exception as e:
		raise Exception("Failed processing instance {}".format(coco["id"])) from e

def convert_multi_instance(
	coco: CocoMultiInstanceAnnotation,
	image: CocoImage,
	category: CocoCategory,
	options: ConversionOptions
) -> MultiInstance:
	"""
	Converts the given COCO crowd-instance to a Droplet multi-instance.
	"""

	try:
		return MultiInstance(
			bounding_box = convert_bounding_box(coco["bbox"], image, options),
			segmentation = convert_rle(coco["segmentation"], options)
		)
	except Exception as e:
		raise Exception("Failed processing multi-instance {}".format(coco["id"])) from e

def get_category_mapping(coco: CocoDataset) -> Dict[int, CocoCategory]:
	"""
	Returns a mapping from category ids to category objects for the given
	dataset.
	"""

	return {
		category["id"]: category
		for category in coco["categories"]
	}

def get_image_mapping(coco: CocoDataset) -> Dict[int, CocoImage]:
	"""
	Returns a mapping from image ids to image objects for the given dataset.
	"""

	return {
		image["id"]: image
		for image in coco["images"]
	}

def get_annotation_mapping(coco: CocoDataset) -> Dict[int, CocoAnnotation]:
	"""
	Returns a mapping from annotation ids to annotation objects for the given
	dataset.
	"""

	return {
		annotation["id"]: annotation
		for annotation in coco["annotations"]
	}

def convert_dataset(
	coco: CocoDataset,
	options: ConversionOptions
) -> Tuple[Sequence[ImageAnnotation], ImageAnnotationTemplate]:
	"""
	Converts the given COCO-formatted dataset into the Droplet format.

	This returns both the actual list of annotations and a template describing
	what is present in them.
	"""

	class_mapping = get_category_mapping(coco)
	image_mapping = get_image_mapping(coco)

	# generate the template
	template = ImageAnnotationTemplate(
		classes = {
			category["name"]: ClassAnnotationTemplate(
				instances = InstanceTemplate(
					bounding_box = True,
					segmentation = True,
					keypoints = set(category.get("keypoints", []))
				),
				multi_instances = MultiInstanceTemplate(
					bounding_box = True,
					segmentation = True
				)
			)
			for category in class_mapping.values()
		}
	)

	# initialize the storage we're going to use to collect the detections
	# detections[image_id][class_id] is a tuple of two lists, the instances and the multi instances, for the particular
	# image
	detections: Mapping[int, Mapping[str, Tuple[List[Instance], List[MultiInstance]]]] = (
		defaultdict(lambda: defaultdict(lambda: ([], [])))
	)

	# collect the detections
	for detection in coco["annotations"]:
		image_id = detection["image_id"]
		image = image_mapping[image_id]
		class_id = detection["category_id"]
		clss = class_mapping[class_id]

		if detection["iscrowd"] == CocoIsCrowd.Instance:
			detection = cast(CocoInstanceAnnotation, detection) # TODO(mdsavage): determine why the cast is needed
			detections[image_id][clss["name"]][0].append(convert_instance(detection, image, clss, options))
		else:
			detection = cast(CocoMultiInstanceAnnotation, detection) # TODO(mdsavage): determine why the cast is needed
			detections[image_id][clss["name"]][1].append(convert_multi_instance(detection, image, clss, options))

	# produce the final annotations
	annotations = [
		ImageAnnotation(
			image = Image(
				paths = [image["coco_url"], image["flickr_url"]]
			),
			classes = {
				clss["name"]: ClassAnnotation(
					instances = detections[image_id][clss["name"]][0],
					multi_instances = detections[image_id][clss["name"]][1]
				)
				for clss in class_mapping.values()
			}
		)
		for image_id, image in image_mapping.items()
	]

	return annotations, template

def merge_coco(a: CocoDataset, b: CocoDataset) -> CocoDataset:
	"""
	Merges two COCO datasets into a single one.  When an image id, category id,
	or instance id is present in both, the image, category, or instance in the
	second dataset is treated as authoritative.

	This is useful for merging keypoint data into the main dataset (e.g., for
	COCO 2017).
	"""

	images = get_image_mapping(a)
	images.update(get_image_mapping(b))

	categories = get_category_mapping(a)
	categories.update(get_category_mapping(b))

	annotations = get_annotation_mapping(a)
	annotations.update(get_annotation_mapping(b))

	return {
		"images": list(images.values()),
		"categories": list(categories.values()),
		"annotations": list(annotations.values())
	}

##################################### Main #####################################

class Args:
	datasets: List[str]
	clip: bool
	rle_downsample_size: int

def main():
	parser = argparse.ArgumentParser(
		description = "Convert COCO-format annotations to droplets."
	)
	parser.add_argument(
		"datasets",
		metavar = "dataset",
		type = str,
		nargs = "+",
		help = """
			A COCO dataset file to convert.

			Images, categories, and annotations appearing in later annotation files that have the same IDs as those
			appearing in earlier files will take precendence.  The primary use for this is to import COCO keypoints by
			specifying the main dataset file as the first argument and the keypoints file as the second argument.
		"""
	)
	parser.add_argument(
		"--clip",
		action = "store_true",
		help = """
			Clip geometry to always lie in the unit square.  (Default: do not clip; this will cause an exception to be
			thrown for geometry outside the unit square, which may be useful in catching errors.)
		"""
	)
	parser.add_argument(
		"--rle-downsample-size",
		type = int,
		default = 200,
		help = """
			Size to which to downsample RLE-based masks before converting them to polygons.  (Default: 200)
		"""
	)
	args = Args()
	parser.parse_args(namespace = args)

	coco_dataset: CocoDataset = { "categories": [], "images": [], "annotations": [] }

	for dataset_file in args.datasets:
		with open(dataset_file) as file:
			coco_dataset = merge_coco(coco_dataset, json.load(file))

	annotations, template = convert_dataset(
		coco_dataset,
		ConversionOptions(clip = args.clip, rle_downsample_size = args.rle_downsample_size)
	)

	# Do something with the results here...
	print(template)
	print(len(annotations))
	print(type(annotations[0]))
	print(annotations[0].get_visualization_url())

if __name__ == "__main__":
	main()
