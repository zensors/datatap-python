from __future__ import annotations

from typing import Optional, Sequence

try:
	from comet_ml import APIExperiment, Experiment
	from comet_ml.exceptions import NotFound
except ImportError:
	from datatap.utils import pprint
	pprint("{yellow}Unable to import comet_ml.")

from datatap.api.entities import Dataset
from datatap.droplet.image_annotation import ImageAnnotation


def init_experiment(experiment: Experiment, dataset: Dataset):
	"""
	Initializes an experiment by logging the template and the validation set ground truths if they have not already
	been logged.
	"""
	api_experiment = APIExperiment(previous_experiment = experiment.id)

	if get_dataset(experiment) is None:
		log_dataset(experiment, dataset)

	try:
		api_experiment.get_asset("datatap/template.json")
	except NotFound:
		experiment.log_asset_data(
			[annotation.to_json() for annotation in dataset.stream_split("validation")],
			name = "datatap/validation/ground_truth.json"
		)

		experiment.log_asset_data(
			dataset.template.to_json(),
			name = "datatap/template.json"
		)

def log_dataset(experiment: Experiment, dataset: Dataset):
	experiment.log_other("datatap-dataset", dataset.get_stable_identifier())

def get_dataset(experiment: Experiment) -> Optional[str]:
	api_experiment = APIExperiment(previous_experiment = experiment.id)
	others = api_experiment.get_others_summary()
	dataset_metrics = [other for other in others if other["name"] == "datatap-dataset"]

	if len(dataset_metrics) == 0:
		return None

	return dataset_metrics[0].get("valueCurrent", None)

def log_validation_proposals(experiment: Experiment, proposals: Sequence[ImageAnnotation]):
	experiment.log_asset_data(
		[annotation.to_json() for annotation in proposals],
		name = "datatap/validation/proposals.json"
	)
