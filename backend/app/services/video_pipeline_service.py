from __future__ import annotations

import asyncio
import hashlib
import inspect
import math
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Awaitable, Callable, Iterable, Optional
from uuid import uuid4

from loguru import logger

from app.core.config import Settings
from app.models.pipeline import (
    BackgroundMusicSpec,
    GeneratedMedia,
    ThumbnailInfo,
    TimelineClip,
    TimelineCompositionRequest,
    TimelineCompositionResult,
    TransitionType,
)
from app.models.video_asset import VideoAsset
from app.repositories.video_repository import VideoAssetRepository
from app.utils.ffmpeg import (
    FFmpegError,
    apply_fade,
    burn_subtitles,
    concat_videos,
    crossfade_videos,
    extract_thumbnail,
    generate_keyframe_thumbnails,
    get_video_metadata,
    mix_audio_tracks,
    overlay_watermark,
    transcode_video,
    trim_video,
)
from app.utils.storage import StorageManager


LogCallback = Callable[[str, dict[str, Any]], Awaitable[None]]
ProgressCallback = Callable[[float, str], Awaitable[None]]


class PipelineError(Exception):
    """Raised when the video pipeline encounters a fatal issue."""


@dataclass
class ProcessedClip:
    clip: TimelineClip
    path: Path
    metadata: dict[str, Any]
    thumbnail_path: Optional[Path] = None
    has_audio: bool = True


