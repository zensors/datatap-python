import argparse
import tarfile
from os import environ
from os.path import join as path_join
from time import sleep
from typing import Any, List, Tuple

import dask.bag
from dask.delayed import delayed
from dask.distributed import Client, LocalCluster
from neo4j import GraphDatabase
from neo4j.exceptions import TransientError

NEO4J_PROTOCOL = environ.get("MLDL_NEO4J_PROTOCOL", "neo4j")
NEO4J_HOST = environ.get("MLDL_NEO4J_HOST", "localhost")
NEO4J_PORT = environ.get("MLDL_NEO4J_PORT", "7687")
NEO4J_USER = environ.get("MLDL_NEO4J_USER", "neo4j")
NEO4J_PASS = environ.get("MLDL_NEO4J_PASS", "neo4j")

HELP = """
Runs the necessary commands on the server to import a set of annotations (dumped into the CSV format) into MLDL.

Usage: python -m mldl.importers.coco <path_to_annotation_directory>
"""

ENTITY_GLOBS: List[Tuple[str, str]] = [
	("ent_annotation", "MERGE (anno:Annotation { uid: line.uid }) ON CREATE SET anno.mask = zensors.geometry.maskFromDroplet(line.mask)"),
	("ent_camera", "MERGE (camera:Camera { uid: line.uid })"),
	("ent_image", "MERGE (image:Image { uid: line.uid }) ON CREATE SET image.paths = split(line.paths, ','), image.hash = line.hash"),
	("ent_instance", "MERGE (instance:Instance { uid: line.uid }) ON CREATE SET instance.boundingBox = zensors.geometry.rectangleFromDroplet(line.bounding_box), instance.segmentation = zensors.geometry.maskFromDroplet(line.segmentation)"),
	("ent_multi_instance", "MERGE (multiInstance:MultiInstance { uid: line.uid }) ON CREATE SET multiInstance.boundingBox = zensors.geometry.rectangleFromDroplet(line.bounding_box), multiInstance.segmentation = zensors.geometry.maskFromDroplet(line.segmentation), multiInstance.count = toInteger(line.count)"),
	("ent_video_annotation", "MERGE (va:VideoAnnotation { uid: line.uid }) ON CREATE SET va.mask = zensors.geometry.maskFromDroplet(line.mask)"),
	("ent_video", "MERGE (video:Video { uid: line.uid }) ON CREATE SET video.paths = split(coalesce(line.paths, ''), ','), video.hash = line.hash, video.name = line.name"),
]

