from __future__ import annotations

from typing import TYPE_CHECKING, Any, List, NamedTuple, Optional, overload

from sortedcontainers import SortedDict

if TYPE_CHECKING:
	import matplotlib.pyplot as plt

class DetectionEvent(NamedTuple):
	true_positive_delta: int
	false_positive_delta: int

	@overload
	def __add__(self, other: DetectionEvent) -> DetectionEvent: ...
	def __add__(self, other: Any):
		if isinstance(other, DetectionEvent):
			return DetectionEvent(self.true_positive_delta + other.true_positive_delta, self.false_positive_delta + other.false_positive_delta)
		return NotImplemented

class MaximizeF1Result(NamedTuple):
	threshold: float
	precision: float
	recall: float
	f1: float

class PrecisionRecallPoint(NamedTuple):
	threshold: float
	precision: float
	recall: float

class PrecisionRecallCurve:
	"""
	Represents a curve relating a chosen detection threshold to precision and recall.  Internally, this is actually
	stored as a sorted list of detection events, which are used to compute metrics on the fly when needed.
	"""

	events: SortedDict[float, DetectionEvent]
	ground_truth_positives: int

	def __init__(self, events: Optional[SortedDict[float, DetectionEvent]] = None, ground_truth_positives: int = 0):
		self.events = SortedDict() if events is None else events
		self.ground_truth_positives = ground_truth_positives

	def clone(self) -> PrecisionRecallCurve:
		return PrecisionRecallCurve(self.events.copy(), self.ground_truth_positives)

	def add_event(self, threshold: float, event: DetectionEvent):
		if threshold not in self.events:
			self.events[threshold] = DetectionEvent(0, 0)
		self.events[threshold] += event

	def add_ground_truth_positives(self, count: int):
		self.ground_truth_positives += count

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

	def _compute_curve(self) -> List[PrecisionRecallPoint]:
		assert self.ground_truth_positives > 0
		precision_recall_points: List[PrecisionRecallPoint] = []

		true_positives = 0
		detections = 0

		for threshold in reversed(self.events):
			true_positive_delta, false_positive_delta = self.events[threshold]
			true_positives += true_positive_delta
			detections += true_positive_delta + false_positive_delta
			assert detections > 0

			precision_recall_points.append(PrecisionRecallPoint(
				threshold = threshold,
				precision = true_positives / detections,
				recall = true_positives / self.ground_truth_positives
			))

		return precision_recall_points

	@overload
	def __add__(self, other: PrecisionRecallCurve) -> PrecisionRecallCurve: ...
	def __add__(self, other: Any):
		if isinstance(other, PrecisionRecallCurve):
			ret = self.clone()
			ret.add_ground_truth_positives(other.ground_truth_positives)

			for threshold, event in other.events.items():
				ret.add_event(threshold, event)

			return ret
		return NotImplemented