class VideoPipelineService:
    """High level service orchestrating FFmpeg-based video timeline workflows."""

    def __init__(
        self,
        storage_manager: StorageManager,
        video_repository: VideoAssetRepository,
        settings: Settings,
    ) -> None:
        self.storage_manager = storage_manager
        self.video_repository = video_repository
        self.settings = settings
        self._ffmpeg_threads = max(settings.ffmpeg_threads, 1)
        self._ffmpeg_semaphore = asyncio.Semaphore(self._ffmpeg_threads)

    async def compose_timeline(
        self,
        project_id: str,
        request: TimelineCompositionRequest,
        *,
        log: Optional[LogCallback] = None,
        progress: Optional[ProgressCallback] = None,
    ) -> TimelineCompositionResult:
        """Compose a timeline and produce exports based on the provided request."""

        if not request.clips:
            raise PipelineError("Timeline composition requires at least one clip")

        self.storage_manager.ensure_project_directories(project_id)
        await self._log(log, "Starting timeline composition", project_id=project_id)
        await self._progress(progress, 5.0, "Preparing assets")

        clip_assets = await self._load_clip_assets(request.clips)

        processed_clips = await self._process_clips(
            project_id,
            request,
            clip_assets,
            log=log,
            progress=progress,
        )

        await self._progress(progress, 40.0, "Concatenating clips")
        timeline_path, timeline_metadata = await self._compose_timeline(
            project_id,
            processed_clips,
            request,
        )
        timeline_has_audio = any(clip.has_audio for clip in processed_clips)

        if request.background_music and request.background_music.is_configured:
            await self._progress(progress, 55.0, "Integrating background music")
            timeline_path, timeline_metadata = await self._apply_background_music(
                project_id,
                timeline_path,
                timeline_metadata,
                request.background_music,
                timeline_has_audio,
            )
            timeline_has_audio = True

        if request.global_subtitles is not None:
            await self._progress(progress, 60.0, "Burning global subtitles")
            timeline_path, timeline_metadata = await self._burn_global_subtitles(
                project_id,
                timeline_path,
                request.global_subtitles,
            )

        if request.default_watermark is not None:
            await self._progress(progress, 65.0, "Applying default watermark")
            timeline_path, timeline_metadata = await self._apply_watermark(
                project_id,
                timeline_path,
                request.default_watermark,
            )

        await self._progress(progress, 70.0, "Registering timeline asset")
        source_asset_ids = sorted({clip.clip.asset_id for clip in processed_clips})
        timeline_asset = await self._register_asset(
            project_id,
            timeline_path,
            category="processed",
            source_asset_ids=source_asset_ids,
            label="Timeline",
            metadata=timeline_metadata,
        )

        proxy_asset = await self._generate_proxy(
            project_id,
            timeline_path,
            request,
            timeline_metadata,
            source_asset_ids,
            progress,
        )

        await self._progress(progress, 80.0, "Generating exports")
        export_assets = await self._generate_exports(
            project_id,
            timeline_path,
            request,
            source_asset_ids,
            progress,
        )

        thumbnails = await self._collect_thumbnails(
            project_id,
            request,
            processed_clips,
            timeline_path,
            progress,
        )

        result = TimelineCompositionResult(
            timeline=self._to_generated_media(timeline_asset),
            proxy=self._to_generated_media(proxy_asset) if proxy_asset else None,
            exports=[self._to_generated_media(asset) for asset in export_assets],
            thumbnails=thumbnails,
        )

        await self._progress(progress, 95.0, "Finalising timeline outputs")
        await self._log(log, "Timeline composition complete", outputs=len(result.exports))
        return result

    async def _process_clips(
        self,
        project_id: str,
        request: TimelineCompositionRequest,
        clip_assets: dict[str, VideoAsset],
        *,
        log: Optional[LogCallback],
        progress: Optional[ProgressCallback],
    ) -> list[ProcessedClip]:
        incoming_fades = self._build_incoming_fade_map(request.clips)
        processed: list[ProcessedClip] = []

        for index, clip in enumerate(request.clips):
            await self._log(
                log,
                "Processing clip",
                index=index,
                asset_id=clip.asset_id,
            )
            source_asset = clip_assets.get(clip.asset_id)
            if source_asset is None:
                raise PipelineError(f"Clip references unknown asset '{clip.asset_id}'")

            source_path = (self.storage_manager.storage_root / source_asset.relative_path).resolve()
            if not source_path.exists():
                raise PipelineError(f"Source media not found at '{source_path}'")

            clip_path = self._output_path(project_id, "processed", f"clip_{index:03d}", ".mp4")
            clip_path = await self._ffmpeg(trim_video, source_path, clip_path, start=clip.in_point, end=clip.out_point, include_audio=clip.include_audio)
            clip_metadata = await get_video_metadata(clip_path)
            has_audio = clip_metadata.get("has_audio", False) and clip.include_audio

            incoming = incoming_fades.get(index)
            fade_in_duration = incoming["duration"] if incoming else None
            fade_in_color = incoming["color"] if incoming else "black"

            if clip.transition.type in {TransitionType.FADE_TO_BLACK, TransitionType.FADE_TO_WHITE}:
                fade_out_duration = clip.transition.duration
                fade_out_color = "white" if clip.transition.type == TransitionType.FADE_TO_WHITE else "black"
            else:
                fade_out_duration = None
                fade_out_color = "black"

            if fade_in_duration or fade_out_duration:
                faded_path = self._output_path(project_id, "processed", f"clip_{index:03d}_fade", ".mp4")
                faded_path = await self._ffmpeg(
                    apply_fade,
                    clip_path,
                    faded_path,
                    fade_in=fade_in_duration,
                    fade_out=fade_out_duration,
                    total_duration=clip_metadata.get("duration"),
                    fade_in_color=fade_in_color,
                    fade_out_color=fade_out_color,
                )
                clip_path.unlink(missing_ok=True)
                clip_path = faded_path
                clip_metadata = await get_video_metadata(clip_path)
                has_audio = clip_metadata.get("has_audio", False)

            if clip.subtitles is not None:
                subtitle_path = self._resolve_storage_path(project_id, clip.subtitles.path)
                subtitled = self._output_path(project_id, "processed", f"clip_{index:03d}_subs", ".mp4")
                subtitled = await self._ffmpeg(
                    burn_subtitles,
                    clip_path,
                    subtitle_path,
                    subtitled,
                    encoding=clip.subtitles.encoding,
                    force_style=clip.subtitles.force_style,
                )
                clip_path.unlink(missing_ok=True)
                clip_path = subtitled
                clip_metadata = await get_video_metadata(clip_path)
                has_audio = clip_metadata.get("has_audio", False)

            watermark = clip.watermark or request.default_watermark
            if watermark is not None:
                watermark_path = self._resolve_storage_path(project_id, watermark.path)
                watermarked = self._output_path(project_id, "processed", f"clip_{index:03d}_wm", ".mp4")
                watermarked = await self._ffmpeg(
                    overlay_watermark,
                    clip_path,
                    watermark_path,
                    watermarked,
                    position=watermark.position,
                    scale=watermark.scale,
                    opacity=watermark.opacity,
                )
                clip_path.unlink(missing_ok=True)
                clip_path = watermarked
                clip_metadata = await get_video_metadata(clip_path)

            thumbnail_path: Optional[Path] = None
            if request.generate_thumbnails:
                duration = float(clip_metadata.get("duration") or 0.0)
                midpoint = max(duration / 2, 0.1)
                timestamp = min(midpoint, max(duration - 0.1, 0.1))
                thumbnail_path = self._output_path(project_id, "thumbnails", f"clip_{index:03d}", ".jpg")
                await self._ffmpeg(
                    extract_thumbnail,
                    clip_path,
                    thumbnail_path,
                    timestamp=timestamp,
                )
                relative_thumb = self._relative_path(thumbnail_path)
                source_asset.metadata.setdefault("clip_thumbnails", []).append(
                    {
                        "clip_index": index,
                        "path": relative_thumb,
                        "generated_at": datetime.utcnow().isoformat(),
                    }
                )
                source_asset.updated_at = datetime.utcnow()
                await self.video_repository.update(source_asset)
                clip_assets[clip.asset_id] = source_asset

            processed.append(
                ProcessedClip(
                    clip=clip,
                    path=clip_path,
                    metadata=clip_metadata,
                    thumbnail_path=thumbnail_path,
                    has_audio=has_audio,
                )
            )

            clip_progress = 20.0 * ((index + 1) / len(request.clips))
            await self._progress(progress, 10.0 + clip_progress, f"Processed clip {index + 1}/{len(request.clips)}")

        return processed

    async def _compose_timeline(
        self,
        project_id: str,
        clips: list[ProcessedClip],
        request: TimelineCompositionRequest,
    ) -> tuple[Path, dict[str, Any]]:
        if len(clips) == 1:
            final_path = self._output_path(project_id, "processed", "timeline", ".mp4")
            shutil.copy(clips[0].path, final_path)
            metadata = await get_video_metadata(final_path)
            return final_path, metadata

        current_path = clips[0].path
        current_metadata = clips[0].metadata
        cleanup: list[Path] = []
        source_paths = {clip.path for clip in clips}

        for index in range(1, len(clips)):
            transition = clips[index - 1].clip.transition
            next_clip = clips[index]
            step_path = self._output_path(project_id, "processed", f"timeline_step_{index:03d}", ".mp4")

            if transition.type == TransitionType.CROSSFADE:
                await self._ffmpeg(
                    crossfade_videos,
                    current_path,
                    next_clip.path,
                    step_path,
                    duration=transition.duration,
                    style=transition.style,
                    first_duration=current_metadata.get("duration"),
                )
            else:
                await self._ffmpeg(
                    concat_videos,
                    [current_path, next_clip.path],
                    step_path,
                )

            if current_path not in source_paths:
                cleanup.append(current_path)
            current_path = step_path
            current_metadata = await get_video_metadata(current_path)

        final_path = self._output_path(project_id, "processed", "timeline", ".mp4")
        if final_path.exists():
            final_path.unlink()
        shutil.move(current_path, final_path)
        for path in cleanup:
            path.unlink(missing_ok=True)
        metadata = await get_video_metadata(final_path)
        return final_path, metadata

    async def _apply_background_music(
        self,
        project_id: str,
        timeline_path: Path,
        metadata: dict[str, Any],
        music: BackgroundMusicSpec,
        base_has_audio: bool,
    ) -> tuple[Path, dict[str, Any]]:
        music_path = self._resolve_music_path(project_id, music.track)
        if music_path is None or not music_path.exists():
            raise PipelineError(f"Background music '{music.track}' not found in storage/music")

        mixed_path = self._output_path(project_id, "processed", "timeline_music", ".mp4")
        duration = metadata.get("duration")
        await self._ffmpeg(
            mix_audio_tracks,
            timeline_path,
            music_path,
            mixed_path,
            music_volume=music.volume,
            fade_in=music.fade_in,
            fade_out=music.fade_out,
            duration=duration,
            offset=music.offset,
            ducking=self._ducking_to_dict(music),
            loop=music.loop,
            base_has_audio=base_has_audio,
        )
        timeline_path.unlink(missing_ok=True)
        return mixed_path, await get_video_metadata(mixed_path)

    async def _burn_global_subtitles(
        self,
        project_id: str,
        timeline_path: Path,
        subtitle_spec,
    ) -> tuple[Path, dict[str, Any]]:
        subtitle_path = self._resolve_storage_path(project_id, subtitle_spec.path)
        if not subtitle_path.exists():
            raise PipelineError(f"Subtitle file '{subtitle_path}' not found")
        subtitled_path = self._output_path(project_id, "processed", "timeline_subs", ".mp4")
        await self._ffmpeg(
            burn_subtitles,
            timeline_path,
            subtitle_path,
            subtitled_path,
            encoding=subtitle_spec.encoding,
            force_style=subtitle_spec.force_style,
        )
        timeline_path.unlink(missing_ok=True)
        return subtitled_path, await get_video_metadata(subtitled_path)

    async def _apply_watermark(
        self,
        project_id: str,
        timeline_path: Path,
        watermark_spec,
    ) -> tuple[Path, dict[str, Any]]:
        watermark_path = self._resolve_storage_path(project_id, watermark_spec.path)
        if not watermark_path.exists():
            raise PipelineError(f"Watermark asset '{watermark_spec.path}' not found")
        watermarked_path = self._output_path(project_id, "processed", "timeline_wm", ".mp4")
        await self._ffmpeg(
            overlay_watermark,
            timeline_path,
            watermark_path,
            watermarked_path,
            position=watermark_spec.position,
            scale=watermark_spec.scale,
            opacity=watermark_spec.opacity,
        )
        timeline_path.unlink(missing_ok=True)
        return watermarked_path, await get_video_metadata(watermarked_path)

    async def _generate_proxy(
        self,
        project_id: str,
        timeline_path: Path,
        request: TimelineCompositionRequest,
        metadata: dict[str, Any],
        source_asset_ids: list[str],
        progress: Optional[ProgressCallback],
    ) -> Optional[VideoAsset]:
        proxy_width, proxy_height = request.proxy_dimensions()
        proxy_path = self._output_path(project_id, "processed", "timeline_proxy", ".mp4")
        await self._progress(progress, 75.0, "Generating proxy preview")
        await self._ffmpeg(
            transcode_video,
            timeline_path,
            proxy_path,
            width=proxy_width,
            height=proxy_height,
            video_bitrate="4M",
            audio_bitrate="128k",
        )
        proxy_metadata = await get_video_metadata(proxy_path)
        proxy_asset = await self._register_asset(
            project_id,
            proxy_path,
            category="proxy",
            source_asset_ids=source_asset_ids,
            label="Timeline Proxy",
            metadata=proxy_metadata,
        )
        return proxy_asset

    async def _generate_exports(
        self,
        project_id: str,
        timeline_path: Path,
        request: TimelineCompositionRequest,
        source_asset_ids: list[str],
        progress: Optional[ProgressCallback],
    ) -> list[VideoAsset]:
        exports: list[VideoAsset] = []
        for index, template in enumerate(request.export_templates):
            export_path = self._output_path(project_id, "exports", self._safe_name(template.name), f".{template.format}")
            await self._progress(progress, 82.0 + (index / max(len(request.export_templates), 1)) * 10.0, f"Exporting {template.name}")

            await self._ffmpeg(
                transcode_video,
                timeline_path,
                export_path,
                width=template.width,
                height=template.height,
                video_codec="libx264" if template.format != "webm" else "libvpx-vp9",
                audio_codec="aac" if template.format != "webm" else "libvorbis",
                video_bitrate=template.video_bitrate,
                audio_bitrate=template.audio_bitrate,
            )

            if template.watermark is not None:
                watermark_path = self._resolve_storage_path(project_id, template.watermark.path)
                final_export_path = self._output_path(project_id, "exports", self._safe_name(f"{template.name}_wm"), f".{template.format}")
                await self._ffmpeg(
                    overlay_watermark,
                    export_path,
                    watermark_path,
                    final_export_path,
                    position=template.watermark.position,
                    scale=template.watermark.scale,
                    opacity=template.watermark.opacity,
                )
                export_path.unlink(missing_ok=True)
                export_path = final_export_path

            export_metadata = await get_video_metadata(export_path)
            export_asset = await self._register_asset(
                project_id,
                export_path,
                category="proxy" if template.proxy else "export",
                source_asset_ids=source_asset_ids,
                label=template.name,
                metadata=export_metadata,
            )
            exports.append(export_asset)
        return exports

    async def _collect_thumbnails(
        self,
        project_id: str,
        request: TimelineCompositionRequest,
        clips: list[ProcessedClip],
        timeline_path: Path,
        progress: Optional[ProgressCallback],
    ) -> list[ThumbnailInfo]:
        thumbnails: list[ThumbnailInfo] = []
        if request.generate_thumbnails:
            await self._progress(progress, 90.0, "Generating keyframe thumbnails")
            timeline_thumbs = await self._ffmpeg(
                generate_keyframe_thumbnails,
                timeline_path,
                self.storage_manager.project_category_path(project_id, "thumbnails"),
                "timeline",
            )
            for idx, thumb in enumerate(timeline_thumbs):
                thumbnails.append(
                    ThumbnailInfo(
                        path=self._relative_path(thumb),
                        clip_index=None,
                        timestamp=float(idx),
                        context="timeline",
                    )
                )

            for clip in clips:
                if clip.thumbnail_path is None:
                    continue
                thumbnails.append(
                    ThumbnailInfo(
                        path=self._relative_path(clip.thumbnail_path),
                        clip_index=request.clips.index(clip.clip),
                        timestamp=clip.metadata.get("duration", 0) / 2 if clip.metadata.get("duration") else 0.0,
                        context="clip",
                    )
                )
        return thumbnails

    async def _register_asset(
        self,
        project_id: str,
        path: Path,
        *,
        category: str,
        source_asset_ids: Iterable[str],
        label: str,
        metadata: dict[str, Any],
    ) -> VideoAsset:
        checksum = self._compute_checksum(path)
        stat_size = path.stat().st_size if path.exists() else metadata.get("size_bytes", 0)
        metadata = dict(metadata)
        metadata.setdefault("label", label)
        metadata.setdefault("aspect_ratio", self._aspect_ratio(metadata))
        now = datetime.utcnow()
        asset = VideoAsset(
            id=str(uuid4()),
            project_id=project_id,
            filename=path.name,
            original_filename=path.name,
            relative_path=self._relative_path(path),
            checksum=checksum,
            size_bytes=stat_size,
            mime_type=self._guess_mime_type(path),
            category=category,
            status="ready",
            source_asset_ids=list(source_asset_ids),
            metadata=metadata,
            created_at=now,
            updated_at=now,
        )
        await self.video_repository.add(asset)
        await self._link_derivative(asset)
        return asset

    async def _link_derivative(self, derivative: VideoAsset) -> None:
        timestamp = datetime.utcnow().isoformat()
        for asset_id in derivative.source_asset_ids:
            asset = await self.video_repository.get(asset_id)
            if asset is None:
                continue
            derivatives = asset.metadata.setdefault("derivatives", [])
            derivatives.append(
                {
                    "asset_id": derivative.id,
                    "category": derivative.category,
                    "path": derivative.relative_path,
                    "created_at": timestamp,
                }
            )
            asset.updated_at = datetime.utcnow()
            await self.video_repository.update(asset)

    async def _ffmpeg(self, func, *args, **kwargs):
        signature = inspect.signature(func)
        if "threads" in signature.parameters and "threads" not in kwargs:
            kwargs["threads"] = self._ffmpeg_threads
        async with self._ffmpeg_semaphore:
            return await func(*args, **kwargs)

    async def _log(self, callback: Optional[LogCallback], message: str, **details: Any) -> None:
        if callback is not None:
            await callback(message, details)
        logger.debug(message, **details)

    async def _progress(self, callback: Optional[ProgressCallback], value: float, message: str) -> None:
        if callback is not None:
            await callback(value, message)
        logger.debug("Progress update", value=value, message=message)

    async def _load_clip_assets(self, clips: Iterable[TimelineClip]) -> dict[str, VideoAsset]:
        assets: dict[str, VideoAsset] = {}
        for clip in clips:
            if clip.asset_id in assets:
                continue
            asset = await self.video_repository.get(clip.asset_id)
            if asset is None:
                raise PipelineError(f"Video asset '{clip.asset_id}' not found in repository")
            assets[clip.asset_id] = asset
        return assets

    def _build_incoming_fade_map(self, clips: list[TimelineClip]) -> dict[int, dict[str, Any]]:
        incoming: dict[int, dict[str, Any]] = {}
        for index, clip in enumerate(clips[:-1]):
            if clip.transition.type == TransitionType.FADE_TO_BLACK:
                incoming[index + 1] = {"duration": clip.transition.duration, "color": "black"}
            elif clip.transition.type == TransitionType.FADE_TO_WHITE:
                incoming[index + 1] = {"duration": clip.transition.duration, "color": "white"}
        return incoming

    def _ducking_to_dict(self, music: BackgroundMusicSpec) -> Optional[dict[str, float]]:
        if music.ducking is None or not music.ducking.enabled:
            return None
        return {
            "enabled": True,
            "threshold": music.ducking.threshold,
            "ratio": music.ducking.ratio,
            "attack": music.ducking.attack,
            "release": music.ducking.release,
        }

    def _resolve_storage_path(self, project_id: str, path_str: str) -> Path:
        relative = Path(path_str)
        if relative.is_absolute() and relative.exists():
            return relative
        absolute = (self.storage_manager.storage_root / relative).resolve()
        if absolute.exists():
            return absolute
        # Attempt within project categories, trying both nested and basename lookups
        for category in ["uploads", "processed", "thumbnails", "exports", "music"]:
            base = self.storage_manager.project_category_path(project_id, category)
            candidate = base / relative
            if candidate.exists():
                return candidate
            if len(relative.parts) > 1:
                name_candidate = base / relative.name
                if name_candidate.exists():
                    return name_candidate
        return absolute

    def _resolve_music_path(self, project_id: str, track: Optional[str]) -> Optional[Path]:
        if not track:
            return None
        candidate = self._resolve_storage_path(project_id, f"music/{track}")
        if candidate.exists():
            return candidate
        candidate = self._resolve_storage_path(project_id, track)
        return candidate if candidate.exists() else None

    def _output_path(self, project_id: str, category: str, prefix: str, suffix: str) -> Path:
        safe_prefix = self._safe_name(prefix)
        suffix = suffix if suffix.startswith(".") else f".{suffix}"
        filename = f"{safe_prefix}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{uuid4().hex[:6]}{suffix}"
        return self.storage_manager.project_category_path(project_id, category) / filename

    def _relative_path(self, path: Path) -> str:
        return str(path.resolve().relative_to(self.storage_manager.storage_root))

    def _compute_checksum(self, path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _guess_mime_type(self, path: Path) -> str:
        ext = path.suffix.lower()
        mapping = {
            ".mp4": "video/mp4",
            ".mov": "video/quicktime",
            ".webm": "video/webm",
        }
        return mapping.get(ext, "video/mp4")

    def _safe_name(self, value: str) -> str:
        return "".join(char if char.isalnum() else "_" for char in value.lower()).strip("_") or "export"

    def _aspect_ratio(self, metadata: dict[str, Any]) -> Optional[str]:
        width = metadata.get("width")
        height = metadata.get("height")
        if not width or not height:
            return None
        gcd = math.gcd(int(width), int(height)) or 1
        return f"{int(width) // gcd}:{int(height) // gcd}"

    def _to_generated_media(self, asset: VideoAsset) -> GeneratedMedia:
        return GeneratedMedia(
            asset_id=asset.id,
            name=asset.metadata.get("label", asset.filename),
            category=asset.category,
            relative_path=asset.relative_path,
            metadata=asset.metadata,
        )
