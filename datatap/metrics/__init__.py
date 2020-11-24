"""
The metrics module provides a number of utilities for analyzing droplets in the context
of a broader training or evaluation job.

Here are some examples of the metrics module

```py
from datatap import Api, metrics
from my_model import model

api = Api()
dataset = api.get_default_database().get_dataset_list()[0]
latest_version = dataset.latest_version

confusion_matrix = metrics.ConfusionMatrix(latest_version.template.classes.keys())
pr_curve = metrics.PrecisionRecallCurve()

for annotation in latest_version.stream_split("validation"):
    prediction = model(annotation)
    confusion_matrix.add_annotation(annotation, prediction, 0.5, 0.5)
    pr_curve.add_annotation(annotation, prediction, 0.5)

print(confusion_matrix.matrix)
print(pr_curve.maximize_f1())
```
"""

from .confusion_matrix import ConfusionMatrix
from .precision_recall_curve import PrecisionRecallCurve, MaximizeF1Result
from .iou import generate_confusion_matrix, generate_pr_curve

__all__ = [
    "ConfusionMatrix",
    "PrecisionRecallCurve",
    "MaximizeF1Result",
    "generate_confusion_matrix",
    "generate_pr_curve",
]