from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from os import unlink
from os.path import join as path_join
from os.path import realpath
from tempfile import TemporaryDirectory
from typing import (IO, Any, Dict, Generic, Iterable, List, Mapping, Optional,
                    Sequence, Set, Tuple, TypeVar, get_type_hints)
from uuid import UUID, uuid4

import mldl.droplet as droplet
from dask.bag.core import Bag
from mldl.droplet import CameraMetadata, Keypoint, PrideMetadata
from mldl.geometry import Mask, Point, Polygon, Rectangle
from mldl.template import AnnotationTemplate
from typing_extensions import TypedDict

T = TypeVar("T")

class SortedDictWriter(Generic[T]):
	file: IO[str]
	rows: List[T]
	field_names: Sequence[str]
	writer: csv.DictWriter

	def __init__(self, file_path: str, cls: Any): # this should be cls: Type[T], but it doesn't work
		self.file = open(file_path, "w")
		self.rows = []
		self.field_names = list(get_type_hints(cls).keys())
		self.writer = csv.DictWriter(self.file, fieldnames = self.field_names)

	def write(self, row: T):
		self.rows.append(row)

	def __enter__(self) -> SortedDictWriter[T]:
		return self

	def __exit__(self, _type: Any, _value: Any, _traceback: Any):
		if len(self.rows) > 0:
			self.writer.writeheader()
			self.writer.writerows(sorted(self.rows, key = lambda row: tuple(row[col] for col in self.field_names))) # type: ignore
			self.file.close()
		else:
			self.file.close()
			unlink(self.file.name)

###### Entities ######

# Data Graph

class InstanceIdentityCsv(TypedDict):
	uid: UUID

class InstanceCsv(TypedDict):
	uid: UUID
	bounding_box: Optional[str]
	segmentation: Optional[str]

class MultiInstanceCsv(TypedDict):
	uid: UUID
	bounding_box: Optional[str]
	segmentation: Optional[str]
	count: Optional[int]

class AnnotationCsv(TypedDict):
	uid: UUID
	mask: Optional[str]

class VideoAnnotationCsv(TypedDict):
	uid: UUID
	mask: Optional[str]

class ImageCsv(TypedDict):
	uid: UUID
	paths: Sequence[str]
	hash: Optional[str]

class VideoCsv(TypedDict):
	uid: UUID
	paths: Sequence[str]
	hash: Optional[str]
	name: Optional[str]

# Metadata graph

class DataSourceCsv(TypedDict):
	uid: UUID
	name: str

class LabelerCsv(TypedDict):
	uid: UUID

class CameraCsv(TypedDict):
	uid: UUID


###### Relationships ######

class InstanceIsClassCsv(TypedDict):
	class_name: str
	instance_uid: UUID

class InstanceHasKeypointCsv(TypedDict):
	class_name: str
	keypoint_name: str
	instance_uid: UUID
	point: str
	occluded: Optional[bool]

class InstanceHasAttributeCsv(TypedDict):
	class_name: str
	attribute_type: str
	attribute_value: str
	instance_uid: UUID

class InstanceIdentifiedByInstanceIdentityCsv(TypedDict):
	instance_identity: UUID
	instance_uid: UUID

class InstanceIdentityIsClassCsv(TypedDict):
	class_name: str
	instance_identity: UUID

class MultiInstanceIsClassCsv(TypedDict):
	class_name: str
	multi_instance_uid: UUID

class AnnotationFromDataSourceCsv(TypedDict):
	annotation_uid: UUID
	data_source_uid: UUID

class AnnotationAnnotatesImageCsv(TypedDict):
	annotation_uid: UUID
	image_uid: UUID

class AnnotationHasInstanceCsv(TypedDict):
	annotation_uid: UUID
	instance_uid: UUID

class AnnotationHasMultiInstanceCsv(TypedDict):
	annotation_uid: UUID
	multi_instance_uid: UUID

class AnnotationLabeledByLabelerCsv(TypedDict):
	labeler_uid: UUID
	annotation_uid: UUID
	at: str

class ImageTakenByCameraCsv(TypedDict):
	camera_uid: UUID
	image_uid: UUID
	at: str

class VideoTakenByCameraCsv(TypedDict):
	camera_uid: UUID
	video_uid: UUID
	at: str

class ImageIsFrameOfVideoCsv(TypedDict):
	video_uid: UUID
	image_uid: UUID
	index: int

