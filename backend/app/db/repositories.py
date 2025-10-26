from __future__ import annotations

from typing import Any, Generic, Optional, TypeVar

from sqlalchemy import Select, select

from .base import Base
from .models import (
    AudioTrack,
    ExportJob,
    JobStatus,
    JobStatusCode,
    Project,
    SceneDetection,
    SubtitleSegment,
    TimelineClip,
    VideoAsset,
    VideoAssetStatus,
    VideoAssetType,
)
from .session import SessionFactory, SessionLocal, session_scope

ModelType = TypeVar("ModelType", bound=Base)


class RepositoryError(Exception):
    """Base class for repository layer errors."""


class NotFoundError(RepositoryError):
    """Raised when a record is not found for the requested operation."""


class SQLAlchemyRepository(Generic[ModelType]):
    """Generic repository exposing convenience CRUD helpers."""

    model: type[ModelType]

    def __init__(self, model: type[ModelType], session_factory: SessionFactory = SessionLocal) -> None:
        self.model = model
        self._session_factory = session_factory

    def create(self, data: dict[str, Any]) -> ModelType:
        with session_scope(self._session_factory) as session:
            instance = self.model(**data)
            session.add(instance)
            session.flush()
            session.refresh(instance)
            return instance

    def add(self, instance: ModelType) -> ModelType:
        with session_scope(self._session_factory) as session:
            session.add(instance)
            session.flush()
            session.refresh(instance)
            return instance

    def get(self, obj_id: Any) -> Optional[ModelType]:
        with self._session_factory() as session:
            return session.get(self.model, obj_id)

    def list(self, filters: Optional[dict[str, Any]] = None, order_by: Optional[Any] = None) -> list[ModelType]:
        stmt: Select[Any] = select(self.model)
        if filters:
            for key, value in filters.items():
                stmt = stmt.where(getattr(self.model, key) == value)
        if order_by is not None:
            stmt = stmt.order_by(order_by)

        with self._session_factory() as session:
            return list(session.scalars(stmt))

    def update(self, obj_id: Any, data: dict[str, Any]) -> ModelType:
        with session_scope(self._session_factory) as session:
            instance = session.get(self.model, obj_id)
            if instance is None:
                raise NotFoundError(f"{self.model.__name__} with id '{obj_id}' not found")
            for key, value in data.items():
                if not hasattr(instance, key):  # safeguard against typos
                    raise AttributeError(f"{self.model.__name__} has no attribute '{key}'")
                setattr(instance, key, value)
            session.flush()
            session.refresh(instance)
            return instance

    def delete(self, obj_id: Any) -> None:
        with session_scope(self._session_factory) as session:
            instance = session.get(self.model, obj_id)
            if instance is None:
                raise NotFoundError(f"{self.model.__name__} with id '{obj_id}' not found")
            session.delete(instance)


class ProjectRepository(SQLAlchemyRepository[Project]):
    def __init__(self, session_factory: SessionFactory = SessionLocal) -> None:
        super().__init__(Project, session_factory)

    def get_by_slug(self, slug: str) -> Optional[Project]:
        stmt = select(Project).where(Project.slug == slug)
        with self._session_factory() as session:
            return session.scalar(stmt)


class VideoAssetRepository(SQLAlchemyRepository[VideoAsset]):
    def __init__(self, session_factory: SessionFactory = SessionLocal) -> None:
        super().__init__(VideoAsset, session_factory)

    def list_by_project(
        self,
        project_id: str,
        *,
        asset_type: Optional[VideoAssetType] = None,
        status: Optional[VideoAssetStatus] = None,
    ) -> list[VideoAsset]:
        stmt = select(VideoAsset).where(VideoAsset.project_id == project_id)
        if asset_type is not None:
            stmt = stmt.where(VideoAsset.asset_type == asset_type)
        if status is not None:
            stmt = stmt.where(VideoAsset.status == status)
        stmt = stmt.order_by(VideoAsset.created_at)
        with self._session_factory() as session:
            return list(session.scalars(stmt))

    def get_by_checksum(self, checksum: str) -> Optional[VideoAsset]:
        stmt = select(VideoAsset).where(VideoAsset.checksum == checksum)
        with self._session_factory() as session:
            return session.scalar(stmt)


class SceneDetectionRepository(SQLAlchemyRepository[SceneDetection]):
    def __init__(self, session_factory: SessionFactory = SessionLocal) -> None:
        super().__init__(SceneDetection, session_factory)

    def list_for_asset(self, video_asset_id: str) -> list[SceneDetection]:
        stmt = select(SceneDetection).where(SceneDetection.video_asset_id == video_asset_id)
        stmt = stmt.order_by(SceneDetection.start_time)
        with self._session_factory() as session:
            return list(session.scalars(stmt))

    def list_for_project(self, project_id: str) -> list[SceneDetection]:
        stmt = select(SceneDetection).where(SceneDetection.project_id == project_id)
        stmt = stmt.order_by(SceneDetection.video_asset_id, SceneDetection.start_time)
        with self._session_factory() as session:
            return list(session.scalars(stmt))


