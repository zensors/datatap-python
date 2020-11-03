import argparse
import sys
from os import environ, path
from typing import Sequence, Tuple

import dask.bag
from dask.distributed import Client, LocalCluster
import PIL.Image

from mldl.importers.base import Annotation, ClassAnnotation, Image, Instance, Point, Rectangle, get_image_digest, write_output_tar

WiderfaceFace = Tuple[int, int, int, int, int, int, int, int, int, int]
# x, y, width, height, blur, expression, illumination, invalid, occlusion, pose

WiderfaceAnnotation = Tuple[str, Sequence[WiderfaceFace]]
# image_path, faces

def widerface_annotation_to_face_annotations(path):
	with open(path, "r") as infile:
		while True:
			image_path = infile.readline().strip()

			if image_path == "":
				return

			face_count = int(infile.readline())

			if face_count > 0:
				faces = [tuple(map(int, infile.readline().split(" ")[:10])) for i in range(face_count)]
			else:
				faces = []
				infile.readline() # for some reason the format has a line with 0s when there aren't any faces

			yield (image_path, faces)

def widerface_bb_to_droplet(widerface_bb: Tuple[int, int, int, int], im_width: int, im_height: int) -> Rectangle:
	x, y, w, h = widerface_bb
	return Rectangle(
		p1 = Point(x = x / im_width, y = y / im_height),
		p2 = Point(x = (x + w) / im_width, y = (y + h) / im_height)
	)

def is_valid_face(face: WiderfaceFace, im_width: int, im_height: int) -> bool:
	x, y, w, h, blur, expression, illumination, invalid, occlusion, pose = face

	# Some faces are marked as invalid.
	# Others may have no area or may appear outside of the image entirely.
	return invalid == 0 and 0 <= x and x + w <= im_width and 0 <= y and y + h < im_height and w > 0 and h > 0

def widerface_annotation_to_droplet(annotation: WiderfaceAnnotation, images_dir: str) -> Annotation:
	image_path, faces = annotation

	image_path = path.join(images_dir, image_path)
	im = PIL.Image.open(image_path)
	im_width, im_height = im.size
	im.close()

	return Annotation(
		image = Image(paths = [image_path], hash = get_image_digest(image_path)),
		classes = {
			"face": ClassAnnotation(
				instances = [
					Instance(bounding_box = widerface_bb_to_droplet(face[:4], im_width, im_height))
					for face in faces
					if is_valid_face(face, im_width, im_height)
				]
			)
		}
	)

def main(argv):
	parser = argparse.ArgumentParser()
	parser.add_argument(
		"--annotations",
		required = True,
		help="Path to annotations .txt file"
	)
	parser.add_argument(
		"--images",
		required = True,
		help = "Path to the image directory",
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
	parser.add_argument("--workers", type=int)
	args = parser.parse_args()

	cluster = LocalCluster(n_workers = args.workers, dashboard_address = "0.0.0.0:8787")
	print("Dask dashboard available at:", cluster.dashboard_link)
	client = Client(cluster)

	face_annotations = list(widerface_annotation_to_face_annotations(args.annotations))
	annotations = dask.bag.from_sequence([
		widerface_annotation_to_droplet(annotation, args.images)
		for annotation in face_annotations
	])

	write_output_tar(annotations, args.data_source, args.output)

if __name__ == "__main__":
	main(sys.argv)