RELATIONSHIP_GLOBS: List[Tuple[str, str]] = [
	("ent_annotation", "MATCH (annotation:Annotation { uid: line.uid }) MATCH (template:AnnotationTemplate { uid: $template_uid }) CREATE (annotation)-[:DESCRIBED_BY]->(template)"),
	("rel_annotation_from_data_source", "MATCH (annotation:Annotation { uid: line.annotation_uid }) MATCH (data_source:DataSource { uid: line.data_source_uid }) MERGE (annotation)-[:FROM_DATA_SOURCE]->(data_source)"),
	("rel_annotation_annotates_image", "MATCH (annotation:Annotation { uid: line.annotation_uid }) MATCH (image:Image { uid: line.image_uid }) MERGE (annotation)-[:ANNOTATES_IMAGE]->(image)"),
	("rel_annotation_has_instance", "MATCH (annotation:Annotation { uid: line.annotation_uid }) MATCH (instance:Instance { uid: line.instance_uid }) MERGE (annotation)-[:HAS_INSTANCE]->(instance)"),
	("rel_annotation_has_multi_instance", "MATCH (annotation:Annotation { uid: line.annotation_uid }) MATCH (multiInstance:MultiInstance { uid: line.multi_instance_uid }) MERGE (annotation)-[:HAS_multi_instance]->(multiInstance)"),
	("rel_instance_is_class", "MATCH (instance:Instance { uid: line.instance_uid }) MATCH (class:Class { name: line.class_name }) MERGE (instance)-[:IS_INSTANCE_OF]->(class)"),
	("rel_instance_has_keypoint", "MATCH (instance:Instance { uid: line.instance_uid }) MATCH (kpn:KeypointNode { name: line.keypoint_name })-[:IS_KEYPOINT_NODE_OF]->(:Class { name: line.class_name }) MERGE (instance)-[r:HAS_KEYPOINT]->(kpn) ON CREATE SET r.point = zensors.geometry.pointFromDroplet(line.point), r.occluded = toBoolean(line.occluded)"),
	("rel_instance_has_attribute", "MATCH (instance:Instance { uid: line.instance_uid }) MATCH (attr:Attribute { name: line.attribute_value })-[:IS_OF_TYPE]->(:AttributeType { name: line.attribute_type })-[:IS_ATTRIBUTE_OF]->(:Class { name: line.class_name }) MERGE (instance)-[:HAS_ATTRIBUTE]->(attr)"),
	("rel_multi_instance_is_class", "MATCH (multiInstance:MultiInstance { uid: line.multi_instance_uid }) MATCH (class:Class { name: line.class_name }) MERGE (multiInstance)-[:IS_multi_instance_OF]->(class)"),
	("rel_annotation_labeled_by_labeler", "MATCH (annotation:Annotation { uid: line.annotation_uid }) MATCH (labeler:Labeler { uid: line.labeler_uid }) MERGE (annotation)-[r:LABELED_BY]->(labeler) ON CREATE SET r.at = datetime(line.at)"),
	("rel_image_taken_by_camera", "MATCH (camera:Camera { uid: line.camera_uid }) MATCH (image:Image { uid: line.image_uid }) MERGE (image)-[r:TAKEN_BY]->(camera) ON CREATE SET r.at = datetime(line.at)"),
	("rel_video_taken_by_camera", "MATCH (camera:Camera { uid: line.camera_uid }) MATCH (video:Video { uid: line.video_uid }) MERGE (video)-[r:TAKEN_BY]->(camera) ON CREATE SET r.at = datetime(line.at)"),
	("rel_image_is_frame_of_video", "MATCH (video:Video { uid: line.video_uid }) MATCH (image:Image { uid: line.image_uid }) MERGE (image)-[r:IS_FRAME_OF]->(video) ON CREATE SET r.index = toInteger(line.index)"),
	("rel_annotation_is_frame_of_video_annotation", "MATCH (va:VideoAnnotation { uid: line.video_annotation_uid }) MATCH (anno:Annotation { uid: line.annotation_uid }) MERGE (anno)-[r:IS_FRAME_OF]->(va) ON CREATE SET r.index = toInteger(line.index)"),
	("rel_instance_identified_by_instance_identity", "MATCH (ident:InstanceIdentity { uid: line.instance_identity }) MATCH (inst:Instance { uid: line.instance_uid }) MERGE (inst)-[:IS_IDENTIFIED_BY]->(ident)"),
	("rel_identity_is_class", "MATCH (class:Class { name: line.class_name }) MATCH (ident:InstanceIdentity { uid: line.instance_identity }) MERGE (ident)-[:IS_INSTANCE_IDENTITY_OF]->(class)"),
	("rel_video_annotation_from_data_source", "MATCH (va:VideoAnnotation { uid: line.video_annotation_uid }) MATCH (data_source:DataSource { uid: line.data_source_uid }) MERGE (va)-[:FROM_DATA_SOURCE]->(data_source)"),
	("rel_video_annotation_annotates_video", "MATCH (va:VideoAnnotation { uid: line.video_annotation_uid }) MATCH (video:Video { uid: line.video_uid }) MERGE (va)-[:ANNOTATES_VIDEO]->(video)")
]

