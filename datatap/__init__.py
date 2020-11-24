"""
This module provides classes and methods for interacting with dataTap.  This includes inspecting individual annotations,
creating or importing new annotations, and creating or loading datasets for machine learning.

## Examples

### Load a Dataset

```py
from datatap import Api

api = Api("your-api-key-here") # this can also be specified in [DATATAP_API_KEY]

dataset_uid = "your dataset uid here"

database = api.get_default_database()
dataset_version = database.get_dataset_by_uid(dataset_uid)

print("Loaded dataset version:", dataset_version)

# You'll probably want to sanity-check the template and/or get the class list from it
print("Dataset template:", dataset_version.template)

# Datasets can be streamed by specifying which split of the dataset you want
# The streams are returned as generators that yield individual annotations

training_stream = dataset_version.stream_split("training")
validation_stream = dataset_version.stream_split("validation")

print(f"First training element: {next(training_stream)}")
```
"""

from .api.entities import Api

__all__ = [
    "Api",
    "api",
    "droplet",
    "geometry",
    "metrics",
    "template",
    "tf",
    "torch",
    "utils",
]