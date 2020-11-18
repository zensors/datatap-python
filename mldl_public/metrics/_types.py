from typing import NamedTuple

from mldl_public.geometry import Rectangle

class PredictionBox(NamedTuple):
	confidence: float
	class_name: str
	box: Rectangle

class GroundTruthBox(NamedTuple):
	class_name: str
	box: Rectangle

