import argparse
import re
import sys
from ast import literal_eval
from glob import glob
from os.path import join as path_join
from os.path import split as path_split
from os.path import splitext
from typing import Dict, List, Mapping, NamedTuple, Optional, Sequence, Tuple, cast

import dask.bag
import dask.bytes
import dask.dataframe
from dask.distributed import Client, LocalCluster
from mldl.importers.base import (Annotation, ClassAnnotation, Image, Instance,
                                 Keypoint, Point, Rectangle, get_image_digest,
                                 write_output_tar)

HELP = """
Imports a single subset of the carfusion dataset.

For example, for car_fifth1:

python -m mldl.importers.carfusion path/to/car_fifth1 --image-storage-path="s3://path/to/car_fifth1 --data-source="Carfusion (car_fifth1)"
"""

"""
How to run this, e.g. for butler1:

python -m mldl.importers.carfusion ~/carfusion/car_butler1 \
	--output="out/carfusion/car_butler1/*.image.jsonl.gz"
"""

# note: image width / height hard coded.
IMAGE_WIDTH = 1920
IMAGE_HEIGHT = 1080

CARFUSION_KEYPOINT_NAMES = [
	"__unused__",
	"right front tire",
	"left front tire",
	"right back tire",
	"left back tire",
	"right headlight",
	"left headlight",
	"right taillight",
	"left taillight",
	"exhaust pipe",
	"right front roof",
	"left front roof",
	"right back roof",
	"left back roof"
]

class KeypointTuple(NamedTuple):
	keypoint: Keypoint
	instance_index: int
	keypoint_name: str

def parse_kp_line(line: str) -> Optional[KeypointTuple]:
	# line format is a list of comma-separated numbers: x, y, keypoint index, instance index, visibility
	# for example: 1413.64,753.18,1,0,3
	x, y, keypoint_index, instance_index, visibility = cast(Tuple[float, float, int, int, int], literal_eval(line))
	x /= IMAGE_WIDTH
	y /= IMAGE_HEIGHT

	if not (0 <= x <= 1 and 0 <= y <= 1):
		return None # ignore out-of-bounds keypoints

	occluded = (
		None if visibility == 0 else
		False if visibility == 1 else
		True # not sure what the difference between 2 and 3 is
	)

	keypoint = Keypoint(Point(x, y, clip = True), occluded = occluded)
	return KeypointTuple(keypoint, instance_index, CARFUSION_KEYPOINT_NAMES[keypoint_index])

def parse_bbox_line(line: str) -> Tuple[Rectangle, str]:
	# line format is a numpy array, then a comma, then the class name
	# for example: [ 1370.   606.   436.   178.],bus

	match = re.search(r"\[\s*([0-9\.]+)\s+([0-9\.]+)\s+([0-9\.]+)\s+([0-9\.]+)\],(.+)", line)

	if match is None:
		raise RuntimeError("invalid line: {}".format(line))

	x_str, y_str, w_str, h_str, class_name = match.groups()
	x = float(x_str) / IMAGE_WIDTH
	y = float(y_str) / IMAGE_HEIGHT
	w = float(w_str) / IMAGE_WIDTH
	h = float(h_str) / IMAGE_HEIGHT
	return Rectangle(Point(x, y), Point(x + w, y + h)), class_name

def create_instance(bounding_box: Rectangle, keypoints: Mapping[str, Keypoint]) -> Instance:
	if len(keypoints) > 0:
		# If we have keypoints, adjust the bounding box to ensure that it covers the keypoints plus a bit of padding.
		# We do this because the bounding boxes in carfusion tend to be smaller than the actual car, but the keypoints
		# tend to be well-placed when they exist.  The additional 5% of padding is empirically roughly the right amount
		# to produce a reasonable bounding box.

		keypoint_bounding_box = Rectangle.from_point_set([kp.point for kp in keypoints.values()])
		padded_bounding_box = keypoint_bounding_box.scale_from_center(1.05).clip()
		bounding_box = Rectangle(
			Point(min(bounding_box.p1.x, padded_bounding_box.p1.x), min(bounding_box.p1.y, padded_bounding_box.p1.y)),
			Point(max(bounding_box.p2.x, padded_bounding_box.p2.x), max(bounding_box.p2.y, padded_bounding_box.p2.y))
		)

	return Instance(bounding_box = bounding_box, keypoints = keypoints)

def carfusion_to_droplet(image_path: str, image_storage_path: str) -> Optional[Annotation]:
	dirname, basename = path_split(image_path)
	image_name, _ext = splitext(basename)

	try:
		with open(path_join(dirname, "..", "bb", image_name + ".txt")) as infile:
			bounding_boxes = [parse_bbox_line(line) for line in infile.readlines()]

		with open(path_join(dirname, "..", "gt", image_name + ".txt")) as infile:
			all_keypoints = [parse_kp_line(line) for line in infile.readlines()]
	except IOError as e:
		print(f"Missing annotation file for {basename}; skipping")
		return None

	instance_keypoints: Sequence[Dict[str, Keypoint]] = [dict() for _ in bounding_boxes]

	for keypoint_tuple in all_keypoints:
		if keypoint_tuple is not None:
			keypoint, instance_index, keypoint_name = keypoint_tuple
			instance_keypoints[instance_index][keypoint_name] = keypoint

	class_map: Mapping[str, List[Instance]] = { "car": [], "bus": [], "truck": [] }

	for (bounding_box, class_name), keypoints in zip(bounding_boxes, instance_keypoints):
		class_map[class_name].append(create_instance(bounding_box, keypoints))

	return Annotation(
		image = Image(
			paths = [path_join(image_storage_path, basename)],
			hash = get_image_digest(image_path)
		),
		classes = {
			class_name: ClassAnnotation(instances = instances)
			for class_name, instances in class_map.items()
		}
	)

def main():
	parser = argparse.ArgumentParser(description=HELP)
	parser.add_argument(
		"dir",
		help = "Base directory for the sub-dataset",
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
	parser.add_argument("--workers", type=int)
	args = parser.parse_args()

	cluster = LocalCluster(n_workers = args.workers, dashboard_address = "0.0.0.0:8787")
	print("Dask dashboard available at:", cluster.dashboard_link)
	client = Client(cluster)

	image_paths = dask.bag.from_sequence(glob(path_join(args.dir, "images_jpg", "*.jpg")))
	annotations = (
		image_paths
			.map(carfusion_to_droplet, image_storage_path = args.image_storage_path)
			.filter(lambda anno: anno is not None)
	)
	write_output_tar(annotations, args.data_source, args.output)

	client.close()
	cluster.close()

if __name__ == "__main__":
	main()
