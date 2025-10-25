from __future__ import annotations

from datetime import datetime
from typing import Iterable, List, Optional

from app.models.job import Job, JobStatus
from app.models.video_asset import VideoAsset
from app.repositories.job_repository import JobRepository
from app.repositories.video_repository import VideoAssetRepository
from app.schemas.project import (
    ProjectAssetSummary,
    ProjectJobSummary,
    ProjectSummaryResponse,
)
from app.utils.storage import StorageManager


class ProjectService:
    """Aggregate project level information from assets and jobs."""

    def __init__(
        self,
        *,
        storage_manager: StorageManager,
        video_repository: VideoAssetRepository,
        job_repository: JobRepository,
    ) -> None:
        self._storage_manager = storage_manager
        self._video_repository = video_repository
        self._job_repository = job_repository

    async def list_projects(self) -> List[ProjectSummaryResponse]:
        assets = await self._video_repository.all_assets()
        jobs = await self._job_repository.all_jobs()

        project_ids = {
            *{asset.project_id for asset in assets},
            *{job.project_id for job in jobs},
        }

        summaries = [
            self._build_summary(
                project_id=project_id,
                assets=[asset for asset in assets if asset.project_id == project_id],
                jobs=[job for job in jobs if job.project_id == project_id],
            )
            for project_id in project_ids
        ]

        summaries.sort(key=lambda summary: summary.updated_at, reverse=True)
        return summaries

    async def get_project(self, project_id: str) -> Optional[ProjectSummaryResponse]:
        assets = await self._video_repository.list_by_project(project_id)
        jobs = await self._job_repository.list_by_project(project_id)
        if not assets and not jobs:
            return None
        return self._build_summary(project_id=project_id, assets=assets, jobs=jobs)

    def _build_summary(
        self,
        *,
        project_id: str,
        assets: Iterable[VideoAsset],
        jobs: Iterable[Job],
    ) -> ProjectSummaryResponse:
        asset_list = sorted(assets, key=lambda asset: asset.updated_at, reverse=True)
        job_list = sorted(jobs, key=lambda job: job.updated_at, reverse=True)

        latest_asset = asset_list[0] if asset_list else None
        latest_job = job_list[0] if job_list else None

        status = self._resolve_status(asset_list, job_list)
        storage_usage = self._storage_manager.project_storage_usage(project_id)
        total_size = sum(
            category_stats.get("bytes", 0)
            for category_stats in storage_usage.get("categories", {}).values()
            if isinstance(category_stats, dict)
        )
        updated_at_candidates = [
            item.updated_at for item in (*asset_list[:1], *job_list[:1]) if hasattr(item, "updated_at")
        ]
        updated_at = max(updated_at_candidates) if updated_at_candidates else datetime.utcnow()

        active_job = next(
            (job for job in job_list if job.status in {JobStatus.QUEUED, JobStatus.RUNNING}),
            latest_job,
        )
        job_progress = float(active_job.progress) if active_job else (100.0 if status == "ready" else 0.0)

        thumbnail_url = None
        if latest_asset and latest_asset.thumbnail_path and not latest_asset.thumbnail_path.endswith(".placeholder"):
            thumbnail_url = f"/projects/{project_id}/videos/{latest_asset.id}/thumbnail"

        return ProjectSummaryResponse(
            project_id=project_id,
            display_name=self._resolve_display_name(project_id, latest_asset),
            status=status,
            updated_at=updated_at,
            asset_count=len(asset_list),
            total_size_bytes=total_size,
            job_progress=job_progress,
            thumbnail_url=thumbnail_url,
            latest_asset=self._to_asset_summary(latest_asset) if latest_asset else None,
            latest_job=self._to_job_summary(latest_job) if latest_job else None,
        )

    def _resolve_status(self, assets: Iterable[VideoAsset], jobs: Iterable[Job]) -> str:
        job_statuses = {job.status for job in jobs}
        if JobStatus.FAILED in job_statuses:
            return "failed"
        if JobStatus.RUNNING in job_statuses or JobStatus.QUEUED in job_statuses:
            return "processing"

        asset_list = list(assets)
        asset_statuses = [asset.status for asset in asset_list]
        if any(status == "ready" for status in asset_statuses):
            return "ready"
        if asset_list:
            # Fallback to the latest asset status (list is sorted by updated_at DESC before call)
            return asset_list[0].status
        if JobStatus.COMPLETED in job_statuses:
            return "completed"
        return "uploaded"

    def _resolve_display_name(self, project_id: str, latest_asset: Optional[VideoAsset]) -> str:
        if latest_asset and latest_asset.original_filename:
            return latest_asset.original_filename
        return f"Project {project_id}"

    def _to_asset_summary(self, asset: VideoAsset) -> ProjectAssetSummary:
        return ProjectAssetSummary(
            asset_id=asset.id,
            filename=asset.filename,
            original_filename=asset.original_filename,
            size_bytes=asset.size_bytes,
            status=asset.status,
            updated_at=asset.updated_at,
        )

    def _to_job_summary(self, job: Job) -> ProjectJobSummary:
        return ProjectJobSummary(
            id=job.id,
            job_type=job.job_type,
            status=job.status,
            progress=job.progress,
            updated_at=job.updated_at,
            error_message=job.error_message,
        )