class AnnotationIsFrameOfVideoAnnotationCsv(TypedDict):
	video_annotation_uid: UUID
	annotation_uid: UUID
	index: int

class VideoAnnotationFromDataSourceCsv(TypedDict):
	video_annotation_uid: UUID
	data_source_uid: UUID

class VideoAnnotationAnnotatesVideoCsv(TypedDict):
	video_annotation_uid: UUID
	video_uid: UUID

class CsvWriter():
	def __init__(self, prefix: str, uid: UUID, root_dir: str):
		for field_name, field_type in get_type_hints(type(self)).items():
			setattr(self, field_name, SortedDictWriter[Any](path_join(root_dir, f"{prefix}_{field_name}__{uid}.csv"), field_type.__args__[0]))

	def __enter__(self):
		for field_name in get_type_hints(type(self)):
			getattr(self, field_name).__enter__()

	def __exit__(self, error_type: Any, value: Any, traceback: Any):
		for field_name in get_type_hints(type(self)):
			getattr(self, field_name).__exit__(error_type, value, traceback)

class EntityCsvWriter(CsvWriter):
	annotation: SortedDictWriter[AnnotationCsv]
	image: SortedDictWriter[ImageCsv]
	instance: SortedDictWriter[InstanceCsv]
	multi_instance: SortedDictWriter[MultiInstanceCsv]
	video: SortedDictWriter[VideoCsv]
	video_annotation: SortedDictWriter[VideoAnnotationCsv]

	def __init__(self, uid: UUID, root_dir: str):
		super().__init__("ent", uid, root_dir)

class RelationshipCsvWriter(CsvWriter):
	annotation_from_data_source: SortedDictWriter[AnnotationFromDataSourceCsv]
	annotation_annotates_image: SortedDictWriter[AnnotationAnnotatesImageCsv]
	annotation_has_instance: SortedDictWriter[AnnotationHasInstanceCsv]
	annotation_has_multi_instance: SortedDictWriter[AnnotationHasMultiInstanceCsv]
	instance_is_class: SortedDictWriter[InstanceIsClassCsv]
	instance_has_keypoint: SortedDictWriter[InstanceHasKeypointCsv]
	multi_instance_is_class: SortedDictWriter[MultiInstanceIsClassCsv]
	instance_has_attribute: SortedDictWriter[InstanceHasAttributeCsv]
	annotation_labeled_by_labeler: SortedDictWriter[AnnotationLabeledByLabelerCsv]
	image_taken_by_camera: SortedDictWriter[ImageTakenByCameraCsv]
	video_taken_by_camera: SortedDictWriter[VideoTakenByCameraCsv]
	image_is_frame_of_video: SortedDictWriter[ImageIsFrameOfVideoCsv]
	annotation_is_frame_of_video_annotation: SortedDictWriter[AnnotationIsFrameOfVideoAnnotationCsv]
	instance_identified_by_instance_identity: SortedDictWriter[InstanceIdentifiedByInstanceIdentityCsv]
	video_annotation_from_data_source: SortedDictWriter[VideoAnnotationFromDataSourceCsv]
	video_annotation_annotates_video: SortedDictWriter[VideoAnnotationAnnotatesVideoCsv]

	def __init__(self, uid: UUID, root_dir: str):
		super().__init__("rel", uid, root_dir)

class MldlCsvWriter:
	entity: EntityCsvWriter
	relationship: RelationshipCsvWriter

	def __init__(self, root_dir: str):
		self.uid = uuid4()
		self.entity = EntityCsvWriter(self.uid, root_dir)
		self.relationship = RelationshipCsvWriter(self.uid, root_dir)

	def __enter__(self) -> MldlCsvWriter:
		self.entity.__enter__()
		self.relationship.__enter__()
		return self

	def __exit__(self, type: Any, value: Any, traceback: Any):
		self.entity.__exit__(type, value, traceback)
		self.relationship.__exit__(type, value, traceback)







