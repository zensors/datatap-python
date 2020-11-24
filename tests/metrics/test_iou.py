import unittest

import numpy as np
from datatap.droplet import (BoundingBox, ClassAnnotation, Image,
                                 ImageAnnotation, Instance)
from datatap.geometry import Point, Rectangle
from datatap.metrics.confusion_matrix import ConfusionMatrix
from datatap.metrics.iou import (generate_confusion_matrix,
                                     generate_pr_curve)
from datatap.metrics.precision_recall_curve import (_DetectionEvent as DetectionEvent,
                                                        PrecisionRecallCurve)
from datatap.template import (ClassAnnotationTemplate,
                                  ImageAnnotationTemplate, InstanceTemplate)

tpl = ImageAnnotationTemplate(
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

gt1 = ImageAnnotation(
	image = im,
	classes = {
		"a": ClassAnnotation(
			instances = [
				Instance(bounding_box = BoundingBox(Rectangle(Point(0.5, 0.5), Point(0.7, 0.7)))),
				Instance(bounding_box = BoundingBox(Rectangle(Point(0.1, 0.1), Point(0.2, 0.2))))
			]
		),
		"b": ClassAnnotation(
			instances = [
				Instance(bounding_box = BoundingBox(Rectangle(Point(0.6, 0.5), Point(0.7, 0.7))))
			]
		)
	}
)

pred1 = ImageAnnotation(
	image = im,
	classes = {
		"a": ClassAnnotation(
			instances = [
				Instance(bounding_box = BoundingBox(Rectangle(Point(0.58, 0.5), Point(0.7, 0.7)), confidence = 0.7)),
				Instance(bounding_box = BoundingBox(Rectangle(Point(0.1, 0.1), Point(0.18, 0.19)), confidence = 0.9))
			]
		),
		"b": ClassAnnotation(
			instances = [
				Instance(bounding_box = BoundingBox(Rectangle(Point(0.6, 0.5), Point(0.7, 0.7)), confidence = 0.6)),
				Instance(bounding_box = BoundingBox(Rectangle(Point(0.1, 0.8), Point(0.2, 0.9)), confidence = 0.2))
			]
		)
	}
)

gt2 = ImageAnnotation(
	image = im,
	classes = {
		"a": ClassAnnotation(
			instances = [
				Instance(bounding_box = BoundingBox(Rectangle(Point(0.1, 0.1), Point(0.4, 0.4)))),
			]
		),
		"b": ClassAnnotation(
			instances = []
		)
	}
)

pred2 = ImageAnnotation(
	image = im,
	classes = {
		"a": ClassAnnotation(
			instances = [
				Instance(bounding_box = BoundingBox(Rectangle(Point(0.1, 0.12), Point(0.37, 0.4)), confidence = 0.8)),
				Instance(bounding_box = BoundingBox(Rectangle(Point(0.09, 0.08), Point(0.39, 0.4)), confidence = 0.6))
			]
		),
		"b": ClassAnnotation(
			instances = [
				Instance(bounding_box = BoundingBox(Rectangle(Point(0.6, 0), Point(0.8, 0.2)), confidence = 0.3))
			]
		)
	}
)

class TestIou(unittest.TestCase):
	def test_add_annotation_to_pr_curve_1(self):
		pr = PrecisionRecallCurve()
		pr.add_annotation(ground_truth = gt1, prediction = pred1, iou_threshold = 0.3)
		self.assertEqual(pr.events, {
			0.2: DetectionEvent(0, 1),
			0.6: DetectionEvent(2, -1),
			0.7: DetectionEvent(0, 1),
			0.9: DetectionEvent(1, 0)
		})

	def test_add_annotation_to_pr_curve_2(self):
		pr = PrecisionRecallCurve()
		pr.add_annotation(ground_truth = gt2, prediction = pred2, iou_threshold = 0.3)
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
		cm.add_annotation(
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
		cm.add_annotation(
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
		cm.add_annotation(
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
		cm.add_annotation(
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
