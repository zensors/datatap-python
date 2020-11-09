from mldl_public.metrics.confusion_matrix import ConfusionMatrix
from typing import NamedTuple, Sequence

import numpy as np
from scipy.optimize import linear_sum_assignment

from ..droplet import ImageAnnotation
from ..geometry import Rectangle
from ..template import ImageAnnotationTemplate
from .precision_recall_curve import DetectionEvent, PrecisionRecallCurve


def generate_pr_curve(ground_truths: Sequence[ImageAnnotation], predictions: Sequence[ImageAnnotation], iou_threshold: float) -> PrecisionRecallCurve:
	"""
	Returns a precision-recall curve for the given ground truth and prediction annotation lists evaluated with the given
	IOU threshold.

	Note: this handles instances only; multi-instances are ignored.
	"""
	precision_recall_curve = PrecisionRecallCurve()
	for ground_truth, prediction in zip(ground_truths, predictions):
		add_annotation_to_pr_curve(precision_recall_curve, ground_truth, prediction, iou_threshold)
	return precision_recall_curve

def generate_confusion_matrix(
	template: ImageAnnotationTemplate,
	ground_truths: Sequence[ImageAnnotation],
	predictions: Sequence[ImageAnnotation],
	iou_threshold: float,
	confidence_threshold: float
) -> ConfusionMatrix:
	"""
	Returns a confusion matrix for the given ground truth and prediction annotation lists evaluated with the given IOU
	threshold.

	Note: this handles instances only; multi-instances are ignored.
	"""
	confusion_matrix = ConfusionMatrix(sorted(template.classes.keys()))
	for ground_truth, prediction in zip(ground_truths, predictions):
		add_annotation_to_confusion_matrix(
			confusion_matrix,
			ground_truth,
			prediction,
			iou_threshold,
			confidence_threshold
		)
	return confusion_matrix

class PredictionBox(NamedTuple):
	confidence: float
	class_name: str
	box: Rectangle

class GroundTruthBox(NamedTuple):
	class_name: str
	box: Rectangle

def add_annotation_to_pr_curve(
	precision_recall_curve: PrecisionRecallCurve,
	ground_truth: ImageAnnotation,
	prediction: ImageAnnotation,
	iou_threshold: float
) -> None:
	"""
	Returns a precision-recall curve for the given ground truth and prediction annotations evaluated with the given
	IOU threshold.  Note that multi-instances are ignored.

	Note: this handles instances only; multi-instances are ignored.
	"""
	ground_truth_boxes = [
		GroundTruthBox(class_name, instance.bounding_box)
		for class_name in ground_truth.classes.keys()
		for instance in ground_truth.classes[class_name].instances
	]

	prediction_boxes = sorted([
		PredictionBox(instance.confidence or 0, class_name, instance.bounding_box)
		for class_name in prediction.classes.keys()
		for instance in prediction.classes[class_name].instances
	], reverse = True, key = lambda p: p.confidence)

	iou_matrix = np.array([
		[ground_truth_box.box.iou(prediction_box.box) for ground_truth_box in ground_truth_boxes]
		for prediction_box in prediction_boxes
	])

	precision_recall_curve.add_ground_truth_positives(len(ground_truth_boxes))

	previous_true_positives = 0
	previous_false_positives = 0

	for i in range(len(prediction_boxes)):
		confidence_threshold = prediction_boxes[i].confidence

		if i < len(prediction_boxes) - 1 and prediction_boxes[i+1].confidence == confidence_threshold:
			continue

		prediction_indices, ground_truth_indices = linear_sum_assignment(iou_matrix[:i+1,], maximize = True)

		true_positives = 0
		false_positives = max(0, i + 1 - len(ground_truth_boxes))

		for prediction_index, ground_truth_index in zip(prediction_indices, ground_truth_indices):
			if (
				iou_matrix[prediction_index, ground_truth_index] >= iou_threshold
				and prediction_boxes[prediction_index].class_name == ground_truth_boxes[ground_truth_index].class_name
			):
				true_positives += 1
			else:
				false_positives += 1

		precision_recall_curve.add_event(confidence_threshold, DetectionEvent(
			true_positive_delta = true_positives - previous_true_positives,
			false_positive_delta = false_positives - previous_false_positives
		))

		previous_true_positives = true_positives
		previous_false_positives = false_positives

def add_annotation_to_confusion_matrix(
	confusion_matrix: ConfusionMatrix,
	ground_truth: ImageAnnotation,
	prediction: ImageAnnotation,
	iou_threshold: float,
	confidence_threshold: float
) -> None:
	"""
	Returns a confusion matrix for the given ground truth and prediction annotations evaluated with the given IOU
	threshold, only considering instances meeting the given confidence threshold.  Note that multi-instances are
	ignored.

	Note: this handles instances only; multi-instances are ignored.
	"""
	ground_truth_boxes = [
		GroundTruthBox(class_name, instance.bounding_box)
		for class_name in ground_truth.classes.keys()
		for instance in ground_truth.classes[class_name].instances
	]

	prediction_boxes = sorted([
		PredictionBox(instance.confidence or 0, class_name, instance.bounding_box)
		for class_name in prediction.classes.keys()
		for instance in prediction.classes[class_name].instances
		if instance.confidence is not None and instance.confidence >= confidence_threshold
	], reverse = True, key = lambda p: p.confidence)

	iou_matrix = np.array([
		[ground_truth_box.box.iou(prediction_box.box) for ground_truth_box in ground_truth_boxes]
		for prediction_box in prediction_boxes
	], ndmin = 2)

	prediction_indices, ground_truth_indices = linear_sum_assignment(iou_matrix, maximize = True)
	remaining_ground_truth_boxes = set(ground_truth_boxes)
	remaining_prediction_boxes = set(prediction_boxes)

	for prediction_index, ground_truth_index in zip(prediction_indices, ground_truth_indices):
		if iou_matrix[prediction_index, ground_truth_index] >= iou_threshold:
			ground_truth_box = ground_truth_boxes[ground_truth_index]
			prediction_box = prediction_boxes[prediction_index]
			confusion_matrix.add_detection(ground_truth_box.class_name, prediction_box.class_name)
			remaining_ground_truth_boxes.remove(ground_truth_box)
			remaining_prediction_boxes.remove(prediction_box)

	for ground_truth_box in remaining_ground_truth_boxes:
		confusion_matrix.add_false_negative(ground_truth_box.class_name)

	for prediction_box in remaining_prediction_boxes:
		confusion_matrix.add_false_positive(prediction_box.class_name)
