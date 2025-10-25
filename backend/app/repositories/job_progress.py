from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job_progress import JobProgress
from app.repositories.base import BaseRepository


class JobProgressRepository(BaseRepository[JobProgress]):
    model = JobProgress

    async def list_for_job(self, export_job_id: int) -> list[JobProgress]:
        stmt = (
            select(self.model)
            .where(self.model.export_job_id == export_job_id)
            .order_by(self.model.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
