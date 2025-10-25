from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import pytest

from app.core.config import Settings
from app.models.pipeline import BackgroundMusicSpec, TimelineClip, TimelineCompositionRequest
from app.models.video_asset import VideoAsset
from app.repositories.video_repository import VideoAssetRepository
from app.services.video_pipeline_service import VideoPipelineService
from app.utils.storage import StorageManager


@pytest.fixture()
def pipeline_components(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    storage_manager = StorageManager(storage_root=tmp_path)
    video_repository = VideoAssetRepository(storage_root=tmp_path)
    service = VideoPipelineService(
        storage_manager=storage_manager,
        video_repository=video_repository,
        settings=Settings(),
    )

    def _write_dummy(path: Path, content: bytes = b"media") -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    async def _stub_write_output(*_, output_path: Path, content: bytes = b"media", **__):
        _write_dummy(output_path, content)
        return output_path

    async def stub_trim(input_path: Path, output_path: Path, **kwargs):
        return await _stub_write_output(output_path=output_path)

    async def stub_overlay(input_path: Path, watermark_path: Path, output_path: Path, **kwargs):
        return await _stub_write_output(output_path=output_path)

    async def stub_transcode(input_path: Path, output_path: Path, **kwargs):
        return await _stub_write_output(output_path=output_path)

    async def stub_concat(input_paths, output_path: Path):
        return await _stub_write_output(output_path=output_path)

    async def stub_crossfade(first_path: Path, second_path: Path, output_path: Path, **kwargs):
        return await _stub_write_output(output_path=output_path)

    async def stub_mix(video_path: Path, music_path: Path, output_path: Path, **kwargs):
        return await _stub_write_output(output_path=output_path)

    async def stub_burn(input_path: Path, subtitles_path: Path, output_path: Path, **kwargs):
        return await _stub_write_output(output_path=output_path)

    async def stub_fade(input_path: Path, output_path: Path, **kwargs):
        return await _stub_write_output(output_path=output_path)

    async def stub_thumbnail(video_path: Path, thumbnail_path: Path, **kwargs):
        _write_dummy(thumbnail_path, b"thumb")
        return thumbnail_path

    async def stub_keyframes(input_path: Path, output_dir: Path, prefix: str, **kwargs):
        paths = []
        for index in range(2):
            path = output_dir / f"{prefix}_{index:02d}.jpg"
            _write_dummy(path, b"keyframe")
            paths.append(path)
        return paths

    async def stub_metadata(path: Path):
        path = Path(path)
        if not path.exists():
            _write_dummy(path)
        size_bytes = path.stat().st_size
        base_duration = 10.0 if "timeline" in path.name else 5.0
        return {
            "duration": base_duration,
            "width": 1920,
            "height": 1080,
            "codec": "h264",
            "fps": 30.0,
            "bitrate": 5_000_000,
            "size_bytes": size_bytes,
            "has_audio": True,
            "audio_codec": "aac",
            "audio_channels": 2,
            "audio_sample_rate": 48000,
        }

    monkeypatch.setattr("app.services.video_pipeline_service.trim_video", stub_trim)
    monkeypatch.setattr("app.services.video_pipeline_service.overlay_watermark", stub_overlay)
    monkeypatch.setattr("app.services.video_pipeline_service.transcode_video", stub_transcode)
    monkeypatch.setattr("app.services.video_pipeline_service.concat_videos", stub_concat)
    monkeypatch.setattr("app.services.video_pipeline_service.crossfade_videos", stub_crossfade)
    monkeypatch.setattr("app.services.video_pipeline_service.mix_audio_tracks", stub_mix)
    monkeypatch.setattr("app.services.video_pipeline_service.burn_subtitles", stub_burn)
    monkeypatch.setattr("app.services.video_pipeline_service.apply_fade", stub_fade)
    monkeypatch.setattr("app.services.video_pipeline_service.extract_thumbnail", stub_thumbnail)
    monkeypatch.setattr("app.services.video_pipeline_service.generate_keyframe_thumbnails", stub_keyframes)
    monkeypatch.setattr("app.services.video_pipeline_service.get_video_metadata", stub_metadata)

    return storage_manager, video_repository, service


@pytest.mark.asyncio
async def test_compose_timeline_generates_derivatives(pipeline_components):
    storage_manager, repository, service = pipeline_components
    project_id = "demo"

    uploads_dir = storage_manager.project_category_path(project_id, "uploads")
    uploads_dir.mkdir(parents=True, exist_ok=True)
    source_path = uploads_dir / "source.mp4"
    source_bytes = b"source-video"
    source_path.write_bytes(source_bytes)

    checksum = hashlib.sha256(source_bytes).hexdigest()
    source_asset = VideoAsset(
        id="asset-1",
        project_id=project_id,
        filename=source_path.name,
        original_filename="source.mp4",
        relative_path=str(source_path.relative_to(storage_manager.storage_root)),
        checksum=checksum,
        size_bytes=len(source_bytes),
        mime_type="video/mp4",
        category="source",
        status="ready",
        metadata={},
    )
    await repository.add(source_asset)

    music_dir = storage_manager.project_category_path(project_id, "music")
    music_dir.mkdir(parents=True, exist_ok=True)
    (music_dir / "bed.mp3").write_bytes(b"music-bytes")

    request = TimelineCompositionRequest(
        clips=[
            TimelineClip(asset_id=source_asset.id, in_point=0.0, out_point=5.0),
            TimelineClip(asset_id=source_asset.id, in_point=5.0, out_point=10.0),
        ],
        background_music=BackgroundMusicSpec(track="bed.mp3"),
        generate_thumbnails=True,
    )

    logs: list[tuple[str, dict]] = []
    progress_updates: list[tuple[float, str]] = []

    async def log_callback(message: str, details: dict[str, Any]):
        logs.append((message, details))

    async def progress_callback(value: float, message: str):
        progress_updates.append((value, message))

    result = await service.compose_timeline(
        project_id,
        request,
        log=log_callback,
        progress=progress_callback,
    )

    assert result.timeline.category == "processed"
    assert result.proxy is not None
    assert result.exports and len(result.exports) >= 3
    assert result.thumbnails

    assets = await repository.list_by_project(project_id)
    categories = {asset.category for asset in assets}
    assert {"source", "processed", "proxy", "export"}.issubset(categories)

    refreshed_source = await repository.get(source_asset.id)
    assert refreshed_source is not None
    assert refreshed_source.metadata.get("derivatives")
    assert refreshed_source.metadata.get("clip_thumbnails")

    assert logs, "Expected pipeline to emit log callbacks"
    assert progress_updates, "Expected pipeline to emit progress callbacks"
