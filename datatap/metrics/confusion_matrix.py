from __future__ import annotations
from collections import defaultdict

from typing import DefaultDict, Iterable, Mapping, Optional, Sequence, cast

import numpy as np
from scipy.optimize import linear_sum_assignment

from datatap.droplet import ImageAnnotation

from ._types import GroundTruthBox, PredictionBox

class ConfusionMatrix:
	"""
	Represents a confusion matrix for a collection of annotations.
	This class will handle the matching of instances in a ground truth annotations
	to instances in a set of matching prediction annotations.
	"""

	# TODO(mdsavage): make this accept matching strategies other than bounding box IOU

	classes: Sequence[str]
	"""
	A list of the classes that this confusion matrix is tracking.
	"""

	matrix: np.ndarray
	"""
	The current confusion matrix. Entry `(i, j)` represents the number of times that
	an instance of `self.classes[i]` was classified as an instance of `self.classes[j]`
	"""

	_class_map: Mapping[str, int]

	def __init__(self, classes: Sequence[str], matrix: Optional[np.ndarray] = None):
		self.classes = ["__background__"] + list(classes)
		self._class_map = dict([(class_name, index) for index, class_name in enumerate(self.classes)])
		dim = len(self.classes)
		self.matrix = matrix if matrix is not None else np.zeros((dim, dim))

	def add_annotation(
		self: ConfusionMatrix,
		ground_truth: ImageAnnotation,
		prediction: ImageAnnotation,
		iou_threshold: float,
		confidence_threshold: float
	) -> None:
		"""
		Updates this confusion matrix for the given ground truth and prediction annotations evaluated with the given IOU
		threshold, only considering instances meeting the given confidence threshold.

		Note: this handles instances only; multi-instances are ignored.
		"""
		ground_truth_boxes = [
			GroundTruthBox(class_name, instance.bounding_box.rectangle)
			for class_name in ground_truth.classes.keys()
			for instance in ground_truth.classes[class_name].instances
			if instance.bounding_box is not None
		]

		prediction_boxes = sorted([
			PredictionBox(instance.bounding_box.confidence or 1, class_name, instance.bounding_box.rectangle)
			for class_name in prediction.classes.keys()
			for instance in prediction.classes[class_name].instances
			if instance.bounding_box is not None and instance.bounding_box.meets_confidence_threshold(confidence_threshold)
		], reverse = True, key = lambda p: p.confidence)

		iou_matrix = np.array([
			[ground_truth_box.box.iou(prediction_box.box) for ground_truth_box in ground_truth_boxes]
			for prediction_box in prediction_boxes
		], ndmin = 2)

		prediction_indices, ground_truth_indices = linear_sum_assignment(iou_matrix, maximize = True)

		unmatched_ground_truth_box_counts: DefaultDict[str, int] = defaultdict(lambda: 0)
		unmatched_prediction_box_counts: DefaultDict[str, int] = defaultdict(lambda: 0)

		for box in ground_truth_boxes:
			unmatched_ground_truth_box_counts[box.class_name] += 1

		for box in prediction_boxes:
			unmatched_prediction_box_counts[box.class_name] += 1

		for prediction_index, ground_truth_index in zip(cast(Iterable[int], prediction_indices), cast(Iterable[int], ground_truth_indices)):
			if iou_matrix[prediction_index, ground_truth_index] >= iou_threshold:
				ground_truth_box = ground_truth_boxes[ground_truth_index]
				prediction_box = prediction_boxes[prediction_index]
				self._add_detection(ground_truth_box.class_name, prediction_box.class_name)
				unmatched_ground_truth_box_counts[ground_truth_box.class_name] -= 1
				unmatched_prediction_box_counts[prediction_box.class_name] -= 1

		for class_name, count in unmatched_ground_truth_box_counts.items():
			if count > 0:
				self._add_false_negative(class_name, count = count)

		for class_name, count in unmatched_prediction_box_counts.items():
			if count > 0:
				self._add_false_positive(class_name, count = count)

	def batch_add_annotation(
		self: ConfusionMatrix,
		ground_truths: Sequence[ImageAnnotation],
		predictions: Sequence[ImageAnnotation],
		iou_threshold: float,
		confidence_threshold: float
	) -> None:
		"""
		Updates this confusion matrix with the values from several annotations simultaneously.
		"""
		for ground_truth, prediction in zip(ground_truths, predictions):
			self.add_annotation(
				ground_truth,
				prediction,
				iou_threshold,
				confidence_threshold
			)

	def _add_detection(self, ground_truth_class: str, prediction_class: str, count: int = 1) -> None:
		r = self._class_map[ground_truth_class]
		c = self._class_map[prediction_class]
		self.matrix[r, c] += count

	def _add_false_negative(self, ground_truth_class: str, count: int = 1) -> None:
		self._add_detection(ground_truth_class, "__background__", count)

	def _add_false_positive(self, ground_truth_class: str, count: int = 1) -> None:
		self._add_detection("__background__", ground_truth_class, count)


	def __add__(self, other: ConfusionMatrix) -> ConfusionMatrix:
		if isinstance(other, ConfusionMatrix): # type: ignore - pyright complains about the isinstance check being redundant
			return ConfusionMatrix(self.classes, cast(np.ndarray, self.matrix + other.matrix))
		return NotImplemented
