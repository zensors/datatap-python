RLE_SUPPORT = False

import argparse
import hashlib
import itertools
import json
import os
from os.path import join as path_join
import sys
from typing import Callable, Dict, List, Optional, Tuple, Union, cast

import dask.bag
import numpy as np
from dask.distributed import Client, LocalCluster

from mldl.importers.base import Annotation, ClassAnnotation, MultiInstance, get_image_digest, Image, Instance, Keypoint, Mask, Point, Polygon, Rectangle, write_output_tar

if RLE_SUPPORT:
	from pycocotools import mask
	from skimage import measure

HELP = """
Imports any coco-like dataset.

To import COCO 2017 Train:

python -m mldl.importers.coco \
	--instances="path/to/instances_2017.json" \
	--person-keypoints="path/to/person_keypoints_train2017.json" \
	--images="path/to/images" \
	--image-storage-path="s3://path/to/coco/images" \
	--data-source="COCO 2017 Train"
"""

COCO_KEYPOINT_VISIBILITY_MISSING = 0
COCO_KEYPOINT_VISIBILITY_OCCLUDED = 1
COCO_KEYPOINT_VISIBILITY_VISIBLE = 2

def convert_coco_kp(coco_kp, category: dict, w: float, h: float, do_clip: bool = False):
	keypoint_names = list(map(lambda n: n.replace("_", " "), category["keypoints"]))
	keypoints = {
		name: None if v == COCO_KEYPOINT_VISIBILITY_MISSING else Keypoint(point=Point(x = x / w, y = y / h, clip = do_clip), occluded=(v == COCO_KEYPOINT_VISIBILITY_OCCLUDED))
		for (name, (x, y, v)) in zip(keypoint_names, np.reshape(coco_kp, (-1, 3)).tolist())
	}
	return keypoints