class SubtitleSegmentRepository(SQLAlchemyRepository[SubtitleSegment]):
    def __init__(self, session_factory: SessionFactory = SessionLocal) -> None:
        super().__init__(SubtitleSegment, session_factory)

    def list_for_project(self, project_id: str, language: Optional[str] = None) -> list[SubtitleSegment]:
        stmt = select(SubtitleSegment).where(SubtitleSegment.project_id == project_id)
        if language is not None:
            stmt = stmt.where(SubtitleSegment.language == language)
        stmt = stmt.order_by(SubtitleSegment.start_time)
        with self._session_factory() as session:
            return list(session.scalars(stmt))

    def list_for_asset(self, video_asset_id: str) -> list[SubtitleSegment]:
        stmt = select(SubtitleSegment).where(SubtitleSegment.video_asset_id == video_asset_id)
        stmt = stmt.order_by(SubtitleSegment.start_time)
        with self._session_factory() as session:
            return list(session.scalars(stmt))


class TimelineClipRepository(SQLAlchemyRepository[TimelineClip]):
    def __init__(self, session_factory: SessionFactory = SessionLocal) -> None:
        super().__init__(TimelineClip, session_factory)

    def list_for_project(self, project_id: str) -> list[TimelineClip]:
        stmt = select(TimelineClip).where(TimelineClip.project_id == project_id)
        stmt = stmt.order_by(TimelineClip.track_index, TimelineClip.sequence_order)
        with self._session_factory() as session:
            return list(session.scalars(stmt))

    def list_for_asset(self, video_asset_id: str) -> list[TimelineClip]:
        stmt = select(TimelineClip).where(TimelineClip.video_asset_id == video_asset_id)
        stmt = stmt.order_by(TimelineClip.start_time)
        with self._session_factory() as session:
            return list(session.scalars(stmt))


class AudioTrackRepository(SQLAlchemyRepository[AudioTrack]):
    def __init__(self, session_factory: SessionFactory = SessionLocal) -> None:
        super().__init__(AudioTrack, session_factory)

    def list_for_project(self, project_id: str) -> list[AudioTrack]:
        stmt = select(AudioTrack).where(AudioTrack.project_id == project_id)
        stmt = stmt.order_by(AudioTrack.start_time)
        with self._session_factory() as session:
            return list(session.scalars(stmt))


class JobStatusRepository(SQLAlchemyRepository[JobStatus]):
    def __init__(self, session_factory: SessionFactory = SessionLocal) -> None:
        super().__init__(JobStatus, session_factory)

    def get_by_code(self, code: JobStatusCode) -> Optional[JobStatus]:
        stmt = select(JobStatus).where(JobStatus.code == code)
        with self._session_factory() as session:
            return session.scalar(stmt)


class ExportJobRepository(SQLAlchemyRepository[ExportJob]):
    def __init__(self, session_factory: SessionFactory = SessionLocal) -> None:
        super().__init__(ExportJob, session_factory)

    def list_for_project(self, project_id: str) -> list[ExportJob]:
        stmt = select(ExportJob).where(ExportJob.project_id == project_id)
        stmt = stmt.order_by(ExportJob.created_at.desc())
        with self._session_factory() as session:
            return list(session.scalars(stmt))

    def list_active(self) -> list[ExportJob]:
        active_codes = {JobStatusCode.QUEUED, JobStatusCode.RUNNING}
        stmt = (
            select(ExportJob)
            .join(ExportJob.status)
            .where(JobStatus.code.in_(active_codes))
            .order_by(ExportJob.requested_at)
        )
        with self._session_factory() as session:
            return list(session.scalars(stmt))

    def set_status(
        self,
        export_job_id: str,
        *,
        status: JobStatus,
        progress: Optional[float] = None,
        error_message: Optional[str] = None,
    ) -> ExportJob:
        update_data: dict[str, Any] = {"status_id": status.id}
        if progress is not None:
            update_data["progress"] = progress
        if error_message is not None:
            update_data["error_message"] = error_message
        return self.update(export_job_id, update_data)


__all__ = [
    "AudioTrackRepository",
    "ExportJobRepository",
    "JobStatusRepository",
    "NotFoundError",
    "ProjectRepository",
    "RepositoryError",
    "SQLAlchemyRepository",
    "SceneDetectionRepository",
    "SubtitleSegmentRepository",
    "TimelineClipRepository",
    "VideoAssetRepository",
]
