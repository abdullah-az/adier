from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import List, Optional

from loguru import logger

from app.models.project import Project


class ProjectRepository:
    """File-backed repository storing project metadata."""

    def __init__(self, storage_root: str | Path) -> None:
        self.storage_root = Path(storage_root).resolve()
        self.metadata_dir = self.storage_root / "metadata"
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.metadata_dir / "projects.json"
        self._lock: asyncio.Lock | None = None

    async def _get_lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def _load(self) -> List[Project]:
        if not self.metadata_file.exists():
            return []

        def _read() -> List[Project]:
            with self.metadata_file.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            return [Project(**item) for item in payload]

        return await asyncio.to_thread(_read)

    async def _persist(self, projects: List[Project]) -> None:
        def _write() -> None:
            tmp_file = self.metadata_dir / "projects.tmp"
            with tmp_file.open("w", encoding="utf-8") as handle:
                json.dump([project.model_dump(mode="json") for project in projects], handle, indent=2)
            tmp_file.replace(self.metadata_file)

        await asyncio.to_thread(_write)

    async def all_projects(self) -> List[Project]:
        return await self._load()

    async def add(self, project: Project) -> Project:
        lock = await self._get_lock()
        async with lock:
            projects = await self._load()
            projects.append(project)
            await self._persist(projects)
            logger.debug("Project registered", project_id=project.id, name=project.name)
            return project

    async def update(self, project: Project) -> Project:
        lock = await self._get_lock()
        async with lock:
            projects = await self._load()
            projects = [existing for existing in projects if existing.id != project.id]
            projects.append(project)
            await self._persist(projects)
            logger.debug("Project updated", project_id=project.id)
            return project

    async def get(self, project_id: str) -> Optional[Project]:
        projects = await self._load()
        return next((project for project in projects if project.id == project_id), None)

    async def delete(self, project_id: str) -> None:
        lock = await self._get_lock()
        async with lock:
            projects = await self._load()
            projects = [project for project in projects if project.id != project_id]
            await self._persist(projects)
            logger.debug("Project deleted", project_id=project_id)
