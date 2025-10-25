from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scene_detection import SceneDetection
from app.repositories.base import BaseRepository


class SceneDetectionRepository(BaseRepository[SceneDetection]):
    model = SceneDetection

    async def list_by_project(self, project_id: int) -> list[SceneDetection]:
        stmt = select(self.model).where(self.model.project_id == project_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def list_by_asset(self, video_asset_id: int) -> list[SceneDetection]:
        stmt = select(self.model).where(self.model.video_asset_id == video_asset_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
