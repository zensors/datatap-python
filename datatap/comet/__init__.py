from typing import Sequence

from comet_ml import APIExperiment, Experiment
from comet_ml.exceptions import NotFound
from datatap.api.entities import Dataset
from datatap.droplet.image_annotation import ImageAnnotation


def init_experiment(experiment: Experiment, dataset: Dataset):
	"""
	Initializes an experiment by logging the template and the validation set ground truths if they have not already
	been logged.
	"""
	api_experiment = APIExperiment(previous_experiment = experiment.id)

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

def log_validation_proposals(experiment: Experiment, proposals: Sequence[ImageAnnotation]):
	experiment.log_asset_data(
		[annotation.to_json() for annotation in proposals],
		name = "datatap/validation/proposals.json"
	)
