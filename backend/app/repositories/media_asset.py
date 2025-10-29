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

    def update_analysis_cache(
        self,
        instance: MediaAsset,
        *,
        cache_key: str,
        result: dict[str, object],
    ) -> MediaAsset:
        payload = {"analysis_cache": {"hash": cache_key, "result": result}}
        return self.update(instance, payload)

    def clear_analysis_cache(self, instance: MediaAsset) -> MediaAsset:
        return self.update(instance, {"analysis_cache": None})


__all__ = ["MediaAssetRepository"]
