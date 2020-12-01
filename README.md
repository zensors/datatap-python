# dataTap

**dataTap** is the all-in-one data management platform from [Zensors](https://zensors.com). Join for free at [datatap.dev](https://datatap.dev).

# dataTap Python Library

The dataTap Python library is the primary interface for using dataTap's rich data management tools. Create datasets, stream annotations, and analyze model performance all with one library.

Full documentation is available at [docs.datatap.dev](https://docs.datatap.dev/).

## Installation & Setup

The latest version of dataTap can be installed with `pip`.

```bash
pip install datatap
```

In order to access the cloud-based functionality, you will also need to register an account at [app.datatap.dev](https://app.datatap.dev). Once you've registered, go to `Settings > Api Keys` to find your personal API key. In order to avoid storing private keys in your code, you should assign this key to the `DATATAP_API_KEY` environment variable.

```bash
export DATATAP_API_KEY="XXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXX"
```

## Getting started

Installing `datatap` gives access to the `Api` class for interacting with the dataTap cloud platform. Here is how we can use it:

```python
import itertools
from datatap import Api

api = Api()

# Datatap allows users to connect several databases, and also provides a
# public database that contains millions of freely available annotations.
# `get_default_database` will connect us to that one.
database = api.get_default_database()
print("Database", database)

# We can then fetch a list of repositories that have already been created in
# this database
repository_list = database.get_repository_list()
print("Available repositories:", [repo.name for repo in repository_list])

# A repository is a grouping of datasets that are associated in some manner.
# For instance, a repository called `"person-keypoints"` would contain
# one or more datasets of people with their keypoints.
#
# The datasets within a given repository are identfieid by "tags", or short
# strings that identfy either how they were created, or how they should be
# used. Example tags might be `all-datasets`, `open-images`, or `december-2020`.
# Additionally, all repositories have one dataset identified with `latest`,
# which should refer to the most recent "canonical" dataset.
#
# For this example, we will use the `widerperson` repository, and the dataset
# identified as `latest`.

repository = database.get_repository("public", "widerperson")
dataset = repository.get_dataset("latest")

print("Loaded dataset:", dataset)

# A dataset's template describes how it is structured. We can print
# it to see what type of data this dataset contains
print("Dataset template:", dataset.template)

# Datasets are furthermore partitioned into one or more `splits`.
# In most cases, the dataset will contain two splits called `"training"`
# and `"validation"`. We can stream the contents of a particular split
# by using the `stream_split` function
training_stream = dataset_version.stream_split("training")

for annotation in itertools.islice(training_stream, 5):
    # Each element of the stream will be an `ImageAnnotation`
    print("Received annotation:", annotation)
```

For a more in-depth example, including model training and evaluation, please take a look at [datatap/examples/torch.ipynb](https://github.com/Zensors/datatap-python/tree/master/datatap/examples/torch.ipynb).

## Documentation

All documentation for this Python library can be found at [docs.datatap.dev](https://docs.datatap.dev).