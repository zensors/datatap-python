from __future__ import annotations

from typing import Mapping, Optional

from ..geometry import Mask
from ..utils import basic_repr
from .image_annotation import ImageAnnotation
from .class_annotation import ClassAnnotation
from .image import Image
from .pride_metadata import PrideMetadata


class PrideImageAnnotation(ImageAnnotation):
	pride_metadata: PrideMetadata

	def __init__(self, *, image: Image, classes: Mapping[str, ClassAnnotation], pride_metadata: PrideMetadata, mask: Optional[Mask] = None):
		super().__init__(image = image, classes = classes, mask = mask)
		self.pride_metadata = pride_metadata

	def __repr__(self):
		return basic_repr("PrideImageAnnotation", image = self.image, mask = self.mask, pride_metadata = self.pride_metadata, classes = self.classes)
