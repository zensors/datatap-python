from __future__ import annotations

import dask
import dask.bag
import json
import re
from dask.bag import Bag
from neo4j import GraphDatabase
from os import getenv
from uuid import UUID

from ..droplet import Annotation
from ..template import AnnotationTemplate

from typing import Iterable, Optional

UID_REGEX = re.compile(r"^[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}$")

NEO4J_PROTOCOL = getenv("MLDL_NEO4J_PROTOCOL", "neo4j")
NEO4J_HOST = getenv("MLDL_NEO4J_HOST", "localhost")
NEO4J_PORT = getenv("MLDL_NEO4J_PORT", "7687")
NEO4J_USER = getenv("MLDL_NEO4J_USER", "neo4j")
NEO4J_PASS = getenv("MLDL_NEO4J_PASS", "neo4j")

class Dataset:
	uid: str
	template: AnnotationTemplate
	training: Bag[Annotation]
	validation: Bag[Annotation]

	@staticmethod
	def load(name_or_uid: str, npartitions: int = 12) -> Dataset:
		uid = resolve_dataset_uid(name_or_uid)

		return Dataset(
			uid = uid,
			template = load_dataset_template(uid),
			training = load_dataset_split(uid, "training", npartitions),
			validation = load_dataset_split(uid, "validation", npartitions)
		)

	def __init__(self, *, uid: str, template: AnnotationTemplate, training: Bag[Annotation], validation: Bag[Annotation]):
		self.uid = uid
		self.template = template
		self.training = training
		self.validation = validation

def load_dataset_template(uid: str) -> AnnotationTemplate:
	driver = GraphDatabase.driver(f"{NEO4J_PROTOCOL}://{NEO4J_HOST}:{NEO4J_PORT}", auth=(NEO4J_USER, NEO4J_PASS))
	with driver.session() as session:
		with session.begin_transaction() as tx:
			result = tx.run(
				"""
				MATCH (dataset:Dataset { uid: $uid })-[:USES_TEMPLATE]->(template:AnnotationTemplate)
				RETURN zensors.mldl.annotationTemplateToJson(template)
				""",
				uid = uid
			)
			row = result.single()
			if row is None:
				raise Exception(f"Failed to find template for dataset {uid}")
			return AnnotationTemplate.from_json(json.loads(row[0]))

def load_dataset_split(uid: str, split: str, npartitions: int) -> Bag[Annotation]:
	return dask.bag.from_delayed([
		dask.delayed(load_dataset_split_partition)(uid, split, npartitions, i)
		for i in range(npartitions)
	])

def resolve_dataset_uid(name_or_uid: str) -> str:
	if UID_REGEX.fullmatch(name_or_uid):
		return name_or_uid

	driver = GraphDatabase.driver(f"{NEO4J_PROTOCOL}://{NEO4J_HOST}:{NEO4J_PORT}", auth=(NEO4J_USER, NEO4J_PASS))
	with driver.session() as session:
		with session.begin_transaction() as tx:
			result = tx.run(
				"MATCH (ref:DatasetReference { name: $name })-[:IS_DATASET]->(dataset:Dataset) RETURN dataset.uid",
				name = name_or_uid
			)
			row = result.single()
			if row is None:
				raise Exception(f"Failed to resolve dataset reference: '{name_or_uid}'")
			return row[0]

def load_dataset_split_partition(uid: str, split: str, npartitions: int, partition_index: int) -> Iterable[Annotation]:
	driver = GraphDatabase.driver(f"{NEO4J_PROTOCOL}://{NEO4J_HOST}:{NEO4J_PORT}", auth=(NEO4J_USER, NEO4J_PASS))
	with driver.session() as session:
		with session.begin_transaction() as tx:
			result = tx.run(
				"CALL zensors.mldl.loadDatasetSplitChunk($uid, $split, $nchunks, $chunk)",
				uid = uid,
				split = split,
				nchunks = npartitions,
				chunk = partition_index
			)
			return [Annotation.from_json(json.loads(row["value"])) for row in result]

def resolve_dataset_reference(name: str) -> Optional[UUID]:
	driver = GraphDatabase.driver(f"{NEO4J_PROTOCOL}://{NEO4J_HOST}:{NEO4J_PORT}", auth=(NEO4J_USER, NEO4J_PASS))
	with driver.session() as session:
		raw_results = session.run(
			"""
			MATCH (dr:DatasetReference { name: $name })-[:IS_DATASET]->(d:Dataset)
			RETURN d.uid
			""",
			{
				"name": name,
			}
		)
		results = list(raw_results)

		if len(results) == 0 or results[0][0] is None:
			return None

		return UUID(results[0][0])