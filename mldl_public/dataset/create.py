import json
import math
from enum import Enum
from os import getenv

from typing_extensions import TypedDict

from typing import Callable, List, Optional
from uuid import uuid4, UUID
from neo4j import GraphDatabase, Transaction

from mldl_public.template import AnnotationTemplate

NEO4J_PROTOCOL = getenv("MLDL_NEO4J_PROTOCOL", "neo4j")
NEO4J_HOST = getenv("MLDL_NEO4J_HOST", "localhost")
NEO4J_PORT = getenv("MLDL_NEO4J_PORT", "7687")
NEO4J_USER = getenv("MLDL_NEO4J_USER", "neo4j")
NEO4J_PASS = getenv("MLDL_NEO4J_PASS", "neo4j")

# FIXME(zwade): Where is the correct location for this?
class SplitKind(Enum):
    TEMPORARY  = "temporary"
    TRAINING   = "training"
    VALIDATION = "validation"

class DatasetOptions(TypedDict):
    # a maximum percentage allowed
    negative_annotations: Optional[float]

    # the percentage of annotations to be used in the validation set
    validation_size: Optional[float]

    # the max percentage of dataset allowed to come from similar cameras
    camera_similarity: Optional[float]

    # the largest allowed training size
    max_training: Optional[int]

    # the largest allowed validation size
    max_validation: Optional[int]


def binary_search(lo: int, hi: int, predicate: Callable[[int], bool]) -> int:
	# predicate should return true for all values at or below the target value
	while lo < hi:
		mid = (lo + hi + 1) // 2
		if predicate(mid):
			lo = mid
		else:
			hi = mid - 1

	return lo

def init_split(tx: Transaction, kind: SplitKind):
    dataset_split_uid = uuid4()
    tx.run(
        """
        CREATE (:DatasetSplit { uid: $uid, kind: $kind })
        """,
        {
            "uid": str(dataset_split_uid),
            "kind": kind.value
        }
    )
    return dataset_split_uid

def add_all_labels_for_template(tx: Transaction, dataset_split_uid: UUID, template: AnnotationTemplate):
    result = tx.run(
        f"""
        CALL zensors.mldl.findMatchingAnnotationTemplates($template)
        YIELD value AS template
        MATCH (a:Annotation)-[:DESCRIBED_BY]->(template)
        MATCH (set:DatasetSplit {{ uid: $dataset_split_uid }})
        WHERE
            NOT EXISTS (a.invalid)
            AND NOT EXISTS (a.mask)
        CREATE (set)-[r:HAS_ANNOTATION]->(a)
        RETURN count(a) as total_annotations
        """,
        {
            "template": json.dumps(template.to_json()),
            "dataset_split_uid": str(dataset_split_uid)
        }
    )

    [(total_annotations,)] = list(result)
    print(f"Found {total_annotations} total annotations")
    return total_annotations

