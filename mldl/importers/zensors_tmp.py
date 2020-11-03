import argparse
import sys
from ast import literal_eval
from csv import DictReader
from typing import Optional, Sequence, Tuple
from uuid import UUID

import dask.bag
from dask.distributed import Client, LocalCluster
from dateutil.parser import isoparse
from mldl.importers.base import (Annotation, CameraMetadata, ClassAnnotation,
                                 Image, Instance, Mask, Point, Polygon,
                                 Rectangle, write_output_tar)
from mldl.template import (AnnotationTemplate, InstanceTemplate,
                           ClassAnnotationTemplate)

HELP = """
To use:

1. Dump data from timescale using something like this:

	BEGIN;

	CREATE TEMPORARY TABLE export ON COMMIT DROP AS
	SELECT
		sl.sensor_id,
		sl.event_time,
		sl.labeler_id,
		coalesce(sl.bounding_boxes, array[]::box[]) AS bounding_boxes,
		sp.value->>0 as image_url
	FROM sensor_label sl
		JOIN stream_point sp
			ON sl.event_time = sp.event_time
	WHERE sl.sensor_id = <the sensor in question>
		AND sp.stream_id = <the device uid corresponding to the sensor>
		AND sl.labeler_type = 'WORKER'
		AND NOT EXISTS (SELECT * FROM sensor_label_mldl_import slmi WHERE slmi.sensor_id = sl.sensor_id AND slmi.event_time = sl.event_time AND slmi.labeler_id = sl.labeler_id::uuid);

	\copy (SELECT * FROM export) to '/tmp/mldl-export.csv' csv;

	INSERT INTO sensor_label_mldl_import (sensor_id, event_time, labeler_id)
	SELECT sensor_id, event_time, labeler_id::uuid
	FROM export;

	COMMIT;

2. Run the following

python -m mldl.importers.zensors_tmp \
	--labels="path/to/labels.csv" \
	--sensor-uid="<uid of the sensor>" \
	--sensor-name="<name for the sensor>" \
	--class-name="<class being labeled>" \
	--camera-uid="<uid of the camera>" \
	--mask="<the sensor's mask>"

Note: this does not work for yes-no data
"""

def pg_point_to_droplet(pt: Tuple[float, float]) -> Point:
	x, y = pt
	return Point(x, y, clip = True)

def pg_box_to_droplet(box: Tuple[Tuple[float, float], Tuple[float, float]]) -> Optional[Rectangle]:
	p1, p2 = box

	try:
		return Rectangle(pg_point_to_droplet(p1), pg_point_to_droplet(p2), normalize = True)
	except:
		return None

def pg_polygon_to_droplet(poly: Sequence[Tuple[float, float]]) -> Polygon:
	return Polygon([pg_point_to_droplet(pt) for pt in poly])

def crowd_to_droplet(crowd_label: dict, class_name: str, mask: Mask, camera_uid: str) -> Annotation:
	box_strs: Sequence[str] = literal_eval(crowd_label["bounding_boxes"].replace("{", "[").replace("}", "]"))
	boxes_with_invalid = [pg_box_to_droplet(literal_eval(box_str)) for box_str in box_strs]
	boxes = [box for box in boxes_with_invalid if box is not None]

	return Annotation(
		image = Image(
			paths = ["s3://zensors-images" + crowd_label["image_url"]],
			camera_metadata = CameraMetadata(
				camera_uid = UUID(camera_uid),
				taken_at = isoparse(crowd_label["event_time"])
			)
		),
		mask = mask,
		classes = {
			class_name: ClassAnnotation(
				instances = [Instance(bounding_box = box) for box in boxes]
			)
		}
	)

def main(argv):
	parser = argparse.ArgumentParser(description=HELP)
	parser.add_argument(
		"--labels",
		required = True,
		help = "Path to the labels CSV file"
	)
	parser.add_argument(
		"--sensor-uid",
		required=True,
		help="The uid of the sensor whose data is being imported"
	)
	parser.add_argument(
		"--sensor-name",
		required=True,
		help="The name of the sensor being imported"
	)
	parser.add_argument(
		"--camera-uid",
		required=True,
		help="The uid of the camera corresponding to the sensor being imported"
	)
	parser.add_argument(
		"--mask",
		help="The crop area of the sensor being imported"
	)
	parser.add_argument(
		"--class-name",
		required=True,
		help="The name of the class being labeled"
	)
	parser.add_argument("--output", default="out.tar.gz")
	parser.add_argument("--workers", default=4, type=int)

	args = parser.parse_args()
	run(
		n_workers = args.workers,
		labels = args.labels,
		class_name = args.class_name,
		camera_uid = args.camera_uid,
		data_source_name = args.sensor_name,
		output = args.output,
		mask = args.mask,
		sensor_uid = UUID(args.sensor_uid)
	)

def run(
	*,
	n_workers: int,
	labels: str,
	class_name: str,
	camera_uid: str,
	data_source_name: str,
	output: str,
	mask: Optional[str] = None,
	sensor_uid: UUID
):
	cluster = LocalCluster(n_workers = n_workers, dashboard_address = "0.0.0.0:8787")
	print("Dask dashboard available at:", cluster.dashboard_link)
	client = Client(cluster)

	with open(labels) as infile:
		reader = DictReader(infile)
		data = list(reader)

	crowd_labels = dask.bag.from_sequence(data, partition_size = 500)
	annotations = crowd_labels.map(
		crowd_to_droplet,
		class_name = class_name,
		mask = Mask([pg_polygon_to_droplet(literal_eval(mask))]) if mask is not None else None,
		camera_uid = camera_uid
	)
	template = AnnotationTemplate(
		classes = {
			class_name: ClassAnnotationTemplate(
				instances = InstanceTemplate(bounding_box = True)
			)
		}
	)
	write_output_tar(annotations, template, data_source_name, output, data_source_uid = sensor_uid)

	client.close()
	cluster.close()


if __name__ == "__main__":
	main(sys.argv)
