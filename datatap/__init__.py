"""
This module provides classes and methods for interacting with dataTap.  This includes inspecting individual annotations,
creating or importing new annotations, and creating or loading datasets for machine learning.

## Examples

### Load a Dataset

```py
from datatap import Api

api = Api("your-api-key-here") # this can also be specified in [DATATAP_API_KEY]

database = api.get_default_database()
repository = database.get_repository("public/open-images")
dataset = repository.get_dataset("latest")

print("Loaded dataset:", dataset)

# You'll probably want to sanity-check the template and/or get the class list from it
print("Dataset template:", dataset.template)

# Datasets can be streamed by specifying which split of the dataset you want
# The streams are returned as generators that yield individual annotations

training_stream = dataset.stream_split("training")
validation_stream = dataset.stream_split("validation")

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