class Instance(droplet.Instance):
	uid: UUID

	def __init__(
		self,
		*,
		bounding_box: Rectangle,
		segmentation: Optional[Mask] = None,
		keypoints: Optional[Mapping[str, Optional[Keypoint]]] = None,
		attributes: Optional[Mapping[str, str]] = None,
		identity: Optional[UUID] = None
	):
		super().__init__(bounding_box = bounding_box, segmentation = segmentation, keypoints = keypoints, attributes = attributes, identity = identity)
		self.uid = uuid4()

	def write_csv(self, writer: MldlCsvWriter, class_name: str) -> None:
		writer.entity.instance.write({
			"uid": self.uid,
			"bounding_box": json.dumps(self.bounding_box.to_json()),
			"segmentation": json.dumps(self.segmentation.to_json()) if self.segmentation is not None else None
		})
		writer.relationship.instance_is_class.write({ "instance_uid": self.uid, "class_name": class_name })

		if self.keypoints is not None:
			for keypoint_name, keypoint in self.keypoints.items():
				if keypoint is not None:
					writer.relationship.instance_has_keypoint.write({
						"instance_uid": self.uid,
						"class_name": class_name,
						"keypoint_name": keypoint_name,
						"point": json.dumps(keypoint.point.to_json()),
						"occluded": keypoint.occluded
					})

		if self.attributes is not None:
			for attribute_type, attribute_value in self.attributes.items():
				writer.relationship.instance_has_attribute.write({
					"class_name": class_name,
					"attribute_type": attribute_type,
					"attribute_value": attribute_value,
					"instance_uid": self.uid
				})

		if self.identity is not None:
			writer.relationship.instance_identified_by_instance_identity.write({
				"instance_uid": self.uid,
				"instance_identity": self.identity
			})

	def add_shared_entities(self, entities: SharedAnnotationEntities, class_name: str) -> None:
		if self.identity is not None:
			entities.instance_identities[self.identity] = class_name

class MultiInstance(droplet.MultiInstance):
	uid: UUID

	def __init__(self, *, bounding_box: Rectangle, segmentation: Optional[Mask] = None, count: Optional[int] = None):
		super().__init__(bounding_box = bounding_box, segmentation = segmentation, count = count)
		self.uid = uuid4()

	def write_csv(self, writer: MldlCsvWriter, class_name: str) -> None:
		writer.entity.multi_instance.write({
			"uid": self.uid,
			"count": self.count,
			"bounding_box": json.dumps(self.bounding_box.to_json()),
			"segmentation": json.dumps(self.segmentation.to_json()) if self.segmentation is not None else None
		})
		writer.relationship.multi_instance_is_class.write({ "multi_instance_uid": self.uid, "class_name": class_name })

class Image(droplet.Image):
	uid: UUID

	def __init__(self, *, paths: Sequence[str], hash: Optional[str] = None, camera_metadata: Optional[CameraMetadata] = None):
		super().__init__(paths = paths, hash = hash, camera_metadata = camera_metadata)
		self.uid = uuid4()

	def write_csv(self, writer: MldlCsvWriter, video_annotation_info: Optional[Tuple[VideoAnnotation, int]] = None) -> None:
		writer.entity.image.write({ "uid": self.uid, "paths": ",".join(self.paths), "hash": self.hash })

		if self.camera_metadata is not None:
			writer.relationship.image_taken_by_camera.write({
				"camera_uid": self.camera_metadata.camera_uid,
				"image_uid": self.uid,
				"at": self.camera_metadata.taken_at.isoformat()
			})

		if video_annotation_info is not None:
			video_annotation, index = video_annotation_info
			writer.relationship.image_is_frame_of_video.write({
				"video_uid": video_annotation.video.uid,
				"image_uid": self.uid,
				"index": index
			})

	def add_shared_entities(self, entities: SharedAnnotationEntities) -> None:
		if self.camera_metadata is not None:
			entities.cameras.add(self.camera_metadata.camera_uid)

class ClassAnnotation(droplet.ClassAnnotation):
	instances: Sequence[Instance]
	multi_instances: Sequence[MultiInstance]

	def __init__(self, *, instances: Sequence[Instance], multi_instances: Sequence[MultiInstance] = []):
		super().__init__(instances = instances, multi_instances = multi_instances)

	def write_csv(self, writer: MldlCsvWriter, class_name: str) -> None:
		for instance in self.instances:
			instance.write_csv(writer, class_name)

		for multi_instance in self.multi_instances:
			multi_instance.write_csv(writer, class_name)

	def add_shared_entities(self, entities: SharedAnnotationEntities, class_name: str) -> None:
		for instance in self.instances:
			instance.add_shared_entities(entities, class_name)

