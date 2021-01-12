<p align="center">
    <img src="https://zensors-public-content.s3.us-east-2.amazonaws.com/datatap-logo-dark-on-light.png" width="400">
</p>

<p align="center">
    <img src="https://badge.buildkite.com/8afb95fcb4f99547e2d7b8618171e1c7f21b89c2306c8d1f76.svg?branch=master">
    <a href="https://docs.datatap.dev"><img src="https://img.shields.io/badge/docs-available-brightgreen"></a>
    <a href="https://pypi.org/project/datatap/"><img src="https://img.shields.io/pypi/v/datatap"></a>
</p>

<p align="center">
    <img src="https://zensors-public-content.s3.us-east-2.amazonaws.com/getting_started.gif" width="600">
</p>

<p align="center">
    The visual data management platform from <a href="https://zensors.com">Zensors</a>.
</p>

----------

<p align="center">
    Join for free at <a href="https://app.datatap.dev">app.datatap.dev</a>.
</p>


The dataTap Python library is the primary interface for using dataTap's rich data management tools. Create datasets, stream annotations, and analyze model performance all with one library.

----------

## Documentation

Full documentation is available at [docs.datatap.dev](https://docs.datatap.dev/).

## Features

 - [x] ⚡ Begin training instantly
 - [x] 🔥 Works with all major ML frameworks (Pytorch, TensorFlow, etc.)
 - [x] 🛰️ Real-time streaming to avoid large dataset downloads
 - [x] 🌐 Universal data format for simple data exchange
 - [x] 🎨 Combine data from multiples sources into a single dataset easily
 - [x] 🧮 Rich ML utilities to compute PR-curves, confusion matrices, and accuracy metrics.
 - [x] 💽 Free access to a variety of open datasets.

## Getting Started

Install the client library.

```bash
pip install datatap
```

Register at [app.datatap.dev](https://app.datatap.dev). Then, go to `Settings > Api Keys` to find your personal API key.

```bash
export DATATAP_API_KEY="XXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXX"
```

Start using open datasets instantly.

```python
from datatap import Api

api = Api()
coco = api.get_default_database().get_repository("_/coco")
dataset = coco.get_dataset("latest")
print("COCO: ", dataset)
```

## Data Streaming Example

```python
import itertools
from datatap import Api

api = Api()
dataset = (api
    .get_default_database()
    .get_repository("_/wider-person")
    .get_dataset("latest")
)

training_stream = dataset_version.stream_split("training")
for annotation in itertools.islice(training_stream, 5):
    print("Received annotation:", annotation)
```

## More Examples
 - [Documented Sample](https://github.com/Zensors/datatap-python/tree/master/datatap/examples/streaming-sample.md)
 - [Pytorch Jupyter Notebook](https://github.com/Zensors/datatap-python/tree/master/datatap/examples/torch.ipynb)


## Support and FAQ

**Q. How do I resolve a missing API Key?**

If you see the error `Exception: No API key available. Either provide it or use the [DATATAP_API_KEY] environment variable`, then the dataTap library was not able to find your API key. You can find your API key on [app.datatap.dev](https://app.datatap.dev) under settings. You can either set it as an environment variable or as the first argument to the `Api` constructor.

**Q. Can dataTap be used offline?**

Some functionality can be used offline, such as the droplet utilities and metrics. However, repository access and dataset streaming require internet access, even for local databases.

**Q. Is dataTap accepting contributions?**

dataTap currently uses a separate code review system for managing contributions. The team is looking into switching that system to GitHub to allow public contributions. Until then, we will actively monitor the GitHub issue tracker to help accomodate the community's needs.

**Q. How can I get help using dataTap?**

You can post a question in the [issue tracker](https://github.com/zensors/datatap-python/issues). The dataTap team actively monitors the repository, and will try to get back to you as soon as possible.
