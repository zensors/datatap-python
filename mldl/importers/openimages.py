HELP = """
Imports open images dataset.

"""
import argparse
import math
import re
from collections import defaultdict
from dataclasses import dataclass
from os.path import join as path_join
from typing import Dict, Optional, Sequence, Tuple, get_type_hints, List

import dask.bag
import dask.dataframe as pd
import PIL.Image
# import pandas as pd
from dask import delayed
from dask.distributed import Client, LocalCluster
from unidecode import unidecode

from mldl.importers.base import (Annotation, ClassAnnotation, MultiInstance, Image,
								 Instance, Keypoint, Mask, Point, Polygon,
								 Rectangle, get_image_digest, write_output_tar)

from mldl.template.annotation_template import AnnotationTemplate
from mldl.template.class_annotation_template import ClassAnnotationTemplate
from mldl.template.instance_template import InstanceTemplate
from mldl.template.multi_instance_template import MultiInstanceTemplate

from mldl.importers.mask import vectorize_mask


@dataclass
class OpenImagesBBox:
	ImageID: str
	Source: str
	LabelName: str
	Confidence: float  # currently always 1
	XMin: float
	XMax: float
	YMin: float
	YMax: float
	IsOccluded: int
	IsTruncated: int
	IsGroupOf: int
	IsDepiction: int
	IsInside: int
	# the following are ignored.
	XClick1X: float
	XClick2X: float
	XClick3X: float
	XClick4X: float
	XClick1Y: float
	XClick2Y: float
	XClick3Y: float
	XClick4Y: float


@dataclass
class OpenImagesMaskMeta:
	MaskPath: str
	ImageID: str
	BoxID: str
	BoxXMin: float
	BoxXMax: float
	BoxYMin: float
	BoxYMax: float
	PredictedIoU: float
	# we don't care about this
	Clicks: str


@dataclass
class OpenImagesEntry:
	ImageID: str
	Source: str
	LabelName: str
	Confidence: float

	XMin: float
	XMax: float
	YMin: float
	YMax: float

	IsOccluded: int
	IsTruncated: int
	IsGroupOf: int
	IsDepiction: int
	IsInside: int

	MaskPath: Optional[str]


def normalize_name(name: str) -> str:
	return re.sub(r"[^a-z]+", "-", unidecode(name).lower()).strip("-")


def list_to_object(row: pd.Series) -> OpenImagesEntry:
	return [row[k] for k in get_type_hints(OpenImagesEntry)]


def bbox_signature(xmin: float, xmax: float, ymin: float, ymax: float) -> str:
	return f"{xmin:.2f} {xmax:.2f} {ymin:.2f} {ymax:.2f}"


def openimages_to_droplet(
	group: Tuple[str, Sequence[OpenImagesEntry]],
	masks_dir: str,
	image_storage_path: List[str],
	class_descriptions: Dict[str, str],
):
	image_id, entries = group
	classes = defaultdict(lambda: ClassAnnotation(instances=[], multi_instances=[]))
	for e in entries:
		class_name = class_descriptions[e.LabelName]
		bbox = Rectangle(Point(e.XMin, e.YMin), Point(e.XMax, e.YMax))
		mask = None
		if e.MaskPath:
			mask_path = path_join(masks_dir, e.MaskPath)
			mask = vectorize_mask(PIL.Image.open(mask_path))
		if e.IsGroupOf:
			classes[class_name].multi_instances.append(
				MultiInstance(bounding_box=bbox, segmentation=mask)
			)
		else:
			classes[class_name].instances.append(
				Instance(bounding_box=bbox, segmentation=mask)
			)
	return Annotation(
		image=Image(paths=[path_join(p, image_id + ".jpg") for p in image_storage_path]),
		classes=classes,
	)


def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("--csv", required=True, help="Path to root openimages csv")
	parser.add_argument(
		"--class-descriptions", required=True, help="Path to class descriptions csv"
	)
	parser.add_argument("--mask-meta", required=True, help="Path to maskdata csv")
	parser.add_argument(
		"--masks-dir",
		required=True,
		help="Path to root openimages masks directory, this must be local",
	)
	parser.add_argument(
		"--image-storage-path",
		required=True,
		action="append",
		help="The base path at which images are stored (probably an S3 URL)",
	)
	parser.add_argument(
		"--data-source", required=True, help="The name to use for this data source"
	)
	parser.add_argument(
		"--repartition", type=int, default=1024
	)
	parser.add_argument(
		"--normalize", type=bool, default=True
	)
	parser.add_argument("--output", default="out.tar.gz", help="output path")
	args = parser.parse_args()

	with open(args.class_descriptions, "r") as f:
		class_descriptions_list = [l.strip().split(",", 1) for l in f.readlines()]

	class_descriptions = dict(class_descriptions_list)
	class_descriptions = {k: normalize_name(v) if args.normalize else v for k, v in class_descriptions.items()}
	assert len(class_descriptions) == len(class_descriptions_list)

	cluster = LocalCluster(dashboard_address="0.0.0.0:8787")
	print("Dask dashboard available at:", cluster.dashboard_link)
	client = Client(cluster)

	bboxes = pd.read_csv(
		args.csv,
		dtype=OpenImagesBBox.__annotations__,
	)
	bboxes["BBoxSignature"] = bboxes.apply(
		lambda row: row["ImageID"]
		+ " "
		+ bbox_signature(row["XMin"], row["XMax"], row["YMin"], row["YMax"]),
		axis=1,
		meta=(None, "object"),
	)

	mask_metas = pd.read_csv(
		args.mask_meta,
		dtype=OpenImagesMaskMeta.__annotations__,
	)
	mask_metas["BBoxSignature"] = mask_metas.apply(
		lambda row: row["ImageID"]
		+ " "
		+ bbox_signature(
			row["BoxXMin"], row["BoxXMax"], row["BoxYMin"], row["BoxYMax"]
		),
		axis=1,
		meta=(None, "object"),
	)
	mask_metas = mask_metas.set_index("BBoxSignature")

	objects = (
		bboxes.join(mask_metas, on="BBoxSignature", rsuffix="_r")[
			list(OpenImagesEntry.__annotations__)
		]
		.fillna("")
		.to_bag()
		.map(lambda o: OpenImagesEntry(*o))
	)

	images = objects.groupby(lambda o: o.ImageID).repartition(args.repartition)

	annotations = images.map(
		lambda i: openimages_to_droplet(
			i, args.masks_dir, args.image_storage_path, class_descriptions
		)
	)

	template = AnnotationTemplate(
		classes = {
			c: ClassAnnotationTemplate(
				instances = InstanceTemplate(
					bounding_box = True,
					segmentation = True,
					attributes = { "occluded": { "occluded", "unoccluded" } }
				),
				multi_instances = MultiInstanceTemplate(
					bounding_box = True,
				)
			) for c in class_descriptions.values()
		}
	)

	write_output_tar(annotations, template, args.data_source, args.output)


if __name__ == "__main__":
	main()
