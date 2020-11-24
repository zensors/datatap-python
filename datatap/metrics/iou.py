from datatap.metrics.confusion_matrix import ConfusionMatrix
from typing import Sequence

from ..droplet import ImageAnnotation
from ..template import ImageAnnotationTemplate
from .precision_recall_curve import PrecisionRecallCurve


def generate_pr_curve(ground_truths: Sequence[ImageAnnotation], predictions: Sequence[ImageAnnotation], iou_threshold: float) -> PrecisionRecallCurve:
	"""
	Returns a precision-recall curve for the given ground truth and prediction annotation lists evaluated with the given
	IOU threshold.

	Note: this handles instances only; multi-instances are ignored.
	"""
	precision_recall_curve = PrecisionRecallCurve()
	precision_recall_curve.batch_add_annotation(ground_truths, predictions, iou_threshold)
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
	confusion_matrix.batch_add_annotation(ground_truths, predictions, iou_threshold, confidence_threshold)
	return confusion_matrix
