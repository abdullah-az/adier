from __future__ import annotations

from .base import SQLAlchemyRepository
from ..models.media_asset import MediaAsset


class MediaAssetRepository(SQLAlchemyRepository[MediaAsset]):
    model_cls = MediaAsset


__all__ = ["MediaAssetRepository"]
