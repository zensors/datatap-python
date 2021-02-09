from typing import Sequence

from comet_ml import Experiment
from datatap.api.entities import Dataset
from datatap.droplet.image_annotation import ImageAnnotation


def log_validation_ground_truths(experiment: Experiment, dataset: Dataset):
	experiment.log_asset_data(
		[annotation.to_json() for annotation in dataset.stream_split("validation")],
		name = "datatap/validation/ground_truth.json"
	)

def log_validation_proposals(experiment: Experiment, proposals: Sequence[ImageAnnotation]):
	experiment.log_asset_data(
		[annotation.to_json() for annotation in proposals],
		name = "datatap/validation/proposals.json"
	)
