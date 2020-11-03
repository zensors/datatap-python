# MLDL Metrics

This page just contains examples of usage for the metrics library.
Visit https://www.notion.so/zensors/Evaluation-Metrics-cb8ca1824f914790b82414c68b34b5e1 for more information on how these metrics are computed and why they were chosen.

---

## Bounding Boxes
```python
from mldl.metrics.eval import estimate_threshold, compute_global_metrics
threshold = estimate_threshold(ground_truth_annotations, prediction_annotations)
metrics = compute_global_metrics(ground_truth_annotations, prediction_annotations, confidence_threshold=threshold)
metrics.log_to_comet(experiment, step=step)

from mldl.metrics.eval import compute_confusion_matrix
classes = ["__background__", "person", "car"] # list of all classes to be used in the confusion matrix
confusion_matrix = compute_confusion_matrix(ground_truth_annotations, prediction_annotations, classes)
confusion_matrix.log_to_comet(experiment, step=step)
```

---

## Keypoints
```python
from mldl.metrics.keypoints_eval import evaluate_images_on_class
class_name = "person" # class to be evaluated on keypoints
thresholds = [0.05, 0.10, 0.15, 0.20] # list of distance thresholds to be used in PCK step of evaluation
metrics = evaluate_images_on_class(ground_truth_annotations, prediction_annotations, class_name, thresholds)
metrics.log_to_comet(experiment, step=step)
```

---

## ReID
```python
from mldl.metrics.reid_eval import ReidMetrics
# similarity matrix: np.array of shape q by g containing distances between query images and gallery images
# query_ids: list of length q containing ids of query images
# gallery_ids: list of length g containing ids of gallery images
# query_dataset, gallery_dataset: Optional[Sequence[Tuple[UUID, Annotation, Rectangle]]] (include if you want to plot top k matches)
metrics = ReidMetrics(similarity_matrix, query_ids, gallery_ids, query_metas=query_dataset, gallery_metas=gallery_dataset)
metrics.log_to_comet(experiment, dataset_name="Market-1501", accuracy_top_k=(1,3,5,10)) 
```

---

## Tracking
```python
from mldl.metrics.track_eval import ClassTrackingMetrics
metrics = ClassTrackingMetrics("person") # class name of object to be tracked
for ground_truth_video, prediction_video in dataset:
    metrics.add_video(ground_truth_video, prediction_video)
metrics.log_to_comet(experiment, step=step)
metrics_host = mm.metrics.create()
# can also access the mm.MOTAccumulator objects directly via metrics.videos and use with the mm interface
import motmetrics as mm
summary = metrics_host.compute_many(
    [video[1] for video in metrics.videos],
    metrics=metrics.metric_names,
    names=[video[0] for video in metrics.videos],
    generate_overall=True
)
strsummary = mm.io.render_summary(
    summary,
    formatters=metrics_host.formatters,
    namemap=mm.io.motchallenge_metric_names
)
print(strsummary)
```

