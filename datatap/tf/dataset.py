from __future__ import annotations
from os import cpu_count

import requests
import functools
from typing import Dict, Optional

try:
    import tensorflow as tf
except ImportError:
    tf = {}

from datatap.api.entities import Dataset

def _get_class_mapping(dataset: Dataset, class_mapping: Optional[Dict[str, int]] = None):
    classes_used = dataset.template.classes.keys()
    if class_mapping is not None:
        if set(class_mapping.keys()) != set(classes_used):
            print(
                "[WARNING]: Potentially invalid class mapping. Provided classes ",
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

def create_dataset(
        dataset: Dataset,
        split: str,
        input_class_mapping: Optional[Dict[str, int]] = None,
        num_workers: int = cpu_count() or 1,
        input_context: Optional[tf.distribute.InputContext] = None
):
    """
    Creates a tensorflow `Dataset` object that will load a specified split of `version`.

    This function handles the necessary `Dataset` operations to parallelize the loading
    operation. Since image loading can be slow, it is recommended to have `num_workers`
    set to a value greater than 1. By default, it will try to load one image per CPU.

    If you intend to use the dataset across multiple processes or computers, consider
    using `create_tf_multi_worker_dataset` instead.
    """
    class_mapping = _get_class_mapping(dataset, input_class_mapping)

    def gen():
        worker_id = input_context.input_pipeline_id if input_context is not None else 0
        num_workers = input_context.num_input_pipelines if input_context is not None else 1

        for droplet in dataset.stream_split(split, worker_id, num_workers):
            image_url = tf.constant(droplet.image.paths[0])

            bounding_boxes = tf.stack([
                tf.constant(i.bounding_box.rectangle.to_xywh_tuple(), shape=(4,), dtype=tf.float64)
                for cls in droplet.classes.keys()
                for i in droplet.classes[cls].instances
                if i.bounding_box is not None
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


def create_multi_worker_dataset(
    strategy: tf.distribute.experimental.Strategy,
    dataset: Dataset,
    split: str,
    num_workers: int = cpu_count() or 1,
    input_class_mapping: Optional[Dict[str, int]] = None,
):
    """
    Creates a multi-worker sharded dataset. In addition to sharding the contents
    of the dataset across multiple machines, this function will also attempt to
    load the images across several workers.

    If you are running multiple workers on the same physical machine, consider lowering
    the value of `num_workers`, as by default each worker will try to use every CPU
    on the machine.
    """
    ds = strategy.experimental_distribute_datasets_from_function(
        functools.partial(create_dataset, dataset, split, num_workers, input_class_mapping)
    )
    return ds
