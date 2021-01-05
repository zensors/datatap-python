from __future__ import annotations

from typing import Iterable, Sequence, TYPE_CHECKING, Any, List, NamedTuple, Optional, cast, overload

import numpy as np
from scipy.optimize import linear_sum_assignment
from sortedcontainers import SortedDict

from datatap.droplet import ImageAnnotation

from ._types import GroundTruthBox, PredictionBox

if TYPE_CHECKING:
	import matplotlib.pyplot as plt

class MaximizeF1Result(NamedTuple):
	"""
	Represents the precision, recall, and f1 for a given `PrecisionRecallCurve`
	at the threshold that maximizes f1.
	"""
	threshold: float
	precision: float
	recall: float
	f1: float

class _PrecisionRecallPoint(NamedTuple):
	threshold: float
	precision: float
	recall: float

class _DetectionEvent(NamedTuple):
	true_positive_delta: int
	false_positive_delta: int

	@overload
	def __add__(self, other: _DetectionEvent) -> _DetectionEvent: ...
	def __add__(self, other: Any) -> _DetectionEvent:
		if isinstance(other, _DetectionEvent):
			return _DetectionEvent(self.true_positive_delta + other.true_positive_delta, self.false_positive_delta + other.false_positive_delta)
		return NotImplemented


class PrecisionRecallCurve:
	"""
	Represents a curve relating a chosen detection threshold to precision and recall.  Internally, this is actually
	stored as a sorted list of detection events, which are used to compute metrics on the fly when needed.
	"""

	# TODO(mdsavage): make this accept matching strategies other than bounding box IOU

	events: SortedDict[float, _DetectionEvent]
	ground_truth_positives: int

	def __init__(self, events: Optional[SortedDict[float, _DetectionEvent]] = None, ground_truth_positives: int = 0):
		self.events = SortedDict() if events is None else events
		self.ground_truth_positives = ground_truth_positives

	def clone(self) -> PrecisionRecallCurve:
		return PrecisionRecallCurve(self.events.copy(), self.ground_truth_positives)

	def maximize_f1(self) -> MaximizeF1Result:
		maximum = MaximizeF1Result(threshold = 1, precision = 0, recall = 0, f1 = 0)

		for threshold, precision, recall in self._compute_curve():
			f1 = 2 / ((1 / precision) + (1 / recall)) if precision > 0 and recall > 0 else 0
			if f1 >= maximum.f1:
				maximum = MaximizeF1Result(threshold = threshold, precision = precision, recall = recall, f1 = f1)

		return maximum

	def plot(self) -> plt.Figure:
		import matplotlib.pyplot as plt
		fig = plt.figure()
		curve = self._compute_curve()
		plt.plot([pt.recall for pt in curve], [pt.precision for pt in curve], "o-")
		plt.xlabel("Recall")
		plt.ylabel("Precision")
		return fig

	def add_annotation(
		self: PrecisionRecallCurve,
		ground_truth: ImageAnnotation,
		prediction: ImageAnnotation,
		iou_threshold: float
	) -> None:
		"""
		Returns a precision-recall curve for the given ground truth and prediction annotations evaluated with the given
		IOU threshold.

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
			if instance.bounding_box is not None
		], reverse = True, key = lambda p: p.confidence)

		iou_matrix = np.array([
			[ground_truth_box.box.iou(prediction_box.box) for ground_truth_box in ground_truth_boxes]
			for prediction_box in prediction_boxes
		])

		self._add_ground_truth_positives(len(ground_truth_boxes))

		previous_true_positives = 0
		previous_false_positives = 0

		for i in range(len(prediction_boxes)):
			confidence_threshold = prediction_boxes[i].confidence

			if i < len(prediction_boxes) - 1 and prediction_boxes[i+1].confidence == confidence_threshold:
				continue

			prediction_indices, ground_truth_indices = linear_sum_assignment(iou_matrix[:i+1,], maximize = True)

			true_positives = 0
			false_positives = max(0, i + 1 - len(ground_truth_boxes))

			for prediction_index, ground_truth_index in zip(cast(Iterable[int], prediction_indices), cast(Iterable[int], ground_truth_indices)):
				if (
					iou_matrix[prediction_index, ground_truth_index] >= iou_threshold
					and prediction_boxes[prediction_index].class_name == ground_truth_boxes[ground_truth_index].class_name
				):
					true_positives += 1
				else:
					false_positives += 1

			self._add_event(confidence_threshold, _DetectionEvent(
				true_positive_delta = true_positives - previous_true_positives,
				false_positive_delta = false_positives - previous_false_positives
			))

			previous_true_positives = true_positives
			previous_false_positives = false_positives

	def batch_add_annotation(
		self: PrecisionRecallCurve,
		ground_truths: Sequence[ImageAnnotation],
		predictions: Sequence[ImageAnnotation],
		iou_threshold: float
	) -> None:
		"""
		Updates this precision-recall curve with the values from several annotations simultaneously.
		"""
		for ground_truth, prediction in zip(ground_truths, predictions):
			self.add_annotation(ground_truth, prediction, iou_threshold)

	def _compute_curve(self) -> List[_PrecisionRecallPoint]:
		assert self.ground_truth_positives > 0
		precision_recall_points: List[_PrecisionRecallPoint] = []

		true_positives = 0
		detections = 0

		for threshold in reversed(self.events):
			true_positive_delta, false_positive_delta = self.events[threshold]
			true_positives += true_positive_delta
			detections += true_positive_delta + false_positive_delta
			assert detections > 0

			precision_recall_points.append(_PrecisionRecallPoint(
				threshold = threshold,
				precision = true_positives / detections,
				recall = true_positives / self.ground_truth_positives
			))

		return precision_recall_points

	def _add_event(self, threshold: float, event: _DetectionEvent) -> None:
		if threshold not in self.events:
			self.events[threshold] = _DetectionEvent(0, 0)
		self.events[threshold] += event

	def _add_ground_truth_positives(self, count: int) -> None:
		self.ground_truth_positives += count

	@overload
	def __add__(self, other: PrecisionRecallCurve) -> PrecisionRecallCurve: ...
	def __add__(self, other: Any) -> PrecisionRecallCurve:
		if isinstance(other, PrecisionRecallCurve):
			ret = self.clone()
			ret._add_ground_truth_positives(other.ground_truth_positives)

			for threshold, event in other.events.items():
				ret._add_event(threshold, event)

			return ret
		return NotImplemented

