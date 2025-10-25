from __future__ import annotations

import math
from datetime import datetime
from typing import Iterable, Optional, Sequence
from uuid import uuid4

from loguru import logger

from app.models.pipeline import AspectRatio, ResolutionPreset
from app.models.project import Project
from app.repositories.project_repository import ProjectRepository
from app.repositories.timeline_repository import TimelineRepository
from app.repositories.video_repository import VideoAssetRepository
from app.utils.storage import StorageManager


class ProjectService:
    """Business logic for managing project lifecycle and aggregating related resources."""

    def __init__(
        self,
        project_repository: ProjectRepository,
        timeline_repository: TimelineRepository,
        video_repository: VideoAssetRepository,
        storage_manager: StorageManager,
    ) -> None:
        self.project_repository = project_repository
        self.timeline_repository = timeline_repository
        self.video_repository = video_repository
        self.storage_manager = storage_manager

    async def create_project(
        self,
        *,
        name: str,
        description: Optional[str] = None,
        locale: str = "en",
        tags: Optional[Sequence[str]] = None,
        status: str = "draft",
        metadata: Optional[dict] = None,
        default_aspect_ratio: AspectRatio = AspectRatio.SIXTEEN_NINE,
        default_resolution: ResolutionPreset = ResolutionPreset.P1080,
    ) -> Project:
        project = Project(
            id=str(uuid4()),
            name=name,
            description=description,
            locale=locale,
            status=status,
            tags=list(tags or []),
            metadata=metadata or {},
            default_aspect_ratio=default_aspect_ratio,
            default_resolution=default_resolution,
        )
        await self.project_repository.add(project)
        self.storage_manager.ensure_project_directories(project.id)
        logger.info("Created project", project_id=project.id, name=project.name)
        return project

    async def list_projects(
        self,
        *,
        page: int,
        page_size: int,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
        locale: Optional[str] = None,
    ) -> tuple[list[Project], int]:
        projects = await self.project_repository.list_all()
        if locale:
            projects = [project for project in projects if project.locale.lower() == locale.lower()]
        key_map = {
            "name": lambda project: project.name.lower(),
            "created_at": lambda project: project.created_at,
            "updated_at": lambda project: project.updated_at,
            "status": lambda project: project.status,
        }
        if sort_by:
            key = key_map.get(sort_by, key_map["created_at"])
        else:
            key = key_map["created_at"]
        reverse = sort_order.lower() == "desc"
        projects.sort(key=key, reverse=reverse)
        total = len(projects)
        start = (page - 1) * page_size
        end = start + page_size
        return projects[start:end], total

    async def get_project(self, project_id: str) -> Optional[Project]:
        return await self.project_repository.get(project_id)

    async def update_project(
        self,
        project_id: str,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        locale: Optional[str] = None,
        status: Optional[str] = None,
        tags: Optional[Sequence[str]] = None,
        metadata: Optional[dict] = None,
        default_aspect_ratio: Optional[AspectRatio] = None,
        default_resolution: Optional[ResolutionPreset] = None,
    ) -> Optional[Project]:
        project = await self.project_repository.get(project_id)
        if project is None:
            return None
        if name is not None:
            project.name = name
        if description is not None:
            project.description = description
        if locale is not None:
            project.locale = locale
        if status is not None:
            project.status = status
        if tags is not None:
            project.tags = list(tags)
        if metadata is not None:
            project.metadata = metadata
        if default_aspect_ratio is not None:
            project.default_aspect_ratio = default_aspect_ratio
        if default_resolution is not None:
            project.default_resolution = default_resolution
        project.updated_at = datetime.utcnow()
        await self.project_repository.update(project)
        logger.info("Updated project", project_id=project.id)
        return project

    async def delete_project(self, project_id: str) -> bool:
        project = await self.project_repository.get(project_id)
        if project is None:
            return False
        await self.timeline_repository.delete_for_project(project_id)
        await self.video_repository.delete_for_project(project_id)
        self.storage_manager.cleanup_project(project_id)
        await self.project_repository.delete(project_id)
        logger.info("Deleted project", project_id=project_id)
        return True

    async def attach_timeline(self, project_id: str, timeline_id: str) -> None:
        project = await self.project_repository.get(project_id)
        if project is None:
            return
        if timeline_id not in project.timeline_ids:
            project.timeline_ids.append(timeline_id)
            project.updated_at = datetime.utcnow()
            await self.project_repository.update(project)

    async def detach_timeline(self, project_id: str, timeline_id: str) -> None:
        project = await self.project_repository.get(project_id)
        if project is None:
            return
        if timeline_id in project.timeline_ids:
            project.timeline_ids = [tid for tid in project.timeline_ids if tid != timeline_id]
            project.updated_at = datetime.utcnow()
            await self.project_repository.update(project)

    async def touch(self, project_id: str) -> Optional[Project]:
        project = await self.project_repository.get(project_id)
        if project is None:
            return None
        project.last_opened_at = datetime.utcnow()
        project.updated_at = datetime.utcnow()
        await self.project_repository.update(project)
        return project

