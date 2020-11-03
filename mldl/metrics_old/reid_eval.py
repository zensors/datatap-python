import heapq
import random
from typing import Any, Mapping, Optional, Sequence, Tuple
from uuid import UUID

import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.axes_grid1 import ImageGrid
from PIL import ImageOps

try:
	from comet_ml import Experiment
except ImportError:
	Experiment = {}

from mldl.droplet import Annotation, Rectangle
from mldl.image.loader import load_image_from_annotation
from mldl.image.utils import crop_image

from .metrics import Detection, PrecisionRecallCurve, PrecisionRecallCurveBuilder

# TODO: implement camera ids and ability to exclude gallery instances with the same person id and camera id

class ReidMetrics():
    distance_matrix: np.ndarray
    query_ids: Sequence[str]
    gallery_ids: Sequence[str]
    pr_curve: PrecisionRecallCurve
    # include datasets if you want to plot top k matches
    query_dataset: Optional[Sequence[Tuple[UUID, Annotation, Rectangle]]]
    gallery_dataset: Optional[Sequence[Tuple[UUID, Annotation, Rectangle]]]

    def __init__(
        self,
        distance_matrix: np.ndarray,
        query_ids: Sequence[str],
        gallery_ids: Sequence[str],
        query_dataset: Optional[Sequence[Tuple[UUID, Annotation, Rectangle]]] = None,
        gallery_dataset: Optional[Sequence[Tuple[UUID, Annotation, Rectangle]]] = None
    ):
        assert len(distance_matrix) == len(query_ids)
        assert len(distance_matrix[0]) == len(gallery_ids)
        assert query_dataset is None or len(query_dataset) == len(query_ids)
        assert gallery_dataset is None or len(gallery_dataset) == len(gallery_ids)
        self.distance_matrix = distance_matrix
        self.query_ids = query_ids
        self.gallery_ids = gallery_ids
        self.pr_curve = self.compute_pr_curve()
        self.query_dataset = query_dataset
        self.gallery_dataset = gallery_dataset

    def compute_pr_curve(self) -> PrecisionRecallCurve:
        pr_curves = []

        for query_index, query_id in enumerate(self.query_ids):
            gallery_indices = np.argsort(self.distance_matrix[query_index])
            num_p = sum(np.array(self.gallery_ids) == query_id)
            if num_p == 0:
                continue
            pr_curve_builder = PrecisionRecallCurveBuilder(num_p)
            for gallery_index in gallery_indices:
                distance = self.distance_matrix[query_index][gallery_index]
                if self.gallery_ids[gallery_index] == query_id:
                    pr_curve_builder.add_detection(Detection.TP, distance)
                else:
                    pr_curve_builder.add_detection(Detection.FP, distance)
            pr_curves.append(pr_curve_builder.build())

        return PrecisionRecallCurve.estimate_pr_curve_average(pr_curves)

    def compute_accuracy_at_top_k(self, k: int) -> float:
        """Compute fraction of queries for which there is a correct match among the top k matched galleries"""
        num_correct = 0.0
        gallery_id_set = set(self.gallery_ids)
        num_p = len(list(filter(lambda id: id in gallery_id_set, self.query_ids)))
        if num_p == 0:
            raise Exception("Query set and gallery set are disjoint.")
        for query_index, query_id in enumerate(self.query_ids):
            gallery_indices = heapq.nsmallest(
                k, range(len(self.gallery_ids)),
                key = lambda i: self.distance_matrix[query_index][i]
            )
            gallery_ids = np.array(self.gallery_ids)[gallery_indices]
            num_correct += 1 if np.any(gallery_ids == query_id) else 0
        return num_correct / num_p

    def compute_distance_threshold_top_1(self) -> float:
        """Compute distance threshold which maximizes top 1 f1"""
        gallery_indices = self.distance_matrix.argmin(axis = 1)
        gallery_id_set = set(self.gallery_ids)
        num_p = len(list(filter(lambda id: id in gallery_id_set, self.query_ids)))
        if num_p == 0:
            raise Exception("Query set and gallery set are disjoint.")
        pr_curve_builder = PrecisionRecallCurveBuilder(num_p)
        for query_index, gallery_index in enumerate(gallery_indices):
            distance = self.distance_matrix[query_index][gallery_index]
            if self.gallery_ids[gallery_index] == self.query_ids[query_index]:
                pr_curve_builder.add_detection(Detection.TP, distance)
            else:
                pr_curve_builder.add_detection(Detection.FP, distance)
        return pr_curve_builder.build().get_f1_and_threshold()[1]

    def compute_distance_threshold(self) -> float:
        """Compute distance threshold which maximizes overall f1"""
        return self.pr_curve.get_f1_and_threshold()[1]

    def compute_statistics(self, distance_threshold: float) -> Mapping[str, int]:
        detection_matrix = self.distance_matrix <= distance_threshold
        matches_matrix = np.asarray([
            [gallery_id == query_id for gallery_id in self.gallery_ids]
            for query_id in self.query_ids
        ])
        true_positives = np.sum(np.logical_and(detection_matrix, matches_matrix))
        false_positives = np.sum(detection_matrix) - true_positives
        false_negatives = np.sum(matches_matrix) - true_positives
        true_negatives = np.sum(np.logical_not(np.logical_or(detection_matrix, matches_matrix)))
        return {
            "true_positives": true_positives,
            "false_positives": false_positives,
            "false_negatives": false_negatives,
            "true_negatives": true_negatives
        }

    def log_to_comet(
        self,
        experiment: Experiment,
        dataset_name: Optional[str] = None,
        step: Optional[int] = None,
        accuracy_top_k: Sequence[int] = [1, 3, 5, 10],
        plot_top_k: int = 10,
        plot_sample_size: int = 15
    ) -> None:
        suffix = "" if dataset_name is None else f" ({dataset_name})"
        experiment.log_metric(f"mAP{suffix}", self.pr_curve.get_average_precision(), step = step)
        experiment.log_figure(figure_name = f"average p-r curve{suffix}", figure = self.pr_curve.plot(), step = step)
        experiment.log_metric(f"threshold{suffix}", self.compute_distance_threshold(), step = step)
        if accuracy_top_k is not None:
            for k in accuracy_top_k:
                experiment.log_metric(f"accuracy @ top {k}{suffix}", self.compute_accuracy_at_top_k(k), step = step)
        if plot_top_k is not None and plot_sample_size is not None:
            for fig in self.plot_top_k(plot_sample_size, plot_top_k):
                experiment.log_figure(figure_name = dataset_name, figure = fig, step = step)
        plt.close("all")

    def plot_top_k(self, sample_size: int, k: int) -> Sequence[plt.Figure]:
        assert self.query_dataset is not None and self.gallery_dataset is not None
        figures = []

        query_indices = random.sample(range(len(self.query_ids)), min(sample_size, len(self.query_ids)))
        for query_index in query_indices:
            fig = plt.figure(figsize = (k, 2))
            grid = ImageGrid(fig, 111, nrows_ncols = (1, k + 1))
            query_img = load_image_from_annotation(self.query_dataset[query_index][1])
            query_img = crop_image(query_img, self.query_dataset[query_index][2])
            grid[0].imshow(query_img)
            grid[0].axis("off")

            gallery_indices = heapq.nsmallest(
                k, range(len(self.gallery_ids)),
                key = lambda i: self.distance_matrix[query_index][i]
            )

            for gallery_index, axes in zip(gallery_indices, grid[1:]):
                image = load_image_from_annotation(self.gallery_dataset[gallery_index][1])
                image = crop_image(image, self.gallery_dataset[gallery_index][2])
                border_color = "green" if self.query_ids[query_index] == self.gallery_ids[gallery_index] else "red"
                image_with_border = ImageOps.expand(image, border = 5, fill = border_color)
                axes.imshow(image_with_border)
                axes.axis("off")

            figures.append(fig)

        return figures
