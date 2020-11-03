from __future__ import annotations  # needed for instance methods to reference other instances of the same class

import numpy as np
import collections
import scipy.optimize
from typing import cast, Mapping, Optional, List, Dict, Sequence
try:
	from comet_ml import Experiment
except ImportError:
	Experiment = {}

from mldl.metrics.metrics import PrecisionRecallCurve, PrecisionRecallCurveBuilder, Detection
from mldl.droplet import Instance, Annotation, Keypoint

# Notes:
# - occlusion is not factored in


def average_keypoint_confidence(dt_instance: Instance) -> float:
    if dt_instance.keypoints is None:
        return 0.5
    confidences = [1 if kp.confidence is None else kp.confidence for kp in dt_instance.keypoints.values() if kp is not None]
    return sum(confidences) / len(confidences)


def is_correct_keypoint(gt_instance: Instance, dt_instance: Instance, node_id: str, threshold: float) -> bool:
    """
    Determine whether the two inputted instances agree on the
    keypoint identified by node_id to a given threshold.

    Agreement is determined by a variant of PCK, iff
    (distance btwn keypoints) < threshold * (length of ground truth bbox diagonal)
    """
    assert gt_instance.keypoints is not None and dt_instance.keypoints is not None
    if node_id not in gt_instance.keypoints or node_id not in dt_instance.keypoints:
        return False

    bbox_diag = gt_instance.bounding_box.diagonal()

    gt_point = cast(Keypoint, gt_instance.keypoints[node_id]).point
    dt_point = cast(Keypoint, dt_instance.keypoints[node_id]).point
    return gt_point.distance(dt_point) < threshold * bbox_diag


def count_correct_keypoints(gt_instance: Instance, dt_instance: Instance, threshold: float) -> int:
    """
    Count the total number of keypoints on which the
    two inputted instances agree on within a given threshold.
    """
    assert gt_instance.keypoints is not None and dt_instance.keypoints is not None
    bbox_diag = gt_instance.bounding_box.diagonal()

    num_correct = 0
    for node_id in gt_instance.keypoints:
        if node_id not in dt_instance.keypoints:
            continue
        gt_point = cast(Keypoint, gt_instance.keypoints[node_id]).point
        dt_point = cast(Keypoint, dt_instance.keypoints[node_id]).point
        num_correct += gt_point.distance(dt_point) < threshold * bbox_diag

    return num_correct