class Annotation(droplet.Annotation):
	uid: UUID
	image: Image
	classes: Mapping[str, ClassAnnotation]
	mask: Optional[Mask]

	def __init__(self, *, image: Image, classes: Mapping[str, ClassAnnotation], mask: Optional[Mask] = None):
		super().__init__(image = image, classes = classes, mask = mask)
		self.uid = uuid4()

	def write_csv(self, writer: MldlCsvWriter, data_source_uid: UUID, video_annotation_info: Optional[Tuple[VideoAnnotation, int]] = None) -> None:
		writer.entity.annotation.write({
			"uid": self.uid,
			"mask": json.dumps(self.mask.to_json()) if self.mask is not None else None
		})
		writer.relationship.annotation_from_data_source.write({ "annotation_uid": self.uid, "data_source_uid": data_source_uid })

		self.image.write_csv(writer, video_annotation_info)
		writer.relationship.annotation_annotates_image.write({ "annotation_uid": self.uid, "image_uid": self.image.uid })

		for class_name, class_annotation in self.classes.items():
			class_annotation.write_csv(writer, class_name)

			for instance in class_annotation.instances:
				writer.relationship.annotation_has_instance.write({ "annotation_uid": self.uid, "instance_uid": instance.uid })

			for multi_instance in class_annotation.multi_instances:
				writer.relationship.annotation_has_multi_instance.write({ "annotation_uid": self.uid, "multi_instance_uid": multi_instance.uid })

		if video_annotation_info is not None:
			video_annotation, index = video_annotation_info
			writer.relationship.annotation_is_frame_of_video_annotation.write({
				"video_annotation_uid": video_annotation.uid,
				"annotation_uid": self.uid,
				"index": index
			})

	def add_shared_entities(self, entities: SharedAnnotationEntities) -> None:
		self.image.add_shared_entities(entities)

		for class_name, class_annotation in self.classes.items():
			class_annotation.add_shared_entities(entities, class_name)

class Video(droplet.Video):
	uid: UUID

	def __init__(
		self,
		paths: Sequence[str],
		hash: Optional[str] = None,
		name: Optional[str] = None,
		camera_metadata: Optional[CameraMetadata] = None
	):
		super().__init__(paths = paths, hash = hash, name = name, camera_metadata = camera_metadata)
		self.uid = uuid4()

	def write_csv(self, writer: MldlCsvWriter) -> None:
		writer.entity.video.write({ "uid": self.uid, "paths": ",".join(self.paths), "hash": self.hash, "name": self.name })

		if self.camera_metadata is not None:
			writer.relationship.video_taken_by_camera.write({
				"camera_uid": self.camera_metadata.camera_uid,
				"video_uid": self.uid,
				"at": self.camera_metadata.taken_at.isoformat()
			})

class VideoAnnotation(droplet.VideoAnnotation):
	uid: UUID
	video: Video
	frames: Sequence[Annotation]
	mask: Optional[Mask]

	def __init__(self, video: Video, frames: Sequence[Annotation], mask: Optional[Mask] = None):
		super().__init__(video = video, frames = frames, mask = mask)
		self.uid = uuid4()

	def write_csv(self, writer: MldlCsvWriter, data_source_uid: UUID) -> None:
		writer.entity.video_annotation.write({
			"uid": self.uid,
			"mask": json.dumps(self.mask.to_json()) if self.mask is not None else None
		})
		writer.relationship.video_annotation_from_data_source.write({ "video_annotation_uid": self.uid, "data_source_uid": data_source_uid })

		self.video.write_csv(writer)
		writer.relationship.video_annotation_annotates_video.write({ "video_annotation_uid": self.uid, "video_uid": self.video.uid })

		for frame_index, frame in enumerate(self.frames):
			frame.write_csv(writer, data_source_uid, (self, frame_index))

	def add_shared_entities(self, entities: SharedAnnotationEntities) -> None:
		for frame in self.frames:
			frame.add_shared_entities(entities)


class PrideAnnotation(droplet.PrideAnnotation, Annotation):
	def __init__(self, *, image: Image, classes: Mapping[str, ClassAnnotation], pride_metadata: PrideMetadata, mask: Optional[Mask] = None):
		super().__init__(image = image, classes = classes, mask = mask, pride_metadata = pride_metadata)

	def write_csv(self, writer: MldlCsvWriter, data_source_uid: UUID, video_annotation_info: Optional[Tuple[VideoAnnotation, int]] = None) -> None:
		Annotation.write_csv(self, writer, data_source_uid, video_annotation_info)
		writer.relationship.annotation_labeled_by_labeler.write({
			"annotation_uid": self.uid,
			"labeler_uid": self.pride_metadata.labeler_uid,
			"at": self.pride_metadata.labeled_at.isoformat()
		})

	def add_shared_entities(self, entities: SharedAnnotationEntities) -> None:
		super().add_shared_entities(entities)
		entities.labelers.add(self.pride_metadata.labeler_uid)


