from __future__ import annotations

from datetime import datetime
from uuid import UUID

from ..utils import basic_repr


class PrideMetadata:
	labeler_uid: UUID
	labeled_at: datetime

	def __init__(self, *, labeler_uid: UUID, labeled_at: datetime):
		self.labeler_uid = labeler_uid
		self.labeled_at = labeled_at

	def __repr__(self) -> str:
		return basic_repr("PrideMetadata", labeler_uid = self.labeler_uid, labeled_at = self.labeled_at)
