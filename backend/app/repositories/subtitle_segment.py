from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subtitle_segment import SubtitleSegment
from app.repositories.base import BaseRepository


class SubtitleSegmentRepository(BaseRepository[SubtitleSegment]):
    model = SubtitleSegment

    async def list_by_project(self, project_id: int) -> list[SubtitleSegment]:
        stmt = select(self.model).where(self.model.project_id == project_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def list_by_asset(self, video_asset_id: int) -> list[SubtitleSegment]:
        stmt = select(self.model).where(self.model.video_asset_id == video_asset_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
