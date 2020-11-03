from __future__ import annotations

from typing import Any, Mapping, Optional, Sequence, cast

import numpy as np

class ConfusionMatrix:
	classes: Sequence[str]
	class_map: Mapping[str, int]
	matrix: np.ndarray

	def __init__(self, classes: Sequence[str], matrix: Optional[np.ndarray] = None):
		self.classes = ["__background__"] + list(classes)
		self.class_map = dict([(class_name, index) for index, class_name in enumerate(self.classes)])
		dim = len(self.classes)
		self.matrix = matrix if matrix is not None else np.zeros((dim, dim))

	def add_detection(self, ground_truth_class: str, prediction_class: str, count: int = 1):
		r = self.class_map[ground_truth_class]
		c = self.class_map[prediction_class]
		self.matrix[r, c] += count

	def add_false_negative(self, ground_truth_class: str, count: int = 1):
		self.add_detection(ground_truth_class, "__background__", count)

	def add_false_positive(self, ground_truth_class: str, count: int = 1):
		self.add_detection("__background__", ground_truth_class, count)

	def __add__(self, other: Any) -> ConfusionMatrix:
		if isinstance(other, ConfusionMatrix):
			return ConfusionMatrix(self.classes, cast(np.ndarray, self.matrix + other.matrix))
		return NotImplemented
