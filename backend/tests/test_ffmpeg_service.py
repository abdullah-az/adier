from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Sequence

import pytest

from backend.app.core.config import TestingSettings
from backend.app.services.video.ffmpeg_service import (
    FFmpegCommandError,
    FFmpegService,
)

pytestmark = pytest.mark.slow


@pytest.fixture(scope="module")
def sample_video_path() -> Path:
    path = Path(__file__).parent / "data" / "sample.mp4"
    if not path.exists():
        pytest.skip("Sample media asset is missing")
    return path


@pytest.fixture(autouse=True)
def ensure_binaries_available() -> None:
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        pytest.skip("FFmpeg binaries are not available in the execution environment")


@pytest.fixture()
def ffmpeg_env(tmp_path: Path) -> tuple[FFmpegService, TestingSettings]:
    settings = TestingSettings(storage_temp=str(tmp_path))
    return FFmpegService(settings), settings


def test_metadata_and_detection(ffmpeg_env: tuple[FFmpegService, TestingSettings], sample_video_path: Path) -> None:
    service, _settings = ffmpeg_env
    metadata = service.get_video_metadata(sample_video_path)
    assert metadata.width == 320
    assert metadata.height == 240
    assert metadata.codec == "h264"
    assert metadata.duration is not None
    assert metadata.duration == pytest.approx(2.0, rel=1e-2)
    assert metadata.fps == pytest.approx(24.0, rel=1e-2)

    scenes = service.detect_scenes(sample_video_path, threshold=0.1)
    assert scenes, "Expected at least one scene boundary to be detected"
    assert scenes[0].timestamp == pytest.approx(1.0, abs=0.05)
    assert scenes[0].score == pytest.approx(0.4, rel=1e-2)

    silences = service.detect_silence(sample_video_path, noise_threshold=-30, min_duration=0.3)
    assert silences
    first = silences[0]
    assert first.start == pytest.approx(0.0, abs=0.05)
    assert first.duration == pytest.approx(1.0, abs=0.05)


def test_transcoding_and_derivatives(
    ffmpeg_env: tuple[FFmpegService, TestingSettings],
    sample_video_path: Path,
) -> None:
    service, settings = ffmpeg_env

    normalised = service.transcode_to_normalised_mp4(sample_video_path)
    assert normalised.exists()
    assert normalised.parent == settings.storage_temp
    assert normalised.suffix == ".mp4"

    waveform = service.extract_audio_waveform(sample_video_path, width=512, height=128)
    assert waveform.exists()
    assert waveform.suffix == ".png"

    audio = service.extract_audio_track(sample_video_path)
    assert audio.exists()
    assert audio.suffix == ".wav"

    thumbnail = service.generate_thumbnail(sample_video_path, timestamp=0.5, width=320)
    assert thumbnail.exists()
    assert thumbnail.suffix == ".jpg"


def test_gpu_flag_and_cpu_fallback(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, sample_video_path: Path) -> None:
    settings = TestingSettings(storage_temp=str(tmp_path), gpu_enabled=True, gpu_device="cuda:0")
    service = FFmpegService(settings)

    gpu_command = service.build_transcode_command(
        sample_video_path,
        tmp_path / "out.mp4",
        target_fps=None,
        use_gpu=True,
    )
    assert "-hwaccel" in gpu_command
    assert "cuda" in gpu_command
    assert "h264_nvenc" in gpu_command

    invoked_commands: list[list[str]] = []

    def fake_run(
        self: FFmpegService,
        command: Sequence[str],
        *,
        capture_stdout: bool,
        capture_stderr: bool,
    ) -> subprocess.CompletedProcess[str]:
        invoked_commands.append(list(command))
        if "h264_nvenc" in command:
            raise FFmpegCommandError(command, stderr="nvenc is not supported")

        output = Path(command[-1])
        output.parent.mkdir(parents=True, exist_ok=True)
        output.touch()
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(FFmpegService, "_run", fake_run, raising=True)

    result = service.transcode_to_normalised_mp4(sample_video_path)
    assert result.exists()
    assert any("h264_nvenc" in cmd for cmd in invoked_commands)
    assert any("libx264" in cmd for cmd in invoked_commands)


def test_gpu_command_cpu_mode_when_disabled(tmp_path: Path, sample_video_path: Path) -> None:
    settings = TestingSettings(storage_temp=str(tmp_path), gpu_enabled=False)
    service = FFmpegService(settings)

    cpu_command = service.build_transcode_command(
        sample_video_path,
        tmp_path / "out.mp4",
        target_fps=30.0,
        use_gpu=True,
    )
    assert "h264_nvenc" not in cpu_command
    assert "libx264" in cpu_command
