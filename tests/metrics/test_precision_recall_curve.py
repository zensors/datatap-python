# pyright: reportPrivateUsage=false

from datatap.metrics.precision_recall_curve import _DetectionEvent as DetectionEvent, MaximizeF1Result, PrecisionRecallCurve

import unittest

class TestPrecisionRecallCurve(unittest.TestCase):
	def test_add(self):
		a = PrecisionRecallCurve()
		a._add_event(0.1, DetectionEvent(0, 1))
		a._add_event(0.8, DetectionEvent(1, -1))
		a._add_ground_truth_positives(3)

		b = PrecisionRecallCurve()
		b._add_event(0.25, DetectionEvent(1, 0))
		b._add_event(0.6, DetectionEvent(0, -1))
		b._add_ground_truth_positives(2)

		c = a + b
		self.assertEqual(c.ground_truth_positives, 5)
		self.assertEqual(c.events, {
			0.1: DetectionEvent(0, 1),
			0.25: DetectionEvent(1, 0),
			0.6: DetectionEvent(0, -1),
			0.8: DetectionEvent(1, -1)
		})

	def test_maximize_f1(self):
		pr = PrecisionRecallCurve()
		pr._add_ground_truth_positives(5)
		pr._add_event(0.1, DetectionEvent(0, 1))  # p = 4/6, r = 4/5, f1 = 8/11
		pr._add_event(0.25, DetectionEvent(1, 0)) # p = 4/5, r = 4/5, f1 = 4/5
		pr._add_event(0.6, DetectionEvent(2, -1)) # p = 3/4, r = 3/5, f1 = 2/3
		pr._add_event(0.72, DetectionEvent(0, 1)) # p = 1/3, r = 1/5, f1 = 1/4
		pr._add_event(0.8, DetectionEvent(1, 0))  # p = 1/2, r = 1/5, f1 = 2/7
		pr._add_event(0.9, DetectionEvent(0, 1))  # p = 0/1, r = 0/5, f1 = 0
		self.assertEqual(pr.maximize_f1(), MaximizeF1Result(threshold = 0.25, precision = 0.8, recall = 0.8, f1 = 0.8))

if __name__ == "__main__":
	unittest.main()
