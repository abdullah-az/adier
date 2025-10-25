from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.timeline_clip import TimelineClip
from app.repositories.base import BaseRepository


class TimelineClipRepository(BaseRepository[TimelineClip]):
    model = TimelineClip

    async def list_by_project(self, project_id: int) -> list[TimelineClip]:
        stmt = select(self.model).where(self.model.project_id == project_id).order_by(
            self.model.track_number.asc(), self.model.start_time.asc()
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