def generic_balance(
    tx: Transaction,
    dataset_split_uid: UUID,
    balance_conditions: List[str],
    group_by_clause: str,
    max_ratio: float,
):
    conditions_pattern = [
        f"OPTIONAL MATCH {condition}"
        for condition in balance_conditions
    ]

    conditions_clause = " ".join(conditions_pattern)

    # group all the annotations in this dataset that match [balance_conditions]
    # according to [group_by_clause]
    raw_grouped_annotations = tx.run(
        f"""
        MATCH (set:DatasetSplit {{ uid: $dataset_split_uid }})-[:HAS_ANNOTATION]->(a:Annotation)
        { conditions_clause }
        RETURN { group_by_clause }, count(distinct a)
        """,
        {
            "dataset_split_uid": str(dataset_split_uid)
        }
    )

    grouped_annotations = list(raw_grouped_annotations)

    # Groups that return [NULL] are allowed to be arbitrarily large
    only_null_group = all(key is None for key, _ in grouped_annotations)
    if only_null_group:
        return

    contains_null_group = any(key is None for key, _ in grouped_annotations)
    if not contains_null_group and 1 / len(grouped_annotations) > max_ratio:
        # By PHP, our constraint can't be satisfied
        raise ValueError(
            "Impossible balance ratio; too few groups to satisfy "
            f" (ratio {max_ratio}, {len(grouped_annotations)} groups)"
        )

    total_annotations: int = max([count for _, count in grouped_annotations])

    def check_threshold(threshold: int):
        """Checks whether a given threshold will allow us to meet our [max_ratio] obligation"""
        corrected_total_annotations = sum(
            min(threshold, count) if key is not None else count
            for key, count in grouped_annotations
        )

        worst_offender = max(
            min(threshold, count)
            for key, count in grouped_annotations
            if key is not None
        )

        return worst_offender < corrected_total_annotations * max_ratio

    threshold = binary_search(1, total_annotations, check_threshold)

    for key, count in grouped_annotations:
        if key is not None and count > threshold:
            tx.run(
                f"""
                MATCH (set:DatasetSplit {{ uid: $dataset_split_uid }})-[r:HAS_ANNOTATION]->(a:Annotation)
                {conditions_clause}
                WITH r, rand() as rand where {group_by_clause} = $key
                WITH r ORDER BY rand LIMIT $remove_count
                DELETE r
                """,
                {
                    "dataset_split_uid": str(dataset_split_uid),
                    "key": key,
                    "remove_count": count - threshold
                }
            )

def balance_data_sources(tx: Transaction, dataset_split_uid: UUID, max_ratio: float):
    generic_balance(
        tx,
        dataset_split_uid,
        ["(a)-[:FROM_DATA_SOURCE]->(src:DataSource)"],
        "src.uid",
        max_ratio,
    )

def balance_camera_similarity(tx: Transaction, dataset_split_uid: UUID, max_ratio: float):
    generic_balance(
        tx,
        dataset_split_uid,
        [
            "(a)-[:ANNOTATES_IMAGE]->(i:Image)-[:TAKEN_BY]->(cam:Camera)",
            "(sg:CameraSimilarityGroup)-[:CONTAINS_CAMERA]->(cam)",
        ],
        "coalesce(sg.uid, cam.uid)",
        max_ratio,
    )

def balance_negative_annotations(tx: Transaction, dataset_split_uid: UUID, classes: List[str], max_ratio: float):
    cases_pattern = [
        "WHEN EXISTS("
            "(a)-[:HAS_INSTANCE]->"
            "(:Instance)-[:IS_INSTANCE_OF]->"
            "(:Class)-[:IS_SUBCLASS_OF*0..]->"
            f"(:Class {{ name: \"{class_name}\" }})"
        ") THEN NULL"
        for class_name in classes
    ]
    cases_clause = "(CASE " + " ".join(cases_pattern) + " ELSE true END)"

    generic_balance(
        tx,
        dataset_split_uid,
        [],
        cases_clause,
        max_ratio
    )

