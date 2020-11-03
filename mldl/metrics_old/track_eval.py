import motmetrics as mm
import numpy as np
from typing import Sequence, Optional, Tuple, List
import pandas as pd

try:
    from comet_ml import Experiment
except ImportError:
    Experiment = {}

from mldl.droplet import VideoAnnotation, Instance, Rectangle


class ClassTrackingMetrics:
    videos: List[Tuple[str, mm.MOTAccumulator]] = [] # (video name, accumulator)
    metric_names: Sequence[str] = mm.metrics.motchallenge_metrics # set of metrics we'll compute, as defined in mm.metrics
    class_name: str

    def __init__(self, class_name: str, metric_names: Optional[Sequence[str]] = None):
        self.class_name = class_name
        if metric_names is not None:
            self.metric_names = metric_names

    def add_video(self, ground_truth: VideoAnnotation, prediction: VideoAnnotation) -> None:
        video_name = ground_truth.video.name or f"Video #{len(self.videos) + 1}"
        accumulator = mm.MOTAccumulator(auto_id=True)

        for ground_truth_frame, prediction_frame in zip(ground_truth.frames, prediction.frames):
            ground_truth_instances: Sequence[Instance] = ground_truth_frame.classes[self.class_name].instances
            prediction_instances: Sequence[Instance] = prediction_frame.classes[self.class_name].instances

            ground_truth_boxes = [
                instance.bounding_box.to_xywh_tuple()
                for instance in ground_truth_instances
            ]
            prediction_boxes = [
                instance.bounding_box.to_xywh_tuple()
                for instance in prediction_instances
            ]
            distance_matrix = mm.distances.iou_matrix(ground_truth_boxes, prediction_boxes, max_iou=0.5)
            accumulator.update(
                [int(instance.identity) for instance in ground_truth_instances],
                [int(instance.identity) for instance in prediction_instances],
                distance_matrix
            )

        self.videos.append((video_name, accumulator))

    def log_to_comet(self, experiment: Experiment, step: Optional[int] = None) -> None:
        metrics_host = mm.metrics.create()
        dataframe = metrics_host.compute_many(
            [video[1] for video in self.videos],
            metrics=self.metric_names,
            names=[video[0] for video in self.videos],
            generate_overall=True
        )
        for row in dataframe.itertuples():
            for col in row._fields:
                if col == "Index":
                    continue
                experiment.log_metric(f"{col} ({self.class_name}, {row.Index})", getattr(row, col), step=step)
