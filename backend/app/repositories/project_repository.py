from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import List, Optional, Union

from app.models.project import Project


class ProjectRepository:
    """Repository persisted as JSON for managing project metadata."""

    def __init__(self, storage_root: Union[str, Path]) -> None:
        self.storage_root = Path(storage_root).resolve()
        self.metadata_dir = self.storage_root / "metadata"
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.metadata_dir / "projects.json"
        self._lock: Optional[asyncio.Lock] = None

    async def _get_lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def _load(self) -> List[Project]:
        if not self.metadata_file.exists():
            return []

        def _read() -> List[Project]:
            with self.metadata_file.open("r", encoding="utf-8") as buffer:
                payload = json.load(buffer)
            return [Project(**record) for record in payload]

        return await asyncio.to_thread(_read)

    async def _persist(self, projects: List[Project]) -> None:
        def _write() -> None:
            tmp_file = self.metadata_dir / "projects.tmp"
            with tmp_file.open("w", encoding="utf-8") as buffer:
                json.dump([project.model_dump() for project in projects], buffer, indent=2)
            tmp_file.replace(self.metadata_file)

        await asyncio.to_thread(_write)

    async def add(self, project: Project) -> Project:
        lock = await self._get_lock()
        async with lock:
            projects = await self._load()
            projects = [existing for existing in projects if existing.id != project.id]
            projects.append(project)
            await self._persist(projects)
            return project

    async def update(self, project: Project) -> Project:
        return await self.add(project)

    async def get(self, project_id: str) -> Optional[Project]:
        projects = await self._load()
        return next((project for project in projects if project.id == project_id), None)

    async def delete(self, project_id: str) -> None:
        lock = await self._get_lock()
        async with lock:
            projects = await self._load()
            projects = [project for project in projects if project.id != project_id]
            await self._persist(projects)

    async def list_all(self) -> List[Project]:
        return await self._load()

    async def all_projects(self) -> List[Project]:  # alias for compatibility
        return await self._load()
