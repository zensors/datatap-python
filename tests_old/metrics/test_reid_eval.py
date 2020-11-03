import pytest
import numpy as np
from mldl.metrics.reid_eval import ReidMetrics

query_ids1 = ["1", "2", "3"]
gallery_ids1 = ["4", "2", "2", "1", "5", "3", "1"]
distances1 = np.array([
    [16, 20, 5, 19, 1, 7, 14],
    [18, 8, 17, 0, 13, 12, 3],
    [11, 6, 15, 9, 4, 2, 10]
])
metrics1 = ReidMetrics(distances1, query_ids1, gallery_ids1)

query_ids2 = ["1", "2", "3"]
gallery_ids2 = ["4", "1", "5", "3", "3", "6"]
distances2 = np.array([
    [4, 5, 15, 2, 6, 10],
    [17, 0, 14, 16, 11, 8],
    [12, 13, 7, 9, 1, 3]
])
metrics2 = ReidMetrics(distances2, query_ids2, gallery_ids2)

def test_map():
    global metrics1, metrics2
    assert metrics1.pr_curve.get_average_precision() == pytest.approx((1 + 7/24 + 1/3) / 3)
    assert metrics2.pr_curve.get_average_precision() == pytest.approx((1/3 + 3/4) / 2)


def test_top_k_accuracy():
    global metrics1, metrics2
    assert metrics1.compute_accuracy_at_top_k(1) == pytest.approx(1/3)
    assert metrics1.compute_accuracy_at_top_k(3) == pytest.approx(2/3)
    assert metrics1.compute_accuracy_at_top_k(5) == pytest.approx(3/3)
    assert metrics2.compute_accuracy_at_top_k(1) == pytest.approx(1/2)
    assert metrics2.compute_accuracy_at_top_k(3) == pytest.approx(2/2)
    assert metrics2.compute_accuracy_at_top_k(5) == pytest.approx(2/2)


def test_distance_threshold_top_1():
    global metrics1, metrics2
    assert metrics1.compute_distance_threshold_top_1() == 2
    assert metrics2.compute_distance_threshold_top_1() == 1