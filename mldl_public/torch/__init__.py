"""
The `torch` module provides utilities for using MLDL with PyTorch.

Please note that if you want to be able to use this module, you will
either need to install PyTorch manually, or install MLDL with the
PyTorch extra:

```bash
pip install 'mldl_public[torch]'
```

The `torch` module provides both a `torch.IterableDataset` implementation,
and a convenience method to create a `torch.Dataloader` using it. Here is
an example of how to use these:

```py
import itertools
from mldl_public import Api
from mldl_public.torch import create_dataloader

import torchvision.transforms as T

api = Api()
dataset = api.get_default_database().get_dataset_list()[0]
latest_version = dataset.latest_version

transforms = T.Compose([
    T.Resize((128, 128)),
    T.ColorJitter(hue=0.2),
    T.ToTensor(),
])

dataloader = create_dataloader(latest_version, "training", batch_size = 4, image_transform = transforms)
for batch in itertools.islice(dataloader, 3):
    print(batch.boxes, batch.labels)
```

"""

from ._patch_torch import patch_all as _patch_all
_patch_all()

from .dataset import DatasetElement, DatasetBatch, IterableDataset
from .dataloader import create_dataloader

__all__ = [
    "DatasetElement",
    "DatasetBatch",
    "IterableDataset",
    "create_dataloader",
]