def subdivide_split(
    tx: Transaction,
    temporary_split_uid: UUID,
    ratio: float,
    max_training: Optional[int] = None,
    max_val: Optional[int] = None
):
    training_split_uid = init_split(tx, SplitKind.TRAINING)
    validation_split_uid = init_split(tx, SplitKind.VALIDATION)

    count_result = tx.run(
        """
        MATCH (:DatasetSplit { uid: $temporary_split_uid })-[:HAS_ANNOTATION]->(a:Annotation)
        RETURN count(a) as count
        """,
        {
            "temporary_split_uid": str(temporary_split_uid)
        }
    )

    total_count: int = list(count_result)[0][0]

    val_size = int(math.ceil(ratio * total_count))
    if max_val is not None:
        val_size = min(val_size, max_val)

    training_size = total_count - val_size
    if max_training is not None:
        training_size = min(training_size, max_training)

    tx.run(
        """
        MATCH (tmp_split:DatasetSplit { uid: $temporary_split_uid })
        MATCH (train_split:DatasetSplit { uid: $training_split_uid })
        MATCH (val_split:DatasetSplit { uid: $validation_split_uid })
        MATCH (tmp_split)-[r:HAS_ANNOTATION]->(a:Annotation)
        DELETE r
        WITH tmp_split, train_split, val_split, a, rand() as rng
        ORDER BY rng
        WITH tmp_split, train_split, val_split, collect(a) as all_a
        CALL {
            WITH tmp_split, train_split, all_a
            UNWIND all_a[$val_size..($training_size+$val_size)] AS a
            CREATE (train_split)-[r:HAS_ANNOTATION]->(a)
            RETURN count(r) AS r1
        }
        CALL {
            WITH tmp_split, val_split, all_a
            UNWIND all_a[..$val_size] AS a
            CREATE (val_split)-[r:HAS_ANNOTATION]->(a)
            RETURN count(r) AS r2
        }
        DELETE tmp_split
        RETURN r1, r2
        """,
        {
            "temporary_split_uid": str(temporary_split_uid),
            "training_split_uid": str(training_split_uid),
            "validation_split_uid": str(validation_split_uid),
            "val_size": val_size,
            "training_size": training_size,
        }
    )

    return (training_split_uid, validation_split_uid)

def create_dataset(
    tx: Transaction,
    training_split_uid: UUID,
    validation_split_uid: UUID,
    name: str,
    template: AnnotationTemplate
):
    dataset_uid = uuid4()

    tx.run(
        """
        MATCH (train_split:DatasetSplit { uid: $training_split_uid })
        MATCH (val_split:DatasetSplit { uid: $validation_split_uid })
        CALL zensors.mldl.getAnnotationTemplateNode($template)
        YIELD value AS template
        CREATE (ds:Dataset { uid: $dataset_uid, name: $name })-[:USES_TEMPLATE]->(template)
        CREATE (ds)-[:HAS_SPLIT]->(train_split)
        CREATE (ds)-[:HAS_SPLIT]->(val_split)
        """,
        {
            "training_split_uid": str(training_split_uid),
            "validation_split_uid": str(validation_split_uid),
            "dataset_uid": str(dataset_uid),
            "name": name,
            "template": json.dumps(template.to_json())
        }
    )

    return dataset_uid

def create_dataset_from_template(name: str, template: AnnotationTemplate, opts: DatasetOptions) -> UUID:
    driver = GraphDatabase.driver(f"{NEO4J_PROTOCOL}://{NEO4J_HOST}:{NEO4J_PORT}", auth=(NEO4J_USER, NEO4J_PASS))
    with driver.session() as session:
        def run_tx(tx: Transaction):
            classes = list(template.classes.keys())

            tmp_split = init_split(tx, SplitKind.TEMPORARY)
            total_annotations = add_all_labels_for_template(tx, tmp_split, template)

            if total_annotations == 0:
                raise Exception("Unable to create dataset. Not enough data")

            balance_camera_similarity(tx, tmp_split, opts.get("camera_similarity") or 0.1)
            balance_negative_annotations(tx, tmp_split, classes, opts.get("negative_annotations") or 1 / min(1 + len(classes), 4))

            training_split, validation_split = subdivide_split(tx, tmp_split, opts.get("validation_size") or 0.05, opts.get("max_training"), opts.get("max_validation"))

            return create_dataset(tx, training_split, validation_split, name, template)

        dataset = session.write_transaction(run_tx)

    return dataset

def promote_dataset(name: str, dataset: UUID):
    driver = GraphDatabase.driver(f"{NEO4J_PROTOCOL}://{NEO4J_HOST}:{NEO4J_PORT}", auth=(NEO4J_USER, NEO4J_PASS))
    with driver.session() as session:
        session.run(
            """
            CALL zensors.mldl.updateDatasetReference($name, $dataset)
            """,
            {
                "name": name,
                "dataset": str(dataset)
            }
        )