class ClassKeypointMetrics:
    pr_per_threshold: Dict[float, PrecisionRecallCurve] = {}
    pr_per_keypoint_per_threshold: Dict[str, Dict[float, PrecisionRecallCurve]] = {}
    class_name: str

    @staticmethod
    def average_kp_metrics(kp_metrics: Sequence[ClassKeypointMetrics]) -> ClassKeypointMetrics:
        keypoint_node_ids = collections.defaultdict(set)
        thresholds = collections.defaultdict(set)
        for i, kp_metric in enumerate(kp_metrics):
            for node_id in kp_metric.pr_per_keypoint_per_threshold:
                keypoint_node_ids[node_id].add(i)
            for threshold in kp_metric.pr_per_threshold:
                thresholds[threshold].add(i)

        average = ClassKeypointMetrics(list(keypoint_node_ids.keys()), list(thresholds.keys()), kp_metrics[0].class_name)

        for threshold, threshold_index_set in thresholds.items():
            average.pr_per_threshold[threshold] = PrecisionRecallCurve.estimate_pr_curve_average(
                [kp_metrics[index].pr_per_threshold[threshold] for index in threshold_index_set]
            )
            for node_id, keypoint_index_set in keypoint_node_ids.items():
                average.pr_per_keypoint_per_threshold[node_id][threshold] = PrecisionRecallCurve.estimate_pr_curve_average(
                    [kp_metrics[index].pr_per_keypoint_per_threshold[node_id][threshold] for index in keypoint_index_set & threshold_index_set]
                )

        return average

    def __init__(
        self, keypoint_node_ids: Sequence[str], thresholds: Sequence[float], class_name: str,
        default_precision_vals: Optional[List[float]] = None,
        default_recall_vals: Optional[List[float]] = None,
        default_confidence_vals: Optional[List[float]] = None
    ):
        self.class_name = class_name
        for threshold in thresholds:
            self.pr_per_threshold[threshold] = PrecisionRecallCurve(precision_vals = default_precision_vals, recall_vals = default_recall_vals)
        for node_id in keypoint_node_ids:
            self.pr_per_keypoint_per_threshold[node_id] = {}
            for threshold in thresholds:
                self.pr_per_keypoint_per_threshold[node_id][threshold] = PrecisionRecallCurve(precision_vals = default_precision_vals, recall_vals = default_recall_vals)

    def log_to_comet(self, experiment: Experiment, step: Optional[int] = None):
        average_pr_curve = PrecisionRecallCurve.estimate_pr_curve_average(list(self.pr_per_threshold.values()))
        experiment.log_metric(f"ap ({self.class_name})", average_pr_curve.get_average_precision(), step = step)
        f1, confidence_threshold = average_pr_curve.get_f1_and_threshold()
        experiment.log_metric(f"kp f1 ({self.class_name})", f1, step = step)
        experiment.log_metric(f"kp confidence threshold ({self.class_name})", confidence_threshold, step = step)
        experiment.log_figure(figure_name = f"average p-r Curve ({self.class_name})", figure = average_pr_curve.plot(), step = step)

        for threshold, curve in self.pr_per_threshold.items():
            experiment.log_metric(f"ap ({self.class_name}, threshold={threshold})", curve.get_average_precision(), step = step)
        experiment.log_figure(figure_name = f"p-r curve per threshold ({self.class_name})", figure = PrecisionRecallCurve.plot_curves(
            list(self.pr_per_threshold.values()),
            [f"t={t}" for t in self.pr_per_threshold.keys()]
        ), step = step)

        averages = []
        for node_id, threshold_to_curve in self.pr_per_keypoint_per_threshold.items():
            average_curve = PrecisionRecallCurve.estimate_pr_curve_average(list(threshold_to_curve.values()))
            experiment.log_metric(f"ap ({self.class_name}, {node_id})", average_curve.get_average_precision(), step = step)
            averages.append(average_curve)
        experiment.log_figure(figure_name = f"p-r curve per keypoint ({self.class_name})", figure = PrecisionRecallCurve.plot_curves(
            averages, list(self.pr_per_keypoint_per_threshold.keys())
        ), step = step)