class SharedAnnotationEntities:
	labelers: Set[UUID]
	cameras: Set[UUID]
	instance_identities: Dict[UUID, str]

	def __init__(
		self,
		labelers: Set[UUID] = set(),
		cameras: Set[UUID] = set(),
		instance_identities: Dict[UUID, str] = dict()
	):
		self.labelers = labelers
		self.cameras = cameras
		self.instance_identities = instance_identities

	def merge(self, other: SharedAnnotationEntities) -> SharedAnnotationEntities:
		return SharedAnnotationEntities(
			labelers = self.labelers | other.labelers,
			cameras = self.cameras | other.cameras,
			instance_identities = { **self.instance_identities, **other.instance_identities }
		)

def dump_csv_for_partition(annotations: Iterable[Annotation], path: str, data_source_uid: UUID) -> Sequence[SharedAnnotationEntities]:
	shared_entities = SharedAnnotationEntities()

	with MldlCsvWriter(path) as writer:
		for annotation in annotations:
			annotation.write_csv(writer, data_source_uid)
			annotation.add_shared_entities(shared_entities)

	return [shared_entities]

def write_output_tar(
	annotations: Bag, # actually Bag[Annotation] (TODO: reintroduce video annotations)
	template: AnnotationTemplate,
	data_source_name: str,
	out_path: str,
	data_source_uid: Optional[UUID] = None
) -> None:
	if not out_path.endswith(".tar.gz"):
		raise Exception("Output file should be a *.tar.gz")

	data_source_uid = data_source_uid if data_source_uid is not None else uuid4()
	real_out_path = realpath(out_path)

	with TemporaryDirectory(prefix="mldl-import-") as tmpdir:
		with open(path_join(tmpdir, "template.json"), "w") as template_file:
			json.dump(template.to_json(), template_file)

		shared_entities: SharedAnnotationEntities = (
			annotations.map_partitions(dump_csv_for_partition, path = tmpdir, data_source_uid = data_source_uid) # type: ignore
				.fold(lambda a, b: a.merge(b)) # type: ignore
				.compute() # type: ignore
		)

		with SortedDictWriter[DataSourceCsv](path_join(tmpdir, "ent_data_source.csv"), DataSourceCsv) as data_source_writer:
			data_source_writer.write({ "name": data_source_name, "uid": data_source_uid })

		with SortedDictWriter[LabelerCsv](path_join(tmpdir, "ent_labeler.csv"), LabelerCsv) as labeler_writer:
			for labeler_uid in shared_entities.labelers:
				labeler_writer.write({ "uid": labeler_uid })

		with SortedDictWriter[CameraCsv](path_join(tmpdir, "ent_camera.csv"), CameraCsv) as camera_writer:
			for camera_uid in shared_entities.cameras:
				camera_writer.write({ "uid": camera_uid })

		with SortedDictWriter[InstanceIdentityCsv](path_join(tmpdir, "ent_instance_identity.csv"), InstanceIdentityCsv) as instance_identity_writer:
			with SortedDictWriter[InstanceIdentityIsClassCsv](path_join(tmpdir, "rel_instance_identity_is_class.csv"), InstanceIdentityIsClassCsv) as instance_identity_is_class_writer:
				for instance_identity, class_name in shared_entities.instance_identities.items():
					instance_identity_writer.write({ "uid": instance_identity })
					instance_identity_is_class_writer.write({ "instance_identity": instance_identity, "class_name": class_name })

		subprocess.run(f"tar -czf {real_out_path} *", cwd = tmpdir, shell = True)

	print(f"Wrote output to {real_out_path}.  You should extract this to somewhere in the Neo4j import directory on the server and then run [python -m mldl.importers.server].")

def get_image_digest(file_path: str) -> str:
	h = hashlib.sha256()

	with open(file_path, "rb") as file:
		while True:
			# Reading is buffered, so we can read smaller chunks.
			chunk = file.read(h.block_size)
			if not chunk:
				break
			h.update(chunk)

	# 1220 is the multihash identifier for SHA256
	return "1220" + h.hexdigest()
