from __future__ import annotations
from os import cpu_count

import requests
import functools
from typing import Dict, Optional

import tensorflow as tf

from mldl_public.api.entities.dataset_version import DatasetVersion

def get_class_mapping(dataset: DatasetVersion, class_mapping: Optional[Dict[str, int]] = None):
    classes_used = dataset.template.classes.keys()
    if class_mapping is not None:
        if set(class_mapping.keys()) != set(classes_used):
            raise Exception(
                "Invalid class mapping. Provided classes ",
                set(class_mapping.keys()),
                " but needed ",
                set(classes_used)
            )
        return class_mapping
    else:
        return {
            cls: i
            for i, cls in enumerate(sorted(classes_used))
        }

def create_tf_dataset(
        version: DatasetVersion,
        split: str,
        input_class_mapping: Optional[Dict[str, int]] = None,
        num_workers: int = cpu_count() or 1,
        input_context: Optional[tf.distribute.InputContext] = None
):
    class_mapping = get_class_mapping(version, input_class_mapping)

    def gen():
        worker_id = input_context.input_pipeline_id if input_context is not None else 0
        num_workers = input_context.num_input_pipelines if input_context is not None else 1

        for droplet in version.stream_split(split, worker_id, num_workers):
            image_url = tf.constant(droplet.image.paths[0])

            bounding_boxes = tf.stack([
                tf.constant(i.bounding_box.to_xywh_tuple(), shape=(4,), dtype=tf.float64)
                for cls in droplet.classes.keys()
                for i in droplet.classes[cls].instances
            ])

            labels = tf.stack([
                tf.constant(class_mapping[cls], dtype=tf.int32)
                for cls in droplet.classes.keys()
                for _ in droplet.classes[cls].instances
            ])

            yield (image_url, bounding_boxes, labels)

    def _load_img_fn(image_url: tf.Tensor):
        res = requests.get(image_url.numpy().decode("ascii"))
        img = tf.io.decode_jpeg(res.content, channels=3)
        return img

    def load_img_fn(image_url: tf.Tensor):
        return tf.py_function(_load_img_fn, inp=(image_url,), Tout=(tf.uint8,))

    def map_fn(image_url: tf.Tensor, boxes: tf.Tensor, labels: tf.Tensor):
        return (load_img_fn(image_url), boxes, labels)

    ds = tf.data.Dataset.from_generator(
        gen,
        (tf.string, tf.float64, tf.int32),
        (tf.TensorShape(()), tf.TensorShape((None, 4)), (tf.TensorShape((None))))
    )

    return ds.map(map_fn, num_parallel_calls=num_workers)


def create_tf_multi_worker_dataset(
    strategy: tf.distribute.experimental.Strategy,
    version: DatasetVersion,
    split: str,
    num_workers: int = cpu_count() or 1,
    input_class_mapping: Optional[Dict[str, int]] = None,
):
    ds = strategy.experimental_distribute_datasets_from_function(
        functools.partial(create_tf_dataset, version, split, num_workers, input_class_mapping)
    )
    return ds
