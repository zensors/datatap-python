"""
The `tf` module provides utilities for using dataTap with Tensorflow.

Please note that if you want to be able to use this module, you will
either need to install Tensorflow manually, or install dataTap with the
tensorflow extra:

```bash
pip install 'datatap[tf]'
```

This module exports two helper functions for creating tensorflow datasets.
Here is an example of the single-process one, `create_tf_dataset`:

```py
import itertools
from datatap import Api
from datatap.tf import create_dataset

api = Api()
dataset = api.get_default_database().get_dataset_list()[0]
latest_version = dataset.latest_version

dataset = create_dataset(latest_version, "training", num_workers = 4)
for (_image, bounding_boxes, labels) in itertools.islice(dataset, 3):
    print(bounding_boxes, labels)
```
"""

from .dataset import create_dataset, create_multi_worker_dataset

__all__ = [
    "create_dataset",
    "create_multi_worker_dataset",
]