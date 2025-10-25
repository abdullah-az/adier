from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.export_job import ExportJob
from app.models.enums import ExportJobStatus
from app.repositories.base import BaseRepository


class ExportJobRepository(BaseRepository[ExportJob]):
    model = ExportJob

    async def list_by_project(self, project_id: int) -> list[ExportJob]:
        stmt = select(self.model).where(self.model.project_id == project_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def list_by_status(self, status: ExportJobStatus) -> list[ExportJob]:
        stmt = select(self.model).where(self.model.status == status)
        result = await self.session.execute(stmt)
        return result.scalars().all()
