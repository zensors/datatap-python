from __future__ import annotations  # needed for instance methods to reference other instances of the same class

from collections import defaultdict
from functools import reduce
from typing import DefaultDict, Dict, List, Mapping, NamedTuple, Optional, Sequence, Union
try:
	from comet_ml import Experiment
except ImportError:
	Experiment = {}

import numpy as np
import scipy.optimize

from mldl.geometry import Rectangle
from mldl.droplet import Annotation, Instance, MultiInstance

def maximize_iou(ground_truth: Sequence[Rectangle], prediction: Sequence[Rectangle]) -> Sequence[float]:
	if len(prediction) == 0:
		return []

	if len(ground_truth) == 0:
		return [0 for _ in prediction]

	iou_matrix = np.asarray([
		[truth_box.iou(prediction_box) for prediction_box in prediction]
		for truth_box in ground_truth
	])

	truth_indices, prediction_indices = scipy.optimize.linear_sum_assignment(iou_matrix, maximize = True)
	result = [0 for _ in prediction]
	for truth_index, prediction_index in zip(truth_indices, prediction_indices):
		result[prediction_index] = iou_matrix[truth_index, prediction_index]
	return result

def estimate_threshold(ground_truth: Sequence[Annotation], prediction: Sequence[Annotation]) -> float:
	# We estimate thrshold by choosing it such that we end up with the correct total number of objects detected, if
	# possible.  This minimizes the bias.

	ground_truth_object_count = sum(
		len(class_annotation.instances) + len(class_annotation.multi_instances)
		for annotation in ground_truth
		for class_annotation in annotation.classes.values()
	)

	prediction_confidences = sorted([
		instance.confidence if instance.confidence is not None else 1.0 # TODO: missing multi-instances?
		for annotation in prediction
		for class_annotation in annotation.classes.values()
		for instance in class_annotation.instances
	], reverse = True)

	if ground_truth_object_count >= len(prediction_confidences):
		return 0.5 if len(prediction_confidences) == 0 else prediction_confidences[-1] / 2

	return (prediction_confidences[ground_truth_object_count - 1] + prediction_confidences[ground_truth_object_count]) / 2

class ClassDetectionStatistics:
	true_positives: int
	false_positives: int
	false_negatives: int

	@classmethod
	def merge(cls, a: ClassDetectionStatistics, b: ClassDetectionStatistics) -> ClassDetectionStatistics:
		result = ClassDetectionStatistics()
		result.add_instances(true_positives = a.true_positives, false_positives = a.false_positives, false_negatives = a.false_negatives)
		result.add_instances(true_positives = b.true_positives, false_positives = b.false_positives, false_negatives = b.false_negatives)
		return result

	def __init__(self):
		self.true_positives = 0
		self.false_positives = 0
		self.false_negatives = 0

	def add_instances(self, *, true_positives: int, false_positives: int, false_negatives: int) -> None:
		self.true_positives += true_positives
		self.false_positives += false_positives
		self.false_negatives += false_negatives

	def get_precision(self) -> Optional[float]:
		return (
			self.true_positives / (self.true_positives + self.false_positives)
			if self.true_positives + self.false_positives > 0
			else None
		)

	def get_recall(self) -> Optional[float]:
		return (
			self.true_positives / (self.true_positives + self.false_negatives)
			if self.true_positives + self.false_negatives > 0
			else None
		)

	def get_f1(self) -> Optional[float]:
		precision = self.get_precision()
		recall = self.get_recall()

		return (
			(2 * precision * recall) / (precision + recall)
			if precision is not None and recall is not None and precision + recall > 0
			else None
		)

	def get_critical_success_index(self) -> Optional[float]:
		return (
			self.true_positives / (self.true_positives + self.false_positives + self.false_negatives)
			if self.true_positives + self.false_positives + self.false_negatives > 0
			else None
		)

	def get_bias(self) -> Optional[float]:
		return (
			(self.false_positives - self.false_negatives) / (self.true_positives + self.false_negatives)
			if self.true_positives + self.false_negatives > 0
			else None
		)

class ClassDetectionMetrics(NamedTuple):
	precision: Optional[float]
	recall: Optional[float]
	f1: Optional[float]
	critical_success_index: Optional[float]
	bias: Optional[float]

	@classmethod
	def from_statistics(cls, statistics: ClassDetectionStatistics) -> ClassDetectionMetrics:
		return ClassDetectionMetrics(
			precision = statistics.get_precision(),
			recall = statistics.get_recall(),
			f1 = statistics.get_f1(),
			critical_success_index = statistics.get_critical_success_index(),
			bias = statistics.get_bias()
		)

	def log_to_comet(self, experiment: Experiment, step: Optional[int] = None, class_name: Optional[str] = None):
		suffix = f" ({class_name}" if class_name else ""
		experiment.log_metric("precision"+suffix, self.precision, step = step)
		experiment.log_metric("recall"+suffix, self.recall, step = step)
		experiment.log_metric("f1"+suffix, self.f1, step = step)
		experiment.log_metric("critical_success_index"+suffix, self.critical_success_index, step = step)
		experiment.log_metric("bias"+suffix, self.bias, step = step)