if RLE_SUPPORT:
	def decode_rle(anno):
		image = anno["image"]
		if type(anno.get("segmentation", [])) is list:
			return anno
		new_anno = dict(anno)
		del new_anno["segmentation"]
		binary_mask = mask.decode(
			mask.frPyObjects(anno["segmentation"], image["width"], image["height"])
		)
		segmentation = map(
			lambda x: np.flip(x, axis=1).ravel().tolist(),
			measure.find_contours(binary_mask, 0.5),
		)
		# should have at least 3 points in each poly
		segmentation = list(filter(lambda poly: len(poly) >= 6, segmentation))
		# also remove excessive points

		def reduce_points(poly, target=100):
			reduction_rate = int((len(poly) // 2) / target)
			if reduction_rate < 2:
				return poly
			new_poly = []
			for i in range(0, len(poly), 2 * reduction_rate):
				new_poly.append(poly[i])
				new_poly.append(poly[i + 1])
			return new_poly

		segmentation = list(map(reduce_points, segmentation))

		# assert: after filtering trival contours, segmentation should not be empty
		# if this assertion fails, check validity of the mask
		assert len(segmentation) > 0
		new_anno["segmentation"] = segmentation
		return new_anno

def coco_segmentation_to_droplet(seg: List[float], w: int, h: int, do_clip: bool = False) -> Polygon:
	if len(seg) == 0:
		raise IndexError("segmentation can't be empty")
	if len(seg) % 2 != 0:
		raise IndexError("segmentation must be in x, y pairs")

	points = []
	for (x, y) in zip(seg[0::2], seg[1::2]):
		points.append(Point(x = x / w, y = y / h, clip = do_clip))
	return Polygon(points = points)


def coco_box_to_droplet(box: Tuple[int, int, int, int], w: int, h: int, do_clip: bool = False) -> Rectangle:
	ix, iy, iw, ih = box
	return Rectangle(
		p1 = Point(x = ix / w, y = iy / h, clip = do_clip),
		p2 = Point(x = (ix + iw) / w, y = (iy + ih) / h, clip = do_clip)
	)

def coco_object_to_droplet(obj: dict, img, do_clip: bool = False) -> Tuple[str, Union[Instance, MultiInstance]]:
	name: str = obj["category"]["name"]
	bounding_box = coco_box_to_droplet(
		obj["bbox"], img["width"], img["height"], do_clip=do_clip
	)

	# TODO: support RLE
	segmentation: Optional[Mask] = None
	if type(obj.get("segmentation", None)) is list:
		segmentation =  Mask(
			polygons = list(map(
				lambda s: coco_segmentation_to_droplet(
					s, img["width"], img["height"], do_clip=do_clip
				),
				obj["segmentation"],
			)
		))

	keypoints: Optional[Dict[str, Optional[Keypoint]]] = None # TODO: fix missing keypoints
	if obj.get("keypoints") is not None and obj.get("num_keypoints", 0) > 0:
		keypoints = convert_coco_kp(
			obj["keypoints"],
			obj["category"],
			img["width"],
			img["height"],
			do_clip=do_clip,
		)

	if obj.get("iscrowd", False):
		return name, MultiInstance(bounding_box = bounding_box, segmentation = segmentation)
	else:
		return name, Instance(bounding_box = bounding_box, segmentation = segmentation, keypoints = keypoints)

def coco_image_to_droplet(image: dict, do_clip: bool, image_path: str, image_storage_path: str) -> Annotation:
	annos = image["annotations"]
	img = Image(
		paths = [
			path_join(image_storage_path, image["file_name"]),
			cast(str, image["coco_url"]),
			cast(str, image["flickr_url"])
		],
		hash = get_image_digest(path_join(image_path, image["file_name"]))
	)

	class_names = { cat["name"] for cat in image["categories"] }
	instances: Dict[str, List[Instance]] = { class_name: [] for class_name in class_names }
	multi_instances: Dict[str, List[MultiInstance]] = { class_name: [] for class_name in class_names }

	for anno in annos:
		class_name, obj = coco_object_to_droplet(anno, image, do_clip)
		if isinstance(obj, Instance):
			instances[class_name].append(obj)
		else:
			multi_instances[class_name].append(obj)

	return Annotation(
		image = img,
		classes = {
			class_name: ClassAnnotation(instances = instances[class_name], multi_instances = multi_instances[class_name])
			for class_name in class_names
		}
	)


def preprocess(coco_instances_path, coco_person_keypoints_path):
	# Turn the file into a jsonl file so dask is happy about it.
	# (Putting multi-hundred MBs of data in one JSON is really a bad idea, who would've thought.)

	with open(coco_instances_path, "r") as f:
		instances = json.load(f)

	keypoints = {
		"annotations": [],
		"categories": [],
	}
	if coco_person_keypoints_path != None:
		print("Loading Keypoints")
		with open(coco_person_keypoints_path, "r") as f:
			keypoints = json.load(f)

	print("Gathering Images and Categories")
	image_dict = dict(map(lambda img: (img["id"], img), instances["images"]))
	category_dict = dict(map(lambda cat: (cat["id"], cat), instances["categories"]))
	keypoint_category_dict = dict(
		map(lambda cat: (cat["id"], cat), keypoints["categories"])
	)
	category_dict.update(keypoint_category_dict)

	print("Calculating overlap between keypoints dataset and instances dataset")
	instance_annotations = instances["annotations"]
	keypoint_annotations = keypoints["annotations"]
	keypoint_annotation_dict = dict(
		map(lambda anno: (anno["id"], anno), keypoint_annotations)
	)

	merged_annotations = map(
		lambda anno: keypoint_annotation_dict.get(anno["id"], anno),
		instance_annotations,
	)

	print("Folding category into annotations")
	merged_annotations = map(
		lambda anno: {**anno, "category": category_dict[anno["category_id"]]},
		merged_annotations,
	)

	for image_id in image_dict:
		image_dict[image_id]["annotations"] = []
		image_dict[image_id]["categories"] = instances["categories"]

	for anno in merged_annotations:
		image = image_dict[anno["image_id"]]
		image["annotations"].append(anno)

	print("Outputting JSON lines for annotations")
	with open("./tmp.jsonl", "w") as f:
		f.writelines(map(lambda anno: json.dumps(anno) + "\n", image_dict.values(),))

def main(argv):
	parser = argparse.ArgumentParser(description=HELP)
	parser.add_argument(
		"--instances",
		required = True,
		help = "Instance file for COCO, usually in the form of instances_trainXXXX.json",
	)
	parser.add_argument(
		"--person-keypoints",
		help = "File for COCO keypoints to override the original JSON",
	)
	parser.add_argument(
		"--images",
		required = True,
		help = "Path to the images directory",
	)
	parser.add_argument(
		"--image-storage-path",
		required = True,
		help="The base path at which images are stored (probably an S3 URL)"
	)
	parser.add_argument(
		"--data-source",
		required = True,
		help="The name to use for this data source"
	)
	parser.add_argument("--output", default="out.tar.gz")
	parser.add_argument("--blocksize", default="30MB")
	parser.add_argument("--skip-preprocess", action="store_true")
	parser.add_argument("--clip", action="store_true")
	parser.add_argument("--workers", type=int)
	args = parser.parse_args()

	if not args.skip_preprocess:
		print("Loading JSONs")
		preprocess(args.instances, args.person_keypoints)

	cluster = LocalCluster(n_workers = args.workers, dashboard_address = "0.0.0.0:8787")
	print("Dask dashboard available at:", cluster.dashboard_link)
	client = Client(cluster)

	images = dask.bag.read_text("./tmp.jsonl", blocksize=args.blocksize).map(json.loads)
	zensors_images = images.map(coco_image_to_droplet, do_clip=args.clip, image_path = args.images, image_storage_path = args.image_storage_path)
	write_output_tar(zensors_images, args.data_source, args.output)


if __name__ == "__main__":
	main(sys.argv)
