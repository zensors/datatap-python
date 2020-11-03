from __future__ import annotations  # needed for instance methods to reference other instances of the same class

import numpy as np
import matplotlib.pyplot as plt
from typing import Sequence, List, Optional, Tuple
from enum import Enum

class PrecisionRecallCurve:
    # (precision_vals[i], recall_vals[i], confidence_vals[i])
    # denotes i-th point on curve, sorted by order of computation
    precision_vals: List[float]
    recall_vals: List[float]
    confidence_vals: List[float]

    @staticmethod
    def estimate_pr_curve_average(pr_curves: Sequence[PrecisionRecallCurve], num_intervals: int = 100) -> PrecisionRecallCurve:
        """Average the inputted precision recall curves to a specified resolution."""
        interpolated_precision = np.zeros((len(pr_curves), num_intervals + 1))
        interpolated_confidence = np.zeros((len(pr_curves), num_intervals + 1))
        average_recall_vals = None
        for i in range(len(pr_curves)):
            pr_curves[i].interpolate(num_intervals = num_intervals)
            interpolated_precision[i, :] = pr_curves[i].precision_vals
            interpolated_confidence[i, :] = pr_curves[i].confidence_vals
            average_recall_vals = pr_curves[i].recall_vals
        average_precision_vals = list(np.average(interpolated_precision, 0))
        average_confidence_vals = list(np.average(interpolated_confidence, 0))
        return PrecisionRecallCurve(average_precision_vals, average_recall_vals, average_confidence_vals)

    @staticmethod
    def plot_curves(pr_curves: Sequence[PrecisionRecallCurve], labels: Optional[Sequence[str]] = None) -> plt.Figure:
        fig = plt.figure()
        for i in range(len(pr_curves)):
            plt.plot(pr_curves[i].recall_vals, pr_curves[i].precision_vals, label = labels[i] if labels is not None else None)
        if labels is not None:
            plt.legend(loc="upper right")
        plt.xlabel("Recall")
        plt.ylabel("Precision")
        return fig

    def __init__(self, precision_vals: Optional[List[float]] = None, recall_vals: Optional[List[float]] = None, confidence_vals: Optional[List[float]] = None):
        self.precision_vals = precision_vals or [1, 0]
        self.recall_vals = recall_vals or [0, 1]
        self.confidence_vals = confidence_vals or [1, 0]

    def interpolate(self, num_intervals: int = 100) -> None:
        """Interpolates to recall values of [0, 1/num_intervals, ..., num_intervals/num_intervals]."""
        interpolated_precision = []
        interpolated_recall = []
        interpolated_confidence = []
        point = 0
        for i in range(num_intervals + 1):
            interpolated_recall.append(i / num_intervals)
            while point < len(self.precision_vals) and self.recall_vals[point] < i / num_intervals:
                point += 1
            interpolated_precision.append(0 if point == len(self.precision_vals) else self.precision_vals[point])
            interpolated_confidence.append(0 if point == len(self.confidence_vals) else self.confidence_vals[point])
        self.precision_vals = interpolated_precision
        self.recall_vals = interpolated_recall
        self.confidence_vals = interpolated_confidence

    def get_average_precision(self) -> float:
        ap = 0.0
        for i in range(len(self.precision_vals) - 1):
            ap += self.precision_vals[i + 1] * (self.recall_vals[i + 1] - self.recall_vals[i])
        return ap

    def get_f1_and_threshold(self) -> Tuple[float, float]:
        """
        Compute best possible F1 score (harmonic mean of precision and recall)
        along a precision-recall curve along with the confidence threshold that
        will produce that F1 metric.
        """
        best_f1 = 0.0
        confidence_threshold = 0.5
        for i in range(len(self.precision_vals)):
            if self.precision_vals[i] + self.recall_vals[i] == 0:
                continue
            f1 = 2 * self.precision_vals[i] * self.recall_vals[i] / (self.precision_vals[i] + self.recall_vals[i])
            if f1 >= best_f1:
                best_f1 = f1
                confidence_threshold = self.confidence_vals[i]
        return best_f1, confidence_threshold

    def plot(self) -> plt.Figure:
        fig = plt.figure()
        plt.plot(self.recall_vals, self.precision_vals)
        plt.xlabel("Recall")
        plt.ylabel("Precision")
        return fig


class Detection(Enum):
    TP = 0
    FP = 1


class PrecisionRecallCurveBuilder:
    precision_vals: List[float]
    recall_vals: List[float]
    confidence_vals: List[float]
    num_p: int
    num_tp: int
    num_fp: int

    def __init__(
        self,
        num_p: int,
        num_tp: Optional[int] = None,
        num_fp: Optional[int] = None,
        precision_vals: Optional[List[float]] = None,
        recall_vals: Optional[List[float]] = None,
        confidence_vals: Optional[List[float]] = None
    ):
        assert num_p > 0
        self.num_p = num_p
        self.num_tp = num_tp or 0
        self.num_fp = num_fp or 0
        self.precision_vals = precision_vals or [1, 0]
        self.recall_vals = recall_vals or [0, 1]
        self.confidence_vals = confidence_vals or [1, 0]

    def add_detection(self, detection: Detection, confidence: float) -> None:
        if detection == Detection.TP:
            self.num_tp += 1
        elif detection == Detection.FP:
            self.num_fp += 1
        precision = self.num_tp / (self.num_tp + self.num_fp)
        recall = self.num_tp / self.num_p
        self.precision_vals.insert(-1, precision)
        self.recall_vals.insert(-1, recall)
        self.confidence_vals.insert(-1, confidence)

    def build(self) -> PrecisionRecallCurve:
        return PrecisionRecallCurve(
            precision_vals = self.precision_vals,
            recall_vals = self.recall_vals,
            confidence_vals = self.confidence_vals
        )