class ConfusionMatrix():
	matrix: np.ndarray
	labels: Sequence[str]

	def __init__(self, labels: Sequence[str]):
		self.matrix = np.zeros((len(labels), len(labels)))
		assert "__background__" in labels
		self.labels = labels

	def add_instance(self, actual_label: str, predicted_label: str) -> None:
		self.matrix[self.labels.index(actual_label), self.labels.index(predicted_label)] += 1

	def log_to_comet(self, experiment: Experiment, step: Optional[int] = None) -> None:
		experiment.log_confusion_matrix(matrix = self.matrix, labels = self.labels, step = step, max_categories = len(self.labels))

def compute_class_statistics(ground_truth: Sequence[Annotation], prediction: Sequence[Annotation], iou_threshold: float = 0.5, confidence_threshold: float = 0) -> Mapping[str, ClassDetectionStatistics]:
	results: DefaultDict[str, ClassDetectionStatistics] = defaultdict(lambda: ClassDetectionStatistics())

	for ground_truth_annotation, prediction_annotation in zip(ground_truth, prediction):
		class_names = ground_truth_annotation.classes.keys() | prediction_annotation.classes.keys()
		for class_name in class_names: # TODO: multi-instances?
			ground_truth_boxes = (
				[instance.bounding_box for instance in ground_truth_annotation.classes[class_name].instances]
				if class_name in ground_truth_annotation.classes
				else []
			)
			prediction_boxes = (
				[
					instance.bounding_box
					for instance in prediction_annotation.classes[class_name].instances
					if instance.confidence is None or instance.confidence >= confidence_threshold
				]
				if class_name in prediction_annotation.classes
				else []
			)
			prediction_ious = maximize_iou(ground_truth_boxes, prediction_boxes)

			true_positives = sum(1 for iou in prediction_ious if iou > iou_threshold)
			results[class_name].add_instances(
				true_positives = true_positives,
				false_positives = len(prediction_boxes) - true_positives,
				false_negatives = len(ground_truth_boxes) - true_positives
			)

	return results

def compute_class_metrics(ground_truth: Sequence[Annotation], prediction: Sequence[Annotation], iou_threshold: float = 0.5, confidence_threshold: float = 0) -> Mapping[str, ClassDetectionMetrics]:
	return {
		class_name: ClassDetectionMetrics.from_statistics(class_statistics)
		for class_name, class_statistics in compute_class_statistics(ground_truth, prediction, iou_threshold, confidence_threshold).items()
	}

def compute_global_metrics(ground_truth: Sequence[Annotation], prediction: Sequence[Annotation], iou_threshold: float = 0.5, confidence_threshold: float = 0) -> ClassDetectionMetrics:
	global_statistics = reduce(
		ClassDetectionStatistics.merge,
		compute_class_statistics(ground_truth, prediction, iou_threshold, confidence_threshold).values(),
		ClassDetectionStatistics()
	)
	return ClassDetectionMetrics.from_statistics(global_statistics)

def compute_confusion_matrix(
	ground_truth: Sequence[Annotation],
	prediction: Sequence[Annotation],
	classes: Sequence[str],
	iou_threshold: float = 0.5,
	confidence_threshold: float = 0.0
) -> ConfusionMatrix:
	matrix = ConfusionMatrix(classes)
	for ground_truth_annotation, prediction_annotation in zip(ground_truth, prediction):
		for kind in ("instances", "multi_instances"):
			# compile list of all bounding boxes with class name injected into it
			ground_truth_boxes = [
				(label.bounding_box, class_name)
				for class_name in ground_truth_annotation.classes
				for label in getattr(ground_truth_annotation.classes[class_name], kind)
			]
			prediction_boxes = [
				(label.bounding_box, class_name)
				for class_name in prediction_annotation.classes
				for label in getattr(prediction_annotation.classes[class_name], kind)
				if label.confidence is None or label.confidence >= confidence_threshold
			]

			# match gt and pred boxes, favoring pairs with matching classes
			large_num = max(len(ground_truth_boxes), len(prediction_boxes))
			score_matrix = np.asarray([
				[
					(
						0 if ground_truth_box.iou(prediction_box) < iou_threshold else
						1 if ground_truth_class != prediction_class else
						large_num
					)
					for ground_truth_box, ground_truth_class in ground_truth_boxes
				]
				for prediction_box, prediction_class in prediction_boxes
			])
			if len(ground_truth_boxes) > 0 and len(prediction_boxes) > 0:
				prediction_indices, ground_truth_indices = scipy.optimize.linear_sum_assignment(score_matrix, maximize=True)
			else:
				prediction_indices, ground_truth_indices = [], []

			unmatched_ground_truth_boxes = set(ground_truth_boxes)
			unmatched_prediction_boxes = set(prediction_boxes)
			# process paired boxes first
			for prediction_index, ground_truth_index in zip(prediction_indices, ground_truth_indices):
				ground_truth_box, ground_truth_class = ground_truth_boxes[ground_truth_index]
				prediction_box, prediction_class = prediction_boxes[prediction_index]
				if ground_truth_box.iou(prediction_box) >= iou_threshold:
					matrix.add_instance(ground_truth_class, prediction_class)
					unmatched_ground_truth_boxes.remove(ground_truth_boxes[ground_truth_index])
					unmatched_prediction_boxes.remove(prediction_boxes[prediction_index])
			# then handle unpaired remaining ground truths and predictions
			for _, ground_truth_class in unmatched_ground_truth_boxes:
				matrix.add_instance(ground_truth_class, "__background__")
			for _, prediction_class in unmatched_prediction_boxes:
				matrix.add_instance("__background__", prediction_class)

	return matrix