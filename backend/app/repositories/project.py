from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.enums import ProjectStatus
from app.repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    model = Project

    async def get_by_name(self, name: str) -> Optional[Project]:
        stmt = select(self.model).where(self.model.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_status(
        self, status: ProjectStatus, skip: int = 0, limit: int = 100
    ) -> list[Project]:
        stmt = select(self.model).where(self.model.status == status).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()
