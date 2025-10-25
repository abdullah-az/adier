from __future__ import annotations

from datetime import datetime
from typing import Optional, Sequence

from loguru import logger

from app.models.pipeline import (
    AspectRatio,
    BackgroundMusicSpec,
    ExportTemplate,
    ResolutionPreset,
    SubtitleSpec,
    TimelineClip,
    TimelineCompositionRequest,
    WatermarkSpec,
)
from app.models.timeline import SubtitleTrack, Timeline, TimelineSegment
from app.repositories.project_repository import ProjectRepository
from app.repositories.timeline_repository import TimelineRepository
from app.repositories.video_repository import VideoAssetRepository
from app.services.job_service import JobService
from app.utils.storage import StorageManager


class TimelineValidationError(ValueError):
    """Raised when timeline configuration is invalid."""


class TimelineService:
    """Business logic layer for managing timeline blueprints and exports."""

    def __init__(
        self,
        timeline_repository: TimelineRepository,
        project_repository: ProjectRepository,
        video_repository: VideoAssetRepository,
        storage_manager: StorageManager,
        job_service: JobService,
    ) -> None:
        self.timeline_repository = timeline_repository
        self.project_repository = project_repository
        self.video_repository = video_repository
        self.storage_manager = storage_manager
        self.job_service = job_service

    # ---------------------------------------------------------------------
    # CRUD
    # ---------------------------------------------------------------------
    async def create_timeline(
        self,
        project_id: str,
        *,
        name: str,
        description: Optional[str] = None,
        locale: Optional[str] = None,
        segments: Optional[Sequence[TimelineSegment]] = None,
        background_music: Optional[BackgroundMusicSpec] = None,
        aspect_ratio: Optional[AspectRatio] = None,
        resolution: Optional[ResolutionPreset] = None,
        proxy_resolution: Optional[ResolutionPreset] = None,
        generate_thumbnails: Optional[bool] = None,
        export_templates: Optional[Sequence[ExportTemplate]] = None,
        default_watermark: Optional[WatermarkSpec] = None,
    ) -> Timeline:
        project = await self.project_repository.get(project_id)
        if project is None:
            raise TimelineValidationError("Project does not exist")
        locale = locale or project.locale
        segments_list = list(segments or [])
        await self._validate_segments(project_id, segments_list)
        resolved_aspect = aspect_ratio or project.default_aspect_ratio
        resolved_resolution = resolution or project.default_resolution
        resolved_proxy = proxy_resolution or ResolutionPreset.P720
        resolved_generate = generate_thumbnails if generate_thumbnails is not None else True
        timeline = Timeline(
            project_id=project_id,
            name=name,
            description=description,
            locale=locale,
            aspect_ratio=resolved_aspect,
            resolution=resolved_resolution,
            proxy_resolution=resolved_proxy,
            generate_thumbnails=resolved_generate,
            segments=segments_list,
            background_music=background_music,
            export_templates=list(export_templates or []),
            default_watermark=default_watermark,
        )
        await self.timeline_repository.add(timeline)
        project.timeline_ids.append(timeline.id)
        project.updated_at = datetime.utcnow()
        await self.project_repository.update(project)
        logger.info("Created timeline", project_id=project_id, timeline_id=timeline.id)
        return timeline

    async def update_timeline(
        self,
        project_id: str,
        timeline_id: str,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        locale: Optional[str] = None,
        segments: Optional[Sequence[TimelineSegment]] = None,
        aspect_ratio: Optional[AspectRatio] = None,
        resolution: Optional[ResolutionPreset] = None,
        proxy_resolution: Optional[ResolutionPreset] = None,
        generate_thumbnails: Optional[bool] = None,
    ) -> Optional[Timeline]:
        timeline = await self.timeline_repository.get(timeline_id)
        if timeline is None or timeline.project_id != project_id:
            return None
        if name is not None:
            timeline.name = name
        if description is not None:
            timeline.description = description
        if locale is not None:
            timeline.locale = locale
        if segments is not None:
            segments_list = list(segments)
            await self._validate_segments(project_id, segments_list)
            timeline.segments = segments_list
        if aspect_ratio is not None:
            timeline.aspect_ratio = aspect_ratio
        if resolution is not None:
            timeline.resolution = resolution
        if proxy_resolution is not None:
            timeline.proxy_resolution = proxy_resolution
        if generate_thumbnails is not None:
            timeline.generate_thumbnails = generate_thumbnails
        timeline.updated_at = datetime.utcnow()
        timeline.version += 1
        await self.timeline_repository.update(timeline)
        logger.info("Updated timeline", project_id=project_id, timeline_id=timeline.id)
        return timeline

    async def list_timelines(self, project_id: str) -> list[Timeline]:
        return await self.timeline_repository.list_by_project(project_id)

    async def get_timeline(self, project_id: str, timeline_id: str) -> Optional[Timeline]:
        timeline = await self.timeline_repository.get(timeline_id)
        if timeline is None or timeline.project_id != project_id:
            return None
        return timeline

    async def delete_timeline(self, project_id: str, timeline_id: str) -> bool:
        timeline = await self.timeline_repository.get(timeline_id)
        if timeline is None or timeline.project_id != project_id:
            return False
        await self.timeline_repository.delete(timeline_id)
        project = await self.project_repository.get(project_id)
        if project is not None:
            project.timeline_ids = [tid for tid in project.timeline_ids if tid != timeline_id]
            project.updated_at = datetime.utcnow()
            await self.project_repository.update(project)
        logger.info("Deleted timeline", project_id=project_id, timeline_id=timeline_id)
        return True

    # ---------------------------------------------------------------------
    # Music and subtitles
    # ---------------------------------------------------------------------
    async def set_background_music(
        self,
        project_id: str,
        timeline_id: str,
        background_music: Optional[BackgroundMusicSpec],
    ) -> Optional[Timeline]:
        timeline = await self.get_timeline(project_id, timeline_id)
        if timeline is None:
            return None
        if background_music is not None:
            # Validate track exists if provided
            if background_music.track:
                music_path = self.storage_manager.project_category_path(project_id, "music") / background_music.track
                if not music_path.exists():
                    raise TimelineValidationError("Background music track not found in project storage")
        timeline.background_music = background_music
        timeline.updated_at = datetime.utcnow()
        timeline.version += 1
        await self.timeline_repository.update(timeline)
        logger.info("Updated timeline music", project_id=project_id, timeline_id=timeline_id)
        return timeline

    async def update_export_templates(
        self,
        project_id: str,
        timeline_id: str,
        templates: Sequence[ExportTemplate],
    ) -> Optional[Timeline]:
        timeline = await self.get_timeline(project_id, timeline_id)
        if timeline is None:
            return None
        timeline.export_templates = list(templates)
        timeline.updated_at = datetime.utcnow()
        timeline.version += 1
        await self.timeline_repository.update(timeline)
        logger.info("Updated export templates", timeline_id=timeline_id, count=len(templates))
        return timeline

    async def set_default_watermark(
        self,
        project_id: str,
        timeline_id: str,
        watermark: Optional[WatermarkSpec],
    ) -> Optional[Timeline]:
        timeline = await self.get_timeline(project_id, timeline_id)
        if timeline is None:
            return None
        timeline.default_watermark = watermark
        timeline.updated_at = datetime.utcnow()
        timeline.version += 1
        await self.timeline_repository.update(timeline)
        logger.info("Updated timeline watermark", timeline_id=timeline_id, has_watermark=bool(watermark))
        return timeline

    async def upsert_subtitle_track(
        self,
        project_id: str,
        timeline_id: str,
        track: SubtitleTrack,
    ) -> Optional[Timeline]:
        timeline = await self.get_timeline(project_id, timeline_id)
        if timeline is None:
            return None
        self._validate_subtitle_track(track)
        existing = next((item for item in timeline.subtitle_tracks if item.id == track.id), None)
        if existing is None:
            timeline.subtitle_tracks.append(track)
        else:
            existing.locale = track.locale
            existing.title = track.title
            existing.segments = track.segments
        timeline.updated_at = datetime.utcnow()
        timeline.version += 1
        await self.timeline_repository.update(timeline)
        logger.info("Updated subtitle track", timeline_id=timeline_id, track_id=track.id)
        return timeline

    # ---------------------------------------------------------------------
    # Thumbnails & downloads
    # ---------------------------------------------------------------------
    async def collect_segment_thumbnails(self, timeline: Timeline) -> list[dict]:
        thumbnails: list[dict] = []
        for segment in timeline.segments:
            asset = await self.video_repository.get(segment.asset_id)
            if not asset:
                continue
            clip_thumbnails = asset.metadata.get("clip_thumbnails") if isinstance(asset.metadata, dict) else None
            if not clip_thumbnails:
                continue
            for thumb in clip_thumbnails:
                thumbnails.append(
                    {
                        "asset_id": asset.id,
                        "segment_id": segment.id,
                        "clip_index": thumb.get("clip_index"),
                        "path": thumb.get("path"),
                        "generated_at": thumb.get("generated_at"),
                    }
                )
        return thumbnails

    # ---------------------------------------------------------------------
    # Jobs & exports
    # ---------------------------------------------------------------------
    async def create_preview_job(self, timeline: Timeline) -> str:
        request = await self._build_composition_request(timeline)
        job = await self.job_service.create_job(
            timeline.project_id,
            "export",
            payload={
                "mode": "preview",
                "timeline_id": timeline.id,
                "timeline": request.model_dump(),
            },
        )
        timeline.last_preview_job_id = job.id
        timeline.updated_at = datetime.utcnow()
        await self.timeline_repository.update(timeline)
        return job.id

    async def create_export_job(self, timeline: Timeline) -> str:
        request = await self._build_composition_request(timeline)
        job = await self.job_service.create_job(
            timeline.project_id,
            "export",
            payload={
                "mode": "export",
                "timeline_id": timeline.id,
                "timeline": request.model_dump(),
            },
        )
        timeline.last_export_job_id = job.id
        timeline.updated_at = datetime.utcnow()
        await self.timeline_repository.update(timeline)
        return job.id

    async def job_progress(self, project_id: str, timeline: Timeline) -> dict:
        payload: dict[str, Optional[dict]] = {"preview": None, "export": None}
        if timeline.last_preview_job_id:
            job = await self.job_service.get_job(timeline.last_preview_job_id)
            if job and job.project_id == project_id:
                payload["preview"] = self.job_service.serialize(job)
        if timeline.last_export_job_id:
            job = await self.job_service.get_job(timeline.last_export_job_id)
            if job and job.project_id == project_id:
                payload["export"] = self.job_service.serialize(job)
        return payload

    # ---------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------
    async def _validate_segments(self, project_id: str, segments: Sequence[TimelineSegment]) -> None:
        if not segments:
            return
        ordered = sorted(segments, key=lambda seg: seg.timeline_start)
        tolerance = 1e-3
        expected_start = 0.0
        for index, segment in enumerate(ordered):
            if segment.duration() <= 0:
                raise TimelineValidationError(f"Segment {index + 1} must have positive duration")
            if abs(segment.timeline_start - expected_start) > tolerance:
                if segment.timeline_start > expected_start:
                    raise TimelineValidationError(
                        f"Gap detected before segment {index + 1}; expected start {expected_start:.2f}s"
                    )
                raise TimelineValidationError(
                    f"Overlap detected at segment {index + 1}; starts at {segment.timeline_start:.2f}s"
                )
            asset = await self.video_repository.get(segment.asset_id)
            if asset is None or asset.project_id != project_id:
                raise TimelineValidationError(f"Segment {index + 1} references unknown asset '{segment.asset_id}'")
            seen_assets.add(segment.asset_id)
            expected_start = segment.timeline_end

    def _validate_subtitle_track(self, track: SubtitleTrack) -> None:
        ordered = sorted(track.segments, key=lambda segment: segment.start)
        tolerance = 1e-3
        previous_end = 0.0
        for index, segment in enumerate(ordered):
            if segment.end <= segment.start:
                raise TimelineValidationError(f"Subtitle segment {index + 1} must end after it starts")
            if segment.start < previous_end - tolerance:
                raise TimelineValidationError(f"Subtitle segment {index + 1} overlaps with previous segment")
            previous_end = segment.end

    async def _build_composition_request(self, timeline: Timeline) -> TimelineCompositionRequest:
        ordered_segments = sorted(timeline.segments, key=lambda seg: seg.timeline_start)
        if not ordered_segments:
            raise TimelineValidationError("Timeline has no segments configured")
        clips = [segment.to_clip() for segment in ordered_segments]
        request = TimelineCompositionRequest(
            clips=clips,
            aspect_ratio=timeline.aspect_ratio,
            resolution=timeline.resolution,
            proxy_resolution=timeline.proxy_resolution,
            generate_thumbnails=timeline.generate_thumbnails,
        )
        if timeline.background_music is not None:
            request.background_music = timeline.background_music
        if timeline.default_watermark is not None:
            request.default_watermark = timeline.default_watermark
        if timeline.export_templates:
            request.export_templates = list(timeline.export_templates)
        track = timeline.get_subtitle_track(timeline.locale)
        if track and track.segments:
            subtitle_spec = await self._write_subtitle_file(timeline, track)
            request.global_subtitles = subtitle_spec
        return request

    async def _write_subtitle_file(self, timeline: Timeline, track: SubtitleTrack) -> SubtitleSpec:
        storage_path = self.storage_manager.project_category_path(timeline.project_id, "processed")
        storage_path.mkdir(parents=True, exist_ok=True)
        filename = f"timeline_{timeline.id}_{track.locale}.srt"
        file_path = storage_path / filename
        contents = self._render_srt(track)
        file_path.write_text(contents, encoding="utf-8")
        relative = file_path.relative_to(self.storage_manager.storage_root)
        return SubtitleSpec(path=str(relative))

    def _render_srt(self, track: SubtitleTrack) -> str:
        def _format_time(value: float) -> str:
            hours = int(value // 3600)
            minutes = int((value % 3600) // 60)
            seconds = int(value % 60)
            milliseconds = int((value - int(value)) * 1000)
            return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

        lines: list[str] = []
        for index, segment in enumerate(sorted(track.segments, key=lambda item: item.start), start=1):
            lines.append(str(index))
            lines.append(f"{_format_time(segment.start)} --> {_format_time(segment.end)}")
            lines.append(segment.text)
            lines.append("")
        return "\n".join(lines).strip() + "\n"
