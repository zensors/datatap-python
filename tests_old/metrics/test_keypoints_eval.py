import numpy as np
import pytest

from mldl.metrics.metrics import PrecisionRecallCurve
from mldl.metrics.keypoints_eval import *
from mldl.droplet import Instance, Annotation, Keypoint, ClassAnnotation, Image

GT_INSTANCE1 = Instance.from_json({
    "boundingBox": [[0, 0], [0.5, 0.5]],
    "keypoints": {
        "point1": {"point": [0.1, 0.1], "occluded": False},
        "point2": {"point": [0.3, 0.1], "occluded": False},
        "point3": {"point": [0.3, 0.3], "occluded": False},
    },
})

GT_INSTANCE2 = Instance.from_json({
    "boundingBox": [[0, 0], [1, 1]],
    "keypoints": {
        "point1": {"point": [0.6, 0.6], "occluded": False},
        "point2": {"point": [0.8, 0.6], "occluded": False},
        "point3": {"point": [0.8, 0.8], "occluded": False},
    },
})

DT_INSTANCE1 = Instance.from_json({
    "boundingBox": [[0, 0], [0.5, 0.5]],
    "keypoints": {
        "point1": {"point": [0.1, 0.4], "occluded": False, "confidence": 1 / 9},
        "point2": {"point": [0.33, 0.1], "occluded": False, "confidence": 2 / 9},
        "point3": {"point": [0.2, 0.4], "occluded": False, "confidence": 4 / 9},
    },
})

DT_INSTANCE2 = Instance.from_json({
    "boundingBox": [[0.5, 0], [1, 1]],
    "keypoints": {
        "point1": {"point": [0.6, 0.1], "occluded": False, "confidence": 6 / 9},
        "point2": {"point": [0.8, 0.67], "occluded": False},
        "point3": {"point": [0.8, 0.1], "occluded": False, "confidence": 8 / 9},
    },
})

DT_INSTANCE3 = Instance.from_json({
    "boundingBox": [[0, 0], [1, 1]],
    "keypoints": {
        "point1": {"point": [0.6, 0.6], "occluded": False, "confidence": 3 / 9},
        "point2": {"point": [0.8, 0.6], "occluded": False, "confidence": 7 / 9},
        "point3": {"point": [0.9, 0.8], "occluded": False, "confidence": 5 / 9},
    },
})

GT_IMAGE = Image(paths = ["../fake_path.jpg"])

DT_IMAGE = Image(paths = ["../another_fake_path.jpg"])

GT = Annotation(
    image = GT_IMAGE,
    classes = {
        "triangle": ClassAnnotation(instances = [GT_INSTANCE1, GT_INSTANCE2], clusters = [])
    }
)

DT = Annotation(
    image = DT_IMAGE,
    classes = {
        "triangle": ClassAnnotation(instances = [DT_INSTANCE1, DT_INSTANCE2, DT_INSTANCE3], clusters = [])
    }
)


def test_average_confidence():
    assert average_keypoint_confidence(DT_INSTANCE1) == pytest.approx(7 / 27)
    assert average_keypoint_confidence(DT_INSTANCE2) == pytest.approx(23 / 27)
    assert average_keypoint_confidence(DT_INSTANCE3) == pytest.approx(5 / 9)


def test_is_correct_keypoint():
    assert not is_correct_keypoint(GT_INSTANCE1, DT_INSTANCE1, "point1", 0.05)
    assert is_correct_keypoint(GT_INSTANCE1, DT_INSTANCE1, "point2", 0.05)
    assert not is_correct_keypoint(GT_INSTANCE1, DT_INSTANCE1, "point3", 0.05)
    assert not is_correct_keypoint(GT_INSTANCE2, DT_INSTANCE2, "point1", 0.05)
    assert is_correct_keypoint(GT_INSTANCE2, DT_INSTANCE2, "point2", 0.05)
    assert not is_correct_keypoint(GT_INSTANCE2, DT_INSTANCE2, "point3", 0.05)
    assert is_correct_keypoint(GT_INSTANCE2, DT_INSTANCE3, "point1", 0.05)
    assert is_correct_keypoint(GT_INSTANCE2, DT_INSTANCE3, "point2", 0.05)
    assert not is_correct_keypoint(GT_INSTANCE2, DT_INSTANCE3, "point3", 0.05)

    assert not is_correct_keypoint(GT_INSTANCE1, DT_INSTANCE1, "point2", 0.03)
    assert not is_correct_keypoint(GT_INSTANCE2, DT_INSTANCE2, "point2", 0.03)
    assert is_correct_keypoint(GT_INSTANCE2, DT_INSTANCE3, "point1", 0.01)
    assert is_correct_keypoint(GT_INSTANCE2, DT_INSTANCE3, "point2", 0.01)


