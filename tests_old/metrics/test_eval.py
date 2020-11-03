from mldl.metrics.eval import *
from mldl.droplet import Instance, ClassAnnotation, Image, Annotation

BASE_INSTANCE = Instance.from_json({"boundingBox": [[0.0, 0.0], [1.0, 1.0]]})
TEST_1_INSTANCE = Instance.from_json({"boundingBox": [[0.0, 0.0], [1.0, 1.0]], "confidence": 1.0})
TEST_2_INSTANCE_1 = Instance.from_json({"boundingBox": [[0.0, 0.0], [1.0, 1.0]], "confidence": 1.0})
TEST_2_INSTANCE_2 = Instance.from_json({"boundingBox": [[0.0, 0.0], [1.0, 1.0]], "confidence": 1.0})
TEST_4_INSTANCE_1 = Instance.from_json({"boundingBox": [[0.0, 0.0], [1.0, 1.0]], "confidence": 1.0})
TEST_4_INSTANCE_2 = Instance.from_json({"boundingBox": [[0.0, 0.0], [1.0, 1.0]], "confidence": 0.5})
TEST_4_INSTANCE_3 = Instance.from_json({"boundingBox": [[0.0, 0.0], [1.0, 1.0]], "confidence": 0.3})
TEST_5_INSTANCE_1 = Instance.from_json({"boundingBox": [[0.0, 0.0], [1.0, 1.0]], "confidence": 1.0})
TEST_5_INSTANCE_2 = Instance.from_json({"boundingBox": [[0.5, 0.5], [1.0, 1.0]], "confidence": 0.5})

BASE = Annotation(
    image = Image(paths = ["./test.jpg"]),
    classes = {
        "person": ClassAnnotation(instances = [BASE_INSTANCE], clusters = [])
    }
)

TEST_1 = Annotation(
    image = Image(paths = ["./test.jpg"]),
    classes = {
        "person": ClassAnnotation(instances = [TEST_1_INSTANCE], clusters = [])
    }
)

TEST_2 = Annotation(
    image = Image(paths = ["./test.jpg"]),
    classes = {
        "person": ClassAnnotation(instances = [TEST_2_INSTANCE_1, TEST_2_INSTANCE_2], clusters = [])
    }
)

TEST_3 = Annotation(
    image = Image(paths = ["./test.jpg"]),
    classes = {
        "person": ClassAnnotation(instances = [], clusters = [])
    }
)

TEST_4 = Annotation(
    image = Image(paths = ["./test.jpg"]),
    classes = {
        "person": ClassAnnotation(instances = [TEST_4_INSTANCE_1, TEST_4_INSTANCE_2, TEST_4_INSTANCE_3], clusters = [])
    }
)

TEST_5 = Annotation(
    image = Image(paths = ["./test.jpg"]),
    classes = {
        "person": ClassAnnotation(instances = [TEST_5_INSTANCE_1, TEST_5_INSTANCE_2], clusters = []),
        "cat": ClassAnnotation(instances = [TEST_5_INSTANCE_1], clusters = [])
    }
)

def test_threshold():
    assert estimate_threshold([BASE], [TEST_1]) == 0.5
    assert estimate_threshold([BASE], [TEST_3]) == 0.5
    assert estimate_threshold([BASE], [TEST_4]) == 0.75


def test_stats():
    result = compute_class_statistics([BASE], [TEST_4], confidence_threshold = 0.5)
    assert result["person"].true_positives == 1
    assert result["person"].false_positives == 1


def test_metrics():
    result = compute_global_metrics([BASE], [TEST_1])
    assert result.bias == 0

    result = compute_class_metrics([BASE], [TEST_1])
    assert result["person"].bias == 0


def test_confustion_matrix():
    result = compute_confusion_matrix([BASE], [TEST_3], ["__background__", "person"])
    np.testing.assert_equal(result.matrix, [
        [0, 0],
        [1, 0]
    ])
    result = compute_confusion_matrix([BASE], [TEST_5], ["__background__", "person", "cat"])
    np.testing.assert_equal(result.matrix, [
        [0, 1, 1],
        [0, 1, 0],
        [0, 0, 0]
    ])