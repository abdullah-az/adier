"""
Simple smoke test to verify database schema creation and basic operations.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger

from app.core.database import get_async_sessionmaker, init_db
from app.models import Project, ProjectStatus, VideoAsset, ExportJob, ExportJobStatus, ExportJobType
from app.repositories import ProjectRepository
from app.schemas import ProjectCreate


async def main():
    logger.info("Initializing database...")
    await init_db()
    logger.success("Database initialized!")

    async_session = get_async_sessionmaker()
    
    async with async_session() as session:
        repo = ProjectRepository(session)
        
        logger.info("Creating test project...")
        project_data = ProjectCreate(
            name="Test Project",
            description="A test video editing project",
            status=ProjectStatus.DRAFT
        )
        project = await repo.create(project_data)
        logger.success(f"Created project: {project.name} (ID: {project.id})")
        
        logger.info("Retrieving project...")
        retrieved = await repo.get(project.id)
        assert retrieved is not None
        assert retrieved.name == "Test Project"
        logger.success(f"Retrieved project: {retrieved.name}")
        
        logger.info("Listing projects...")
        projects = await repo.list()
        assert len(projects) == 1
        logger.success(f"Found {len(projects)} project(s)")
        
        logger.info("Testing relationships...")
        video_asset = VideoAsset(
            project_id=project.id,
            filename="test_video.mp4",
            file_path="/storage/test_video.mp4",
            file_size=1024000,
            mime_type="video/mp4",
            duration=120.5,
            width=1920,
            height=1080,
            fps=30.0,
            codec="h264"
        )
        session.add(video_asset)
        await session.flush()
        logger.success(f"Created video asset: {video_asset.filename}")
        
        export_job = ExportJob(
            project_id=project.id,
            job_type=ExportJobType.VIDEO,
            output_format="mp4",
            status=ExportJobStatus.PENDING,
            resolution="1920x1080",
            fps=30
        )
        session.add(export_job)
        await session.flush()
        logger.success(f"Created export job (ID: {export_job.id})")
        
        await session.commit()
        
    logger.success("All smoke tests passed!")


if __name__ == "__main__":
    asyncio.run(main())
