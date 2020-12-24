![dataTap](https://zensors-public-content.s3.us-east-2.amazonaws.com/dataTapLogo.png)

The all-in-one data management platform from [Zensors](https://zensors.com). Join for free at [datatap.dev](https://datatap.dev).

![build](https://badge.buildkite.com/8afb95fcb4f99547e2d7b8618171e1c7f21b89c2306c8d1f76.svg)
[![docs](https://img.shields.io/badge/docs-available-brightgreen)](https://docs.datatap.dev)
[![pypi](https://img.shields.io/pypi/v/datatap)](https://pypi.org/project/datatap/)

![hero](https://datatap.dev/static/header-image-9a06bbd4c01c2cd44501e0545e88cb2a.png)

----------

Full documentation is available at [docs.datatap.dev](https://docs.datatap.dev/).

The dataTap Python library is the primary interface for using dataTap's rich data management tools. Create datasets, stream annotations, and analyze model performance all with one library.

## Installation & Setup

The latest version of dataTap can be installed with `pip`.

```bash
pip install datatap
```

In order to access the cloud-based functionality, you will also need to register an account at [app.datatap.dev](https://app.datatap.dev). Once you've registered, go to `Settings > Api Keys` to find your personal API key. In order to avoid storing private keys in your code, you should assign this key to the `DATATAP_API_KEY` environment variable.

```bash
export DATATAP_API_KEY="XXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXX"
```

Once you have an API key, you can begin streaming open datasets instantly.

```python
from datatap import Api

api = Api()
coco = api.get_default_database().get_repository("_/coco")
dataset = coco.get_dataset("latest")
print("COCO: ", dataset)
```

For a more in-depth example, including model training and evaluation, please take a look at [datatap/examples/torch.ipynb](https://github.com/Zensors/datatap-python/tree/master/datatap/examples/torch.ipynb).

## Features

### Real-Time Data Streaming

Large datasets can be hundreds of gigabytes. Downloading and preparing these datasets takes away valuable developer and computation time. With dataTap, you can begin training instantly through our real-time streaming API.

### Universal Data Format

dataTap's Droplet format allows all for interoperability between all datasets, and allows developers to write code once and use it everywhere. Additionally, the Droplet format allows structured data queries, so developers get exactly the data they need.

### Powerful Dataset Creation Tools

In addition to our wide array of public datasets, users can upload their own datasets, or combine several for a larger and more representative dataset.

### Rich ML Utilities

dataTap comes with several pre-built ML utilities, such as precision-recall curves and confusion matrices. When you use the droplet format, these powerful metrics work out-of-the-box.

## Support and FAQ

### Q. How do I resolve `Exception: No API key available. Either provide it or use the [DATATAP_API_KEY] environment variable`?

Seeing this error means that the dataTap library was not able to find your API key. You can find your API key on [app.datatap.dev](https://app.datatap.dev) under settings. You can either set it as an environment variable or as the first argument to the `Api` constructor.

### Q. Can dataTap be used offline?

Some functionality can be used offline, such as the droplet utilities and metrics. However, repository access and dataset streaming require internet access, even for local databases.

### Q. Is dataTap accepting contributions?

dataTap currently uses a separate code review system for managing contributions. The team is looking into switching that system to GitHub to allow public contributions. Until then, we will actively monitor the GitHub issue tracker to help accomodate the community's needs.

### Q. How can I get help using dataTap?

You can post a question in the [issue tracker](https://github.com/zensors/datatap-python/issues). The dataTap team actively monitors the repository, and will try to get back to you as soon as possible.

## Resources

All documentation for this Python library can be found at [docs.datatap.dev](https://docs.datatap.dev).

## Detailed Example

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
# For this example, we will use the `wider-person` repository, and the dataset
# identified as `latest`.

repository = database.get_repository("_/wider-person")
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

