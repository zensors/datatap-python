from uuid import UUID, uuid4
import glob
import argparse
import os
import PIL.Image
import dask.bag
from dask.distributed import Client, LocalCluster
from os.path import join as path_join
from typing import Sequence, Dict, Union

from collections import defaultdict

from mldl.importers.base import VideoAnnotation, Video, Annotation, ClassAnnotation, get_image_digest, Image, Instance, Point, Rectangle, write_output_tar

HELP = """
Imports an MOT-format dataset.  Only works for bounding-box-based datasets.

To import a 2D MOT trainset:
python -m mldl.importers.mot \
	--base-path /path/to/mot/directory \
	--base-storage-path s3://path/to/mot/images \
	--data-source '2D MOT 2015 Training'
"""

class Mot2D2015Line:
	def __init__(self, line: str, img_width: int, img_height: int):
		L = line.strip().split(',')
		self.frame = int(L[0])
		self.file_name = str(self.frame).zfill(6) + ".jpg"
		self.id = int(L[1])
		self.bb_left = float(L[2]) / img_width
		self.bb_top = float(L[3]) / img_height
		self.bb_width = float(L[4]) / img_width
		self.bb_height = float(L[5]) / img_height
		self.confidence = float(L[6])
		# ignore x,y,z world coordinates

	def to_instance(self, id_map: Dict[int, UUID]) -> Instance:
		p1 = Point(self.bb_left, self.bb_top, clip = True)
		p2 = Point(self.bb_left + self.bb_width, self.bb_top + self.bb_height, clip = True)

		return Instance(
			bounding_box = Rectangle(p1, p2),
			identity = id_map[self.id]
		)

def lines_to_annotation(lines: Sequence[Mot2D2015Line], image_path: str, image_storage_path: str, id_map: Dict[int, UUID]) -> Annotation:
	# Combine sequence of lines for the same frame into a single annotation
	instances = []
	file_name = lines[0].file_name

	for line in lines:
		assert file_name == line.file_name
		if line.confidence > 0:
			instances.append(line.to_instance(id_map))

	image = Image(
		paths = [path_join(image_storage_path, file_name)],
		hash = get_image_digest(path_join(image_path, file_name))
	)
	return Annotation(
		image = image,
		classes = {"person": ClassAnnotation(instances = instances)}
	)

def compute_video_annotation(folder_path: str, base_storage_path: str) -> VideoAnnotation:
	id_map: Dict[int, UUID] = defaultdict(lambda: uuid4())
	image_path = path_join(folder_path, "img1")
	image_storage_path = path_join(base_storage_path, os.path.basename(folder_path))
	annotations_path = path_join(folder_path, "gt", "gt.txt")
	img_width, img_height = PIL.Image.open(path_join(folder_path, "det", "000001-acf.jpg")).size
	frames = (
		dask.bag.read_text(annotations_path, blocksize = "30MB")
			.filter(lambda line: len(line.strip()) > 0)
			.map(Mot2D2015Line, img_width = img_width, img_height = img_height)
			.groupby(lambda line: line.frame)
			.map(lambda pair: (pair[0], lines_to_annotation(pair[1], image_path, image_storage_path, id_map)))
			.compute()
	)
	frames = [frame_annotations for _, frame_annotations in sorted(frames, key = lambda f: f[0])]
	video = Video(paths = [], name = os.path.basename(folder_path))
	return VideoAnnotation(video = video, frames = frames)

def main():
	parser = argparse.ArgumentParser(description = HELP)
	parser.add_argument(
		"--base-path",
		required = True,
		help = "Path to the MOT directory",
	)
	parser.add_argument(
		"--base-storage-path",
		required = True,
		help = "Path to the stored MOT directory (probably an S3 URL)"
	)
	parser.add_argument(
		"--data-source",
		required = True,
		help = "The name to use for this data source"
	)
	parser.add_argument("--output", default = "out.tar.gz")
	parser.add_argument("--workers", type = int)
	args = parser.parse_args()

	cluster = LocalCluster(n_workers = args.workers, dashboard_address = "0.0.0.0:8787")
	print("Dask dashboard available at:", cluster.dashboard_link)
	client = Client(cluster)

	write_output_tar(
		dask.bag.from_sequence([
			compute_video_annotation(video_directory, args.base_storage_path)
			for video_directory
			in glob.glob(path_join(args.base_path, "train/*"))
		]),
		args.data_source,
		args.output
	)

if __name__ == "__main__":
	main()
