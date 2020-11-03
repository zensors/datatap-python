from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping
from uuid import UUID

from ..utils import basic_repr


class CameraMetadata:
	camera_uid: UUID
	taken_at: datetime

	@staticmethod
	def from_json(json: Mapping[str, Any]):
		return CameraMetadata(
			camera_uid = json["cameraUid"],
			taken_at = datetime.fromtimestamp(json["takenAt"]/1000)
		)

	def __init__(self, *, camera_uid: UUID, taken_at: datetime):
		self.camera_uid = camera_uid
		self.taken_at = taken_at

	def __repr__(self):
		return basic_repr("CameraMetadata", camera_uid = self.camera_uid, taken_at = self.taken_at)

	def __eq__(self, other: Any):
		if not isinstance(other, CameraMetadata):
			return NotImplemented
		return self.camera_uid == other.camera_uid and self.taken_at == other.taken_at
