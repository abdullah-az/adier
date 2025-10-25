from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.video_asset import VideoAsset
from app.repositories.base import BaseRepository


class VideoAssetRepository(BaseRepository[VideoAsset]):
    model = VideoAsset

    async def list_by_project(self, project_id: int) -> list[VideoAsset]:
        stmt = select(self.model).where(self.model.project_id == project_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_path(self, file_path: str) -> Optional[VideoAsset]:
        stmt = select(self.model).where(self.model.file_path == file_path)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
