from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Iterable, List, Optional, Union

from loguru import logger

from app.models.job import Job


class JobRepository:
    """Persist job metadata to JSON storage."""

    def __init__(self, storage_root: Union[str, Path]) -> None:
        self.storage_root = Path(storage_root).resolve()
        self.metadata_dir = self.storage_root / "metadata"
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.metadata_dir / "jobs.json"
        self._lock: Optional[asyncio.Lock] = None

    async def _get_lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def _load_jobs(self) -> List[Job]:
        if not self.metadata_file.exists():
            return []

        def _read() -> List[Job]:
            with self.metadata_file.open("r", encoding="utf-8") as fh:
                payload = json.load(fh)
            return [Job.model_validate(item) for item in payload]

        return await asyncio.to_thread(_read)

    async def _persist(self, jobs: Iterable[Job]) -> None:
        jobs_list = list(jobs)

        def _write() -> None:
            tmp_file = self.metadata_dir / "jobs.tmp"
            with tmp_file.open("w", encoding="utf-8") as fh:
                json.dump([job.model_dump(mode="json") for job in jobs_list], fh, indent=2)
            tmp_file.replace(self.metadata_file)

        await asyncio.to_thread(_write)

    async def add(self, job: Job) -> Job:
        lock = await self._get_lock()
        async with lock:
            jobs = await self._load_jobs()
            jobs.append(job)
            await self._persist(jobs)
            logger.bind(job_id=job.id, job_type=job.job_type).debug("Registered job")
            return job

    async def update(self, job: Job) -> Job:
        lock = await self._get_lock()
        async with lock:
            jobs = await self._load_jobs()
            jobs = [existing for existing in jobs if existing.id != job.id]
            jobs.append(job)
            await self._persist(jobs)
            logger.bind(job_id=job.id, status=job.status).debug("Persisted job update")
            return job

    async def get(self, job_id: str) -> Optional[Job]:
        jobs = await self._load_jobs()
        return next((job for job in jobs if job.id == job_id), None)

    async def list_by_project(
        self,
        project_id: str,
        statuses: Optional[set[str]] = None,
    ) -> List[Job]:
        jobs = await self._load_jobs()
        filtered = [job for job in jobs if job.project_id == project_id]
        if statuses is not None:
            filtered = [job for job in filtered if job.status in statuses]
        filtered.sort(key=lambda job: job.created_at, reverse=True)
        return filtered

    async def all_jobs(self) -> List[Job]:
        return await self._load_jobs()

    async def delete(self, job_id: str) -> None:
        lock = await self._get_lock()
        async with lock:
            jobs = await self._load_jobs()
            jobs = [job for job in jobs if job.id != job_id]
            await self._persist(jobs)
            logger.bind(job_id=job_id).debug("Deleted job record")
