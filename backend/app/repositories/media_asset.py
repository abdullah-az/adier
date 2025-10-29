from __future__ import annotations

from .base import SQLAlchemyRepository
from ..models.media_asset import MediaAsset

_UNSET = object()


class MediaAssetRepository(SQLAlchemyRepository[MediaAsset]):
    model_cls = MediaAsset

    def update_metadata(
        self,
        instance: MediaAsset,
        *,
        size_bytes: int | None | object = _UNSET,
        duration_seconds: float | None | object = _UNSET,
        checksum: str | None | object = _UNSET,
    ) -> MediaAsset:
        payload: dict[str, object] = {}
        if size_bytes is not _UNSET:
            payload["size_bytes"] = size_bytes
        if duration_seconds is not _UNSET:
            payload["duration_seconds"] = duration_seconds
        if checksum is not _UNSET:
            payload["checksum"] = checksum
        if not payload:
            return instance
        return self.update(instance, payload)


__all__ = ["MediaAssetRepository"]
