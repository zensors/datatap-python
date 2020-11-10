from mldl_public.metrics.confusion_matrix import ConfusionMatrix
from mldl_public.template.instance_template import InstanceTemplate
from mldl_public.template.class_annotation_template import ClassAnnotationTemplate
from mldl_public.template.annotation_template import AnnotationTemplate
import unittest

from mldl_public.droplet import Annotation, ClassAnnotation, Image, Instance
from mldl_public.geometry import Point, Rectangle
from mldl_public.metrics.iou import add_annotation_to_confusion_matrix, add_annotation_to_pr_curve, generate_confusion_matrix, generate_pr_curve
from mldl_public.metrics.precision_recall_curve import DetectionEvent, PrecisionRecallCurve

import numpy as np

tpl = AnnotationTemplate(
	classes = {
		"a": ClassAnnotationTemplate(
			instances = InstanceTemplate(bounding_box = True)
		),
		"b": ClassAnnotationTemplate(
			instances = InstanceTemplate(bounding_box = True)
		)
	}
)

im = Image(paths = [])

gt1 = Annotation(
	image = im,
	classes = {
		"a": ClassAnnotation(
			instances = [
				Instance(bounding_box = Rectangle(Point(0.5, 0.5), Point(0.7, 0.7))),
				Instance(bounding_box = Rectangle(Point(0.1, 0.1), Point(0.2, 0.2)))
			]
		),
		"b": ClassAnnotation(
			instances = [
				Instance(bounding_box = Rectangle(Point(0.6, 0.5), Point(0.7, 0.7)))
			]
		)
	}
)

pred1 = Annotation(
	image = im,
	classes = {
		"a": ClassAnnotation(
			instances = [
				Instance(confidence = 0.7, bounding_box = Rectangle(Point(0.58, 0.5), Point(0.7, 0.7))),
				Instance(confidence = 0.9, bounding_box = Rectangle(Point(0.1, 0.1), Point(0.18, 0.19)))
			]
		),
		"b": ClassAnnotation(
			instances = [
				Instance(confidence = 0.6, bounding_box = Rectangle(Point(0.6, 0.5), Point(0.7, 0.7))),
				Instance(confidence = 0.2, bounding_box = Rectangle(Point(0.1, 0.8), Point(0.2, 0.9)))
			]
		)
	}
)

gt2 = Annotation(
	image = im,
	classes = {
		"a": ClassAnnotation(
			instances = [
				Instance(bounding_box = Rectangle(Point(0.1, 0.1), Point(0.4, 0.4))),
			]
		),
		"b": ClassAnnotation(
			instances = []
		)
	}
)

pred2 = Annotation(
	image = im,
	classes = {
		"a": ClassAnnotation(
			instances = [
				Instance(confidence = 0.8, bounding_box = Rectangle(Point(0.1, 0.12), Point(0.37, 0.4))),
				Instance(confidence = 0.6, bounding_box = Rectangle(Point(0.09, 0.08), Point(0.39, 0.4)))
			]
		),
		"b": ClassAnnotation(
			instances = [
				Instance(confidence = 0.3, bounding_box = Rectangle(Point(0.6, 0), Point(0.8, 0.2)))
			]
		)
	}
)

class TestIou(unittest.TestCase):
	def test_add_annotation_to_pr_curve_1(self):
		pr = PrecisionRecallCurve()
		add_annotation_to_pr_curve(precision_recall_curve = pr, ground_truth = gt1, prediction = pred1, iou_threshold = 0.3)
		self.assertEqual(pr.events, {
			0.2: DetectionEvent(0, 1),
			0.6: DetectionEvent(2, -1),
			0.7: DetectionEvent(0, 1),
			0.9: DetectionEvent(1, 0)
		})

	def test_add_annotation_to_pr_curve_2(self):
		pr = PrecisionRecallCurve()
		add_annotation_to_pr_curve(precision_recall_curve = pr, ground_truth = gt2, prediction = pred2, iou_threshold = 0.3)
		self.assertEqual(pr.events, {
			0.3: DetectionEvent(0, 1),
			0.6: DetectionEvent(0, 1),
			0.8: DetectionEvent(1, 0)
		})

	def test_generate_pr_curve(self):
		pr = generate_pr_curve(ground_truths = [gt1, gt2], predictions = [pred1, pred2], iou_threshold = 0.3)
		self.assertEqual(pr.events, {
			0.2: DetectionEvent(0, 1),
			0.3: DetectionEvent(0, 1),
			0.6: DetectionEvent(2, 0),
			0.7: DetectionEvent(0, 1),
			0.8: DetectionEvent(1, 0),
			0.9: DetectionEvent(1, 0)
		})

	def test_add_annotation_to_confusion_matrix_1a(self):
		cm = ConfusionMatrix(sorted(tpl.classes.keys()))
		add_annotation_to_confusion_matrix(
			confusion_matrix = cm,
			ground_truth = gt1,
			prediction = pred1,
			iou_threshold = 0.3,
			confidence_threshold = 0.1
		)
		self.assertTrue(
			np.array_equal(
				cm.matrix,
				np.array([
					[0, 0, 1],
					[0, 2, 0],
					[0, 0, 1]
				])
			)
		)

	def test_add_annotation_to_confusion_matrix_1b(self):
		cm = ConfusionMatrix(sorted(tpl.classes.keys()))
		add_annotation_to_confusion_matrix(
			confusion_matrix = cm,
			ground_truth = gt1,
			prediction = pred1,
			iou_threshold = 0.3,
			confidence_threshold = 0.6
		)
		self.assertTrue(
			np.array_equal(
				cm.matrix,
				np.array([
					[0, 0, 0],
					[0, 2, 0],
					[0, 0, 1]
				])
			)
		)

	def test_add_annotation_to_confusion_matrix_1c(self):
		cm = ConfusionMatrix(sorted(tpl.classes.keys()))
		add_annotation_to_confusion_matrix(
			confusion_matrix = cm,
			ground_truth = gt1,
			prediction = pred1,
			iou_threshold = 0.3,
			confidence_threshold = 0.61
		)
		self.assertTrue(
			np.array_equal(
				cm.matrix,
				np.array([
					[0, 0, 0],
					[1, 1, 0],
					[0, 1, 0]
				])
			)
		)

	def test_add_annotation_to_confusion_matrix_2(self):
		cm = ConfusionMatrix(sorted(tpl.classes.keys()))
		add_annotation_to_confusion_matrix(
			confusion_matrix = cm,
			ground_truth = gt2,
			prediction = pred2,
			iou_threshold = 0.3,
			confidence_threshold = 0.1
		)
		self.assertTrue(
			np.array_equal(
				cm.matrix,
				np.array([
					[0, 1, 1],
					[0, 1, 0],
					[0, 0, 0]
				])
			)
		)

	def test_generate_confusion_matrix(self):
		cm = generate_confusion_matrix(
			template = tpl,
			ground_truths = [gt1, gt2],
			predictions = [pred1, pred2],
			iou_threshold = 0.3,
			confidence_threshold = 0.1
		)
		self.assertTrue(
			np.array_equal(
				cm.matrix,
				np.array([
					[0, 1, 2],
					[0, 3, 0],
					[0, 0, 1]
				])
			)
		)

if __name__ == "__main__":
	unittest.main()