def load_from_csv(file_path: str, command: str, use_periodic_commit: bool = False, **kwargs: Any):
	print("Loading from", file_path)

	driver = GraphDatabase.driver(f"{NEO4J_PROTOCOL}://{NEO4J_HOST}:{NEO4J_PORT}", auth=(NEO4J_USER, NEO4J_PASS)) # type: ignore
	with driver.session() as session: # type: ignore
		while True:
			try:
				session.run( # type: ignore
					"{periodic_commit} LOAD CSV WITH HEADERS FROM $file_path AS line {command}".format(periodic_commit = "USING PERIODIC COMMIT 25000" if use_periodic_commit else "", command = command),
					file_path = "file:///" + file_path,
					**kwargs
				)
				break
			except TransientError as e:
				print("Hit a TransientError (likely a deadlock), trying again after a bit:", file_path)
				sleep(0.1)

	return []

def load_template(file_path: str) -> str:
	driver = GraphDatabase.driver(f"{NEO4J_PROTOCOL}://{NEO4J_HOST}:{NEO4J_PORT}", auth=(NEO4J_USER, NEO4J_PASS)) # type: ignore
	with driver.session() as session: # type: ignore
		results = session.run( # type: ignore
			"LOAD CSV FROM $file_path AS line FIELDTERMINATOR '\\f' CALL zensors.mldl.getAnnotationTemplateNode(line[0]) YIELD value AS templateNode RETURN templateNode.uid AS uid",
			file_path = "file:///" + file_path
		)

		return results.single()["uid"] # type: ignore

def get_neo4j_path(file_path: str, base_path: str):
	return path_join(base_path, file_path)

def main():
	parser = argparse.ArgumentParser(description = HELP)
	parser.add_argument("--server-path", required = True, help = "Path to annotation directory on the server")
	parser.add_argument("--local-tar", required = True, help = "Path to *.tar.gz copy of the files to import on the client")
	parser.add_argument("--workers", type = int, default = 4)
	parser.add_argument("--threads-per-worker", type = int, default = 4)
	args = parser.parse_args()
	run(
		local_tar = args.local_tar,
		server_path = args.server_path,
		n_workers = args.workers,
		threads_per_worker = args.threads_per_worker
	)


def run(*, local_tar: str, server_path: str, n_workers: int, threads_per_worker: int):
	local_tar_members = set(file.name for file in tarfile.open(local_tar).getmembers())

	# initialize client
	cluster = LocalCluster(n_workers = n_workers, threads_per_worker = threads_per_worker, dashboard_address = "0.0.0.0:8787")
	print("Dask dashboard available at", cluster.dashboard_link) # type: ignore
	client = Client(cluster)

	def load_if_exists(file_name: str, command: str) -> None:
		if file_name in local_tar_members:
			load_from_csv(path_join(server_path, file_name), command)

	# load the template
	template_uid = load_template(path_join(server_path, "template.json"))
	print(template_uid)

	# one-off imports: data sources, classes, keypoint nodes, attributes, cameras; do these serially since they depend on each other
	load_if_exists("ent_data_source.csv", "MERGE (ds:DataSource { uid: line.uid }) ON CREATE SET ds.name = line.name")
	load_if_exists("ent_labeler.csv", "MERGE (labeler:Labeler { uid: line.uid })")
	load_if_exists("ent_camera.csv", "MERGE (camera:Camera { uid: line.uid })")
	load_if_exists("ent_instance_identity.csv", "MERGE (ident:InstanceIdentity { uid: line.uid })")

	# entity imports: we can parallelize these since they will never conflict with each other
	dask.bag.from_delayed([ # type: ignore
		delayed(load_from_csv)(path_join(server_path, file), command)
		for file_pattern, command in ENTITY_GLOBS
		for file in local_tar_members
		if file.startswith(file_pattern + "__")
	]).compute()

	# relationship imports: we can parallelize these by being careful about locking order
	dask.bag.from_delayed([ # type: ignore
		delayed(load_from_csv)(path_join(server_path, file), command, use_periodic_commit = True, template_uid = template_uid)
		for file_pattern, command in RELATIONSHIP_GLOBS
		for file in local_tar_members
		if file.startswith(file_pattern + "__")
	]).compute()

	client.close() # type: ignore
	cluster.close() # type: ignore

if __name__ == "__main__":
	main()
