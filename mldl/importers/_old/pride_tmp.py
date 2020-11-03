import argparse
import json
import sys
from dateutil.parser import isoparse
from os import environ, path
from typing import Sequence, Tuple, List

import dask.bag
import PIL.Image
from dask.distributed import Client, LocalCluster

from mldl.importers.base import (Annotation, ClassAnnotation, Image, Instance,
                                 Keypoint, Mask, Point, PrideAnnotation,
                                 PrideMetadata, Rectangle, get_image_digest,
                                 write_output_tar)

def pride_instance_to_droplet(instance: dict) -> Instance:
	return Instance(
		bounding_box = Rectangle.from_json(instance["boundingBox"]),
		segmentation = Mask.from_json(instance["segmentation"]) if "segmentation" in instance else None,
		keypoints = {
			keypoint_name: Keypoint.from_json(instance["keypoints"][keypoint_graph][keypoint_name])
			for keypoint_graph in instance["keypoints"]
			for keypoint_name in instance["keypoints"][keypoint_graph]
		} if "keypoints" in instance else None
	)

def pride_class_to_droplet(class_annotation: dict) -> ClassAnnotation:
	instances: List[Instance] = []

	if "instances" in class_annotation:
		for instance in class_annotation["instances"]:
			try:
				instances.append(pride_instance_to_droplet(instance))
			except Exception as e:
				print(f"Skipping invalid instance: {e}")

	return ClassAnnotation(instances = instances)

def pride_annotation_to_droplet(annotation: dict) -> PrideAnnotation:
	return PrideAnnotation(
		image = Image(paths = annotation["response"]["image"]["paths"]),
		classes = {
			class_name: pride_class_to_droplet(annotation["response"]["image"]["label"]["objectDetection"]["classes"][class_name])
			for class_name in annotation["response"]["image"]["label"]["objectDetection"]["classes"]
		},
		pride_metadata = PrideMetadata(labeler_uid = annotation["worker_uid"], labeled_at = isoparse(annotation["resolved_at"]))
	)

def reformat_mask_annotation(annotation: PrideAnnotation) -> PrideAnnotation:
	# reformatter for mask data: everything is actually of class "face"; we need to map the classes to attributes
	instances = [
		Instance(
			bounding_box = instance.bounding_box,
			segmentation = instance.segmentation,
			keypoints = instance.keypoints,
			attributes = { "is masked": "masked" if class_name == "masked face" else "unmasked" }
		)
		for class_name in ["masked face", "unmasked face"]
		for instance in annotation.classes[class_name].instances
	]

	return PrideAnnotation(
		image = annotation.image,
		classes = { "face": ClassAnnotation(instances = instances, clusters = []) },
		pride_metadata = annotation.pride_metadata
	)


def main(argv):
	parser = argparse.ArgumentParser()
	parser.add_argument(
		"--annotations",
		required = True,
		help="Path to annotations .jsonl file"
	)
	parser.add_argument(
		"--data-source",
		required = True,
		help="The name to use for this data source"
	)
	parser.add_argument(
		"--data-source-uid",
		required = True,
		help="The UID to use for this data source"
	)
	parser.add_argument("--output", default="out.tar.gz")
	parser.add_argument("--workers", type=int)
	args = parser.parse_args()

	cluster = LocalCluster(n_workers = args.workers, dashboard_address = "0.0.0.0:8787")
	print("Dask dashboard available at:", cluster.dashboard_link)
	client = Client(cluster)

	annotations = dask.bag.read_text(args.annotations) \
		.map(json.loads) \
		.map(pride_annotation_to_droplet) \
		# .map(reformat_mask_annotation) # comment this line out if not doing mask annotations

	write_output_tar(annotations, args.data_source, args.output, args.data_source_uid)

if __name__ == "__main__":
	main(sys.argv)
