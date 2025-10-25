from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.background_music import BackgroundMusic
from app.repositories.base import BaseRepository


class BackgroundMusicRepository(BaseRepository[BackgroundMusic]):
    model = BackgroundMusic

    async def list_by_project(self, project_id: int) -> list[BackgroundMusic]:
        stmt = select(self.model).where(self.model.project_id == project_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
