import argparse
import sys
from enum import Enum
from glob import glob
from os.path import basename, dirname
from os.path import join as path_join
from os.path import splitext
from typing import Iterator, List, Tuple, cast

import dask.bag
import PIL.Image
from dask.bag.core import Bag
from mldl.template.annotation_template import AnnotationTemplate
from mldl.template.class_annotation_template import ClassAnnotationTemplate
from mldl.template.instance_template import InstanceTemplate
import shapely.geometry
from dask.distributed import Client, LocalCluster
from mldl.importers.base import (Annotation, ClassAnnotation, Image, Instance,
                                 Mask, MultiInstance, Point, Polygon,
                                 Rectangle, get_image_digest, write_output_tar)
from shapely.geometry.polygon import LinearRing
from toolz import concat

FULL_MASK = shapely.geometry.Polygon([(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)])

"""
How to run this:

python -m mldl.importers.widerperson ~/widerperson/ \
	--output=./out/widerperson/*.image.jsonl.gz
"""


class WiderPersonClass(Enum):
	PERSON = 1
	RIDERS = 2
	PERSON_OCCLUDED = 3
	IGNORE = 4
	CROWD = 5

def widerperson_bb_to_droplet(widerface_bb: Tuple[int, int, int, int], im_width: int, im_height: int) -> Rectangle:
	x1, y1, x2, y2 = widerface_bb
	return Rectangle(
		p1 = Point(x = x1 / im_width, y = y1 / im_height),
		p2 = Point(x = x2 / im_width, y = y2 / im_height)
	)

def widerperson_to_droplet(widerperson_annotation: str, annotation_path: str, image_storage_path: str) -> Annotation:
	image_dir = path_join(dirname(annotation_path), "..", "Images")
	image_name = splitext(basename(annotation_path))[0]
	image_path_abs = path_join(image_dir, image_name)
	image_hash = get_image_digest(image_path_abs)
	image = PIL.Image.open(image_path_abs)
	w, h = image.size
	image.close()

	instances: List[Instance] = []
	multi_instances: List[MultiInstance] = []
	shapely_mask = FULL_MASK

	for line in widerperson_annotation.split("\n")[1:]:
		line = line.strip()
		if len(line) == 0:
			continue
		data = cast(Tuple[int, int, int, int, int], tuple(map(int, line.split(" "))))
		wpclass = WiderPersonClass(data[0])
		box = widerperson_bb_to_droplet(cast(Tuple[int, int, int, int], data[1:]), w, h)

		try: # ignore bad bounding boxes
			box.assert_valid()
		except:
			continue

		if wpclass == WiderPersonClass.IGNORE:
			shapely_mask = shapely_mask.difference(box.to_shapely()) # type: ignore
		elif wpclass == WiderPersonClass.CROWD:
			multi_instances.append(MultiInstance(bounding_box = box))
		else:
			instances.append(
				Instance(
					bounding_box = box,
					attributes = { "occluded": "occluded" if wpclass == WiderPersonClass.PERSON_OCCLUDED else "unoccluded" }
				)
			)

	mask = None
	if shapely_mask is not FULL_MASK:
		assert shapely_mask.is_valid

		shapely_polygons = []

		if isinstance(shapely_mask, shapely.geometry.MultiPolygon):
			shapely_polygons = list(shapely_mask.geoms)
		elif isinstance(shapely_mask, shapely.geometry.Polygon):
			shapely_polygons = [shapely_mask]
		else:
			raise Exception("Expected a polygon or multipolygon")

		polygons = cast(Iterator[LinearRing], concat([[p.exterior] + list(p.interiors) for p in shapely_polygons]))
		mask = Mask(polygons = [Polygon(points = [Point(x = x, y = y) for (x, y) in poly.coords]) for poly in polygons])

	return Annotation(
		image = Image(
			paths = [path_join(image_storage_path, image_name)],
			hash = image_hash
		),
		mask = mask,
		classes = {
			"person": ClassAnnotation(instances = instances, multi_instances = multi_instances)
		}
	)

def load_file(file_name: str) -> Tuple[str, str]:
	with open(file_name, "r") as f:
		return (f.read(), file_name)

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument(
		"--widerperson-dir",
		required = True,
		help="Path to root widerperson directory"
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
	parser.add_argument("--output", default="out/*.jsonl", help="output path")
	parser.add_argument("--workers", type=int)
	args = parser.parse_args()

	cluster = LocalCluster(n_workers = args.workers, dashboard_address = "0.0.0.0:8787")
	print("Dask dashboard available at:", cast(str, cluster.dashboard_link)) # type: ignore
	client = Client(cluster)

	annotations: Bag = (
		dask.bag.from_sequence(glob(path_join(args.widerperson_dir, "Annotations/*.txt"))) # type: ignore
			.repartition(12) # type: ignore
			.map(load_file) # type: ignore
			.map(lambda file: widerperson_to_droplet(file[0], file[1], args.image_storage_path)) # type: ignore
	)

	template = AnnotationTemplate(
		classes = {
			"person": ClassAnnotationTemplate(
				instances = InstanceTemplate(
					bounding_box = True,
					attributes = { "occluded": { "occluded", "unoccluded" } }
				)
			)
		}
	)

	write_output_tar(annotations, template, args.data_source, args.output)


if __name__ == "__main__":
	main()