def test_count_correct_keypoints():
    assert count_correct_keypoints(GT_INSTANCE1, DT_INSTANCE1, 0.05) == 1
    assert count_correct_keypoints(GT_INSTANCE2, DT_INSTANCE2, 0.05) == 1
    assert count_correct_keypoints(GT_INSTANCE2, DT_INSTANCE3, 0.05) == 2


def test_evaluate_image_on_class():
    result = evaluate_image_on_class(GT, DT, "triangle", [0.05, 4.0], ["point1", "point2", "point3"])
    np.testing.assert_allclose(
        result.pr_per_threshold[0.05].precision_vals,
        [1, 0/1, 0/2, 1/3, 1/4, 1/5, 1/6, 2/7, 3/8, 3/9, 0]
    )
    np.testing.assert_allclose(
        result.pr_per_threshold[4.0].precision_vals,
        [1, 1/1, 2/2, 3/3, 4/4, 5/5, 5/6, 6/7, 6/8, 6/9, 0]
    )
    np.testing.assert_allclose(
        result.pr_per_threshold[0.05].recall_vals,
        [0, 0/6, 0/6, 1/6, 1/6, 1/6, 1/6, 2/6, 3/6, 3/6, 1]
    )
    np.testing.assert_allclose(
        result.pr_per_threshold[4.0].recall_vals,
        [0, 1/6, 2/6, 3/6, 4/6, 5/6, 5/6, 6/6, 6/6, 6/6, 1]
    )
    assert result.pr_per_threshold[0.05].get_average_precision() == pytest.approx(167/1008)
    assert result.pr_per_threshold[4.0].get_average_precision() == pytest.approx(41/42)
    print(result.pr_per_keypoint_per_threshold["point1"][0.05].precision_vals)
    print(result.pr_per_keypoint_per_threshold["point1"][0.05].recall_vals)
    print(result.pr_per_keypoint_per_threshold["point1"][0.05].confidence_vals)
    assert result.pr_per_keypoint_per_threshold["point1"][0.05].get_average_precision() == pytest.approx(1/4)
    assert result.pr_per_keypoint_per_threshold["point1"][4.0].get_average_precision() == pytest.approx(1)
    assert result.pr_per_keypoint_per_threshold["point2"][0.05].get_average_precision() == pytest.approx(7/12)
    assert result.pr_per_keypoint_per_threshold["point2"][4.0].get_average_precision() == pytest.approx(1)
    assert result.pr_per_keypoint_per_threshold["point3"][0.05].get_average_precision() == pytest.approx(0)
    assert result.pr_per_keypoint_per_threshold["point3"][4.0].get_average_precision() == pytest.approx(1)


def test_interpolate_pr_curve():
    precision_curve = [1, 0/1, 1/2, 1/3, 1/4, 2/5]
    recall_curve = [0, 0/4, 1/4, 1/4, 1/4, 2/4]
    confidence_curve = [1, 0.9, 0.8, 0.7, 0.6, 0.5]

    PR1 = PrecisionRecallCurve(precision_vals = precision_curve, recall_vals = recall_curve, confidence_vals = confidence_curve)
    PR1.interpolate(6)
    interpolated_precision_curve = [1, 1/2, 2/5, 2/5, 0, 0, 0]
    interpolated_recall_curve = [0, 1/6, 2/6, 3/6, 4/6, 5/6, 6/6]
    interpolated_confidence_curve = [1, 0.8, 0.5, 0.5, 0, 0, 0]
    assert PR1.precision_vals == interpolated_precision_curve
    assert PR1.recall_vals == interpolated_recall_curve
    assert PR1.confidence_vals == interpolated_confidence_curve

    PR2 = PrecisionRecallCurve(precision_vals = precision_curve, recall_vals = recall_curve, confidence_vals = confidence_curve)
    PR2.interpolate(4)
    interpolated_precision_curve = [1, 1/2, 2/5, 0, 0]
    interpolated_recall_curve = [0, 1/4, 2/4, 3/4, 4/4]
    interpolated_confidence_curve = [1, 0.8, 0.5, 0, 0]
    assert PR2.precision_vals == interpolated_precision_curve
    assert PR2.recall_vals == interpolated_recall_curve
    assert PR2.confidence_vals == interpolated_confidence_curve


def test_estimate_f1_and_threshold():
    precision_curve = [1, 0/1, 1/2, 1/3, 1/4, 2/5]
    recall_curve = [0, 0/4, 1/4, 1/4, 1/4, 2/4]
    confidence_curve = [1, 0.9, 0.8, 0.7, 0.6, 0.5]

    PR = PrecisionRecallCurve(precision_vals = precision_curve, recall_vals = recall_curve, confidence_vals = confidence_curve)
    f1, confidence_threshold = PR.get_f1_and_threshold()
    assert f1 == pytest.approx(4/9)
    assert confidence_threshold == 0.5