def evaluate_image_on_class(
    gt_annotation: Annotation,
    dt_annotation: Annotation,
    class_name: str,
    thresholds: Sequence[float],
    keypoint_node_ids: Sequence[str]
) -> ClassKeypointMetrics:
    """
    Compute precision-recall curves for a given class of a pair of 
    keypoint-annotated images over a range of specified thresholds.

    These metrics are calculated as follows for each threshold:
    1. Match predicted instances to ground truth instances to classify each
       predicted keypoint as TP or FP.
    2. Processing all the keypoints in the image in order of decreasing
       confidence to calculate the p-r curves.
    """
    gt_instances = list(filter(lambda instance: instance.keypoints is not None, gt_annotation.classes[class_name].instances))
    dt_instances = list(filter(lambda instance: instance.keypoints is not None, dt_annotation.classes[class_name].instances))

    if len(gt_instances) == 0 and len(dt_instances) == 0:
        return ClassKeypointMetrics(keypoint_node_ids, thresholds, default_precision_vals = [1, 1], default_recall_vals = [0, 1], class_name = class_name)
    elif len(gt_instances) == 0 or len(dt_instances) == 0:
        return ClassKeypointMetrics(keypoint_node_ids, thresholds, default_precision_vals = [1, 0], default_recall_vals = [0, 1], class_name = class_name)

    # Sequence of all predicted keypoints (index of instance, node id, node, confidence) sorted by decreasing confidence
    dt_keypoints = [
        (dt_index, node_id, 1 if node.confidence is None else node.confidence)
        for dt_index, dt_instance in enumerate(dt_instances)
        for node_id, node in cast(Mapping[str, Optional[Keypoint]], dt_instance.keypoints).items()
        if node is not None
    ]
    dt_keypoints = sorted(dt_keypoints, key=lambda kp: kp[2], reverse=True)

    metrics = ClassKeypointMetrics(keypoint_node_ids, thresholds, class_name = class_name)

    for threshold in thresholds:
        score_matrix = np.asarray(
            [[count_correct_keypoints(gt_instance, dt_instance, threshold) + average_keypoint_confidence(dt_instance)
            for gt_instance in gt_instances]
            for dt_instance in dt_instances]
        )
        # match gt instances to dt instances
        dt_matched_inds, gt_matched_inds = scipy.optimize.linear_sum_assignment(score_matrix, maximize=True)
        dt_index_to_gt_instance = {
            dt_index: gt_instances[gt_index]
            for dt_index, gt_index in zip(dt_matched_inds, gt_matched_inds)
        }

        # add points to metrics.pr_per_threshold[threshold]
        num_p = 0
        for gt_instance in gt_instances:
            for kp in cast(Mapping[str, Optional[Keypoint]], gt_instance.keypoints).values():
                num_p += 1 if kp else 0
        if num_p == 0:
            if len(dt_keypoints) == 0:
                metrics.pr_per_threshold[threshold] = PrecisionRecallCurve(precision_vals = [1, 1], recall_vals = [0, 1], confidence_vals = [1, 0])
        else:
            pr_curve_builder = PrecisionRecallCurveBuilder(num_p)
            for k, item in enumerate(dt_keypoints):
                dt_index, node_id, confidence_val = item
                if dt_index in dt_index_to_gt_instance and is_correct_keypoint(dt_index_to_gt_instance[dt_index], dt_instances[dt_index], node_id, threshold):
                    pr_curve_builder.add_detection(Detection.TP, confidence_val)
                else:
                    pr_curve_builder.add_detection(Detection.FP, confidence_val)
            metrics.pr_per_threshold[threshold] = pr_curve_builder.build()

        for keypoint_node_id in keypoint_node_ids:
            # add points to metrics.pr_per_keypoint_per_threshold[node_id][threshold]
            num_p = 0
            for gt_instance in gt_instances:
                for node_id, kp in cast(Mapping[str, Optional[Keypoint]], gt_instance.keypoints).items():
                    num_p += 1 if (node_id == keypoint_node_id and kp is not None) else 0

            dt_node_id_keypoints = list(filter(lambda kp: kp[1] == keypoint_node_id, dt_keypoints))

            if num_p == 0:
                if len(dt_node_id_keypoints) == 0:
                    metrics.pr_per_threshold[threshold] = PrecisionRecallCurve(precision_vals = [1, 1], recall_vals = [0, 1], confidence_vals = [1, 0])
                continue

            pr_curve_builder = PrecisionRecallCurveBuilder(num_p)
            for k, item in enumerate(dt_node_id_keypoints):
                dt_index, _, confidence_val = item
                if dt_index in dt_index_to_gt_instance and is_correct_keypoint(dt_index_to_gt_instance[dt_index], dt_instances[dt_index], keypoint_node_id, threshold):
                    pr_curve_builder.add_detection(Detection.TP, confidence_val)
                else:
                    pr_curve_builder.add_detection(Detection.FP, confidence_val)
            metrics.pr_per_keypoint_per_threshold[keypoint_node_id][threshold] = pr_curve_builder.build()

    return metrics


def evaluate_images_on_class(
    gt_annotations: Sequence[Annotation],
    dt_annotations: Sequence[Annotation],
    class_name: str,
    thresholds: Sequence[float]
) -> ClassKeypointMetrics:
    for gt_annotation in gt_annotations:
        for instance in gt_annotation.classes[class_name].instances:
            if instance.keypoints is not None:
                keypoint_node_ids = list(instance.keypoints.keys())
                break
    metrics_per_annotation = [
        evaluate_image_on_class(gt_annotation, dt_annotation, class_name, thresholds, keypoint_node_ids)
        for gt_annotation, dt_annotation in zip(gt_annotations, dt_annotations)
    ]
    return ClassKeypointMetrics.average_kp_metrics(metrics_per_annotation)
