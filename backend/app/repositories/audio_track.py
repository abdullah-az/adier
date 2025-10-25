from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audio_track import AudioTrack
from app.repositories.base import BaseRepository


class AudioTrackRepository(BaseRepository[AudioTrack]):
    model = AudioTrack

    async def list_by_project(self, project_id: int) -> list[AudioTrack]:
        stmt = select(self.model).where(self.model.project_id == project_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
