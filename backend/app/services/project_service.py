from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Optional, Tuple
from uuid import uuid4

from loguru import logger

from app.models.pipeline import (
    BackgroundMusicSpec,
    SubtitleSpec,
    TimelineCompositionRequest,
    TransitionType,
)
from app.models.project import ClipTiming, Project, ProjectStatus, TimelineState
from app.models.video_asset import VideoAsset
from app.repositories.project_repository import ProjectRepository
from app.repositories.video_repository import VideoAssetRepository
from app.utils.storage import StorageManager

_TOLERANCE = 1e-3


class ProjectNotFoundError(Exception):
    """Raised when a project identifier cannot be resolved."""


@dataclass(slots=True)
class TimelineValidationError(Exception):
    """Rich validation error surfaced when timeline constraints are violated."""

    code: str
    message: str
    details: dict[str, Any]

    def __init__(self, code: str, message: str, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message)
        object.__setattr__(self, "code", code)
        object.__setattr__(self, "message", message)
        object.__setattr__(self, "details", details or {})


class ProjectService:
    """High-level orchestration for managing project lifecycle and timeline state."""

    def __init__(
        self,
        *,
        repository: ProjectRepository,
        storage_manager: StorageManager,
        video_repository: VideoAssetRepository,
    ) -> None:
        self.repository = repository
        self.storage_manager = storage_manager
        self.video_repository = video_repository

    # ------------------------------------------------------------------
    # Project lifecycle operations
    # ------------------------------------------------------------------
    async def list_projects(
        self,
        *,
        page: int,
        page_size: int,
        sort: str,
        locale: Optional[str] = None,
    ) -> Tuple[list[Project], int]:
        projects = await self.repository.all_projects()
        if locale:
            projects = [
                project
                for project in projects
                if locale in project.supported_locales or project.primary_locale == locale
            ]

        sort_field, direction = self._parse_sort(sort)
        projects.sort(key=lambda item: self._sort_key(item, sort_field), reverse=(direction == "desc"))

        total = len(projects)
        start = max((page - 1) * page_size, 0)
        end = start + page_size
        return projects[start:end], total

    async def create_project(
        self,
        *,
        name: str,
        description: Optional[str],
        primary_locale: str,
        supported_locales: Iterable[str],
        tags: Iterable[str],
        metadata: dict[str, Any],
        project_id: Optional[str] = None,
    ) -> Project:
        now = datetime.utcnow()
        identifier = project_id or str(uuid4())
        locales = list(dict.fromkeys([primary_locale, *supported_locales])) or [primary_locale]
        project = Project(
            id=identifier,
            name=name,
            description=description,
            status=ProjectStatus.DRAFT,
            primary_locale=primary_locale,
            supported_locales=locales,
            tags=list(tags),
            metadata=dict(metadata or {}),
            timeline=None,
            created_at=now,
            updated_at=now,
        )
        self.storage_manager.ensure_project_directories(project.id)
        await self.repository.add(project)
        logger.info("Created project", project_id=project.id, name=project.name)
        return project

    async def get_project(self, project_id: str) -> Project:
        project = await self.repository.get(project_id)
        if project is None:
            raise ProjectNotFoundError(project_id)
        return project

    async def update_project(
        self,
        project_id: str,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[ProjectStatus] = None,
        primary_locale: Optional[str] = None,
        supported_locales: Optional[Iterable[str]] = None,
        tags: Optional[Iterable[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Project:
        project = await self.get_project(project_id)
        if name is not None:
            project.name = name
        if description is not None:
            project.description = description
        if status is not None:
            project.status = status
        if primary_locale is not None:
            project.primary_locale = primary_locale
        if supported_locales is not None:
            merged = list(dict.fromkeys([project.primary_locale, *supported_locales]))
            project.supported_locales = merged
        if tags is not None:
            project.tags = list(tags)
        if metadata is not None:
            project.metadata.update(metadata)
        if project.primary_locale not in project.supported_locales:
            project.supported_locales.insert(0, project.primary_locale)
        project.updated_at = datetime.utcnow()
        await self.repository.update(project)
        logger.info("Updated project", project_id=project.id)
        return project

    async def delete_project(self, project_id: str, *, delete_storage: bool = True) -> None:
        await self.get_project(project_id)
        await self.repository.delete(project_id)
        if delete_storage:
            self.storage_manager.cleanup_project(project_id)
        logger.info("Deleted project", project_id=project_id, storage_deleted=delete_storage)

    # ------------------------------------------------------------------
    # Timeline management
    # ------------------------------------------------------------------
    async def get_timeline(self, project_id: str) -> Optional[TimelineState]:
        project = await self.get_project(project_id)
        return project.timeline

    async def update_timeline(
        self,
        project_id: str,
        *,
        composition: TimelineCompositionRequest,
        layout: Iterable[ClipTiming],
        locale: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
        global_subtitles: Optional[SubtitleSpec] = None,
        background_music: Optional[BackgroundMusicSpec] = None,
    ) -> TimelineState:
        project = await self.get_project(project_id)
        layout_models = [ClipTiming(**item.model_dump()) if not isinstance(item, ClipTiming) else item for item in layout]
        (
            validated_layout,
            updated_composition,
            total_duration,
        ) = await self._validate_timeline(project_id, layout_models, composition)

        existing_metadata = dict(project.timeline.metadata) if project.timeline else {}
        combined_metadata = {**existing_metadata, **(metadata or {})}

        if background_music is not None:
            updated_composition.background_music = background_music
        elif project.timeline and project.timeline.background_music and updated_composition.background_music is None:
            updated_composition.background_music = project.timeline.background_music

        if global_subtitles is not None:
            updated_composition.global_subtitles = global_subtitles
        elif project.timeline and project.timeline.global_subtitles and updated_composition.global_subtitles is None:
            updated_composition.global_subtitles = project.timeline.global_subtitles

        timeline_kwargs = dict(
            locale=locale or project.primary_locale,
            layout=validated_layout,
            composition=updated_composition,
            total_duration=total_duration,
            metadata=combined_metadata,
            last_preview_job_id=project.timeline.last_preview_job_id if project.timeline else None,
            last_export_job_id=project.timeline.last_export_job_id if project.timeline else None,
            global_subtitles=updated_composition.global_subtitles,
            background_music=updated_composition.background_music,
            updated_at=datetime.utcnow(),
        )
        if project.timeline:
            timeline_kwargs["timeline_id"] = project.timeline.timeline_id

        timeline = TimelineState(**timeline_kwargs)

        project.timeline = timeline
        project.status = ProjectStatus.EDITING
        project.updated_at = timeline.updated_at
        if timeline.locale not in project.supported_locales:
            project.supported_locales.append(timeline.locale)
        await self.repository.update(project)
        logger.info(
            "Timeline updated",
            project_id=project.id,
            clips=len(validated_layout),
            duration=total_duration,
        )
        return timeline

    async def update_timeline_music(
        self,
        project_id: str,
        music: Optional[BackgroundMusicSpec],
    ) -> TimelineState:
        timeline = await self.get_timeline(project_id)
        if timeline is None:
            raise TimelineValidationError("timeline_missing", "Timeline must be created before configuring music")
        timeline.background_music = music
        timeline.composition.background_music = music
        timeline.updated_at = datetime.utcnow()
        project = await self.get_project(project_id)
        project.timeline = timeline
        project.updated_at = timeline.updated_at
        await self.repository.update(project)
        logger.info("Updated timeline music", project_id=project_id, has_music=bool(music))
        return timeline

    async def update_timeline_subtitles(
        self,
        project_id: str,
        subtitles: Optional[SubtitleSpec],
    ) -> TimelineState:
        timeline = await self.get_timeline(project_id)
        if timeline is None:
            raise TimelineValidationError("timeline_missing", "Timeline must be created before editing subtitles")
        timeline.global_subtitles = subtitles
        timeline.composition.global_subtitles = subtitles
        timeline.updated_at = datetime.utcnow()
        project = await self.get_project(project_id)
        project.timeline = timeline
        project.updated_at = timeline.updated_at
        await self.repository.update(project)
        logger.info("Updated timeline subtitles", project_id=project_id, has_subtitles=bool(subtitles))
        return timeline

    async def record_timeline_job(self, project_id: str, *, job_id: str, kind: str) -> None:
        timeline = await self.get_timeline(project_id)
        if timeline is None:
            return
        if kind == "preview":
            timeline.last_preview_job_id = job_id
        elif kind == "export":
            timeline.last_export_job_id = job_id
        timeline.updated_at = datetime.utcnow()
        project = await self.get_project(project_id)
        project.timeline = timeline
        project.updated_at = timeline.updated_at
        await self.repository.update(project)
        logger.debug("Recorded timeline job", project_id=project_id, job_id=job_id, kind=kind)

    # ------------------------------------------------------------------
    # Media utilities
    # ------------------------------------------------------------------
    async def list_music_options(self, project_id: str) -> list[dict[str, Any]]:
        await self.get_project(project_id)
        music_dir = self.storage_manager.project_category_path(project_id, "music")
        if not music_dir.exists():
            return []
        options: list[dict[str, Any]] = []
        for path in sorted(music_dir.iterdir()):
            if path.is_file():
                options.append(
                    {
                        "track": path.name,
                        "path": path.relative_to(self.storage_manager.storage_root).as_posix(),
                        "size_bytes": path.stat().st_size,
                    }
                )
        return options

    async def list_thumbnails(self, project_id: str) -> list[dict[str, Any]]:
        await self.get_project(project_id)
        assets = await self.video_repository.list_by_project(project_id)
        thumbnails: list[dict[str, Any]] = []
        for asset in assets:
            if asset.thumbnail_path:
                thumbnails.append(
                    {
                        "asset_id": asset.id,
                        "path": asset.thumbnail_path,
                        "generated_at": asset.updated_at.isoformat(),
                    }
                )
            clip_thumbs = asset.metadata.get("clip_thumbnails") if asset.metadata else None
            if isinstance(clip_thumbs, list):
                thumbnails.extend(
                    {
                        "asset_id": asset.id,
                        "path": thumb.get("path"),
                        "clip_index": thumb.get("clip_index"),
                        "generated_at": thumb.get("generated_at"),
                    }
                    for thumb in clip_thumbs
                    if thumb.get("path")
                )
        return thumbnails

    async def resolve_asset_path(
        self,
        asset_id: str,
        *,
        project_id: Optional[str] = None,
    ) -> tuple[Path, VideoAsset]:
        asset = await self.video_repository.get(asset_id)
        if asset is None:
            raise FileNotFoundError(f"Asset {asset_id} not found")
        if project_id and asset.project_id != project_id:
            raise FileNotFoundError(f"Asset {asset_id} not part of project {project_id}")
        path = (self.storage_manager.storage_root / asset.relative_path).resolve()
        return path, asset

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _parse_sort(self, value: str) -> tuple[str, str]:
        if ":" in value:
            field, direction = value.split(":", 1)
        else:
            field, direction = value, "asc"
        field = field.strip().lower()
        direction = direction.strip().lower()
        if direction not in {"asc", "desc"}:
            direction = "asc"
        if field not in {"created_at", "updated_at", "name"}:
            field = "created_at"
        return field, direction

    def _sort_key(self, project: Project, field: str) -> Any:
        if field == "name":
            return project.name.lower()
        if field == "updated_at":
            return project.updated_at
        return project.created_at

    async def _validate_timeline(
        self,
        project_id: str,
        layout: list[ClipTiming],
        composition: TimelineCompositionRequest,
    ) -> tuple[list[ClipTiming], TimelineCompositionRequest, float]:
        if not composition.clips:
            raise TimelineValidationError("timeline_empty", "Timeline requires at least one clip")
        if len(layout) != len(composition.clips):
            raise TimelineValidationError(
                "timeline_mismatch",
                "Layout length must match composition clip count",
                details={"layout": len(layout), "clips": len(composition.clips)},
            )

        ordered_layout = sorted(layout, key=lambda clip: clip.start)
        if any(ordered_layout[i].start + _TOLERANCE < ordered_layout[i - 1].start for i in range(1, len(ordered_layout))):
            raise TimelineValidationError("timeline_unsorted", "Clip layout must be ordered by start time")

        validated: list[ClipTiming] = []
        previous_end = 0.0
        previous_duration = 0.0
        previous_transition = None
        seen_ids: set[str] = set()

        for index, (layout_item, clip) in enumerate(zip(ordered_layout, composition.clips)):
            if layout_item.clip_id in seen_ids:
                raise TimelineValidationError(
                    "timeline_duplicate_clip",
                    "Clip identifiers must be unique",
                    details={"clip_id": layout_item.clip_id},
                )
            seen_ids.add(layout_item.clip_id)

            if layout_item.asset_id != clip.asset_id:
                raise TimelineValidationError(
                    "timeline_asset_mismatch",
                    "Layout asset does not match composition asset",
                    details={"clip_id": layout_item.clip_id, "layout_asset": layout_item.asset_id, "composition_asset": clip.asset_id},
                )

            duration = float(layout_item.duration)
            if duration <= 0:
                raise TimelineValidationError(
                    "timeline_invalid_duration",
                    "Clip duration must be positive",
                    details={"clip_id": layout_item.clip_id},
                )

            if layout_item.out_point is None:
                layout_item.out_point = layout_item.in_point + duration
            elif layout_item.out_point - layout_item.in_point <= 0:
                raise TimelineValidationError(
                    "timeline_invalid_out_point",
                    "Clip out-point must be greater than in-point",
                    details={"clip_id": layout_item.clip_id},
                )
            else:
                duration = layout_item.out_point - layout_item.in_point

            asset = await self.video_repository.get(layout_item.asset_id)
            if asset is None:
                raise TimelineValidationError(
                    "timeline_asset_missing",
                    "Referenced video asset could not be found",
                    details={"asset_id": layout_item.asset_id},
                )

            available_duration = None
            if asset.metadata:
                try:
                    available_duration = float(asset.metadata.get("duration"))
                except (TypeError, ValueError):  # pragma: no cover - defensive
                    available_duration = None

            if available_duration is not None and layout_item.in_point + duration - available_duration > _TOLERANCE:
                raise TimelineValidationError(
                    "timeline_out_of_bounds",
                    "Clip selection exceeds source media duration",
                    details={"asset_id": asset.id, "available": available_duration, "requested": layout_item.in_point + duration},
                )

            if index == 0:
                if layout_item.start > _TOLERANCE:
                    raise TimelineValidationError(
                        "timeline_gap",
                        "Timeline must start at zero",
                        details={"gap": layout_item.start},
                    )
            else:
                allowed_overlap = self._allowed_overlap(previous_transition, previous_duration, duration)
                expected_start = max(0.0, previous_end - allowed_overlap)
                if layout_item.start - expected_start > _TOLERANCE:
                    raise TimelineValidationError(
                        "timeline_gap",
                        "Gap detected between clips",
                        details={
                            "gap": layout_item.start - expected_start,
                            "clip_id": layout_item.clip_id,
                            "expected_start": expected_start,
                            "actual_start": layout_item.start,
                        },
                    )
                if layout_item.start + _TOLERANCE < expected_start:
                    raise TimelineValidationError(
                        "timeline_overlap",
                        "Clips overlap beyond allowed transition",
                        details={
                            "overlap": expected_start - layout_item.start,
                            "clip_id": layout_item.clip_id,
                            "expected_start": expected_start,
                            "actual_start": layout_item.start,
                        },
                    )

            clip.in_point = layout_item.in_point
            clip.out_point = layout_item.out_point
            clip.include_audio = layout_item.include_audio
            previous_end = layout_item.start + duration
            previous_duration = duration
            previous_transition = clip.transition
            validated.append(layout_item)

        total_duration = previous_end
        return validated, composition, total_duration

    def _allowed_overlap(self, transition, previous_duration: float, current_duration: float) -> float:
        if transition is None:
            return 0.0
        try:
            transition_type = transition.type
            duration = float(transition.duration)
        except AttributeError:  # pragma: no cover - defensive
            return 0.0
        if transition_type != TransitionType.CROSSFADE:
            return 0.0
        return max(0.0, min(duration, previous_duration, current_duration))
