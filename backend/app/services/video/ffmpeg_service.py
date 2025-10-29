from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from ...core.config import Settings
from ...utils.ffmpeg import parse_ffmpeg_error, temporary_workspace
from ...utils.pathing import normalise_component

_SILENCE_START_RE = re.compile(r"silence_start:\s*(?P<start>-?\d+(?:\.\d+)?)")
_SILENCE_END_RE = re.compile(
    r"silence_end:\s*(?P<end>-?\d+(?:\.\d+)?)(?:\s*\|\s*silence_duration:\s*(?P<duration>-?\d+(?:\.\d+)?))?"
)


class FFmpegCommandError(RuntimeError):
    """Raised when an FFmpeg or FFprobe command fails."""

    def __init__(
        self,
        command: Sequence[str],
        *,
        stderr: str | None = None,
        message: str | None = None,
        returncode: int | None = None,
    ) -> None:
        self.command = list(command)
        self.stderr = stderr or ""
        self.returncode = returncode
        super().__init__(message or parse_ffmpeg_error(self.stderr))


@dataclass(frozen=True)
class VideoMetadata:
    duration: float | None
    fps: float | None
    width: int | None
    height: int | None
    codec: str | None


@dataclass(frozen=True)
class SceneDetectionResult:
    timestamp: float
    score: float


@dataclass(frozen=True)
class SilenceSegment:
    start: float
    end: float
    duration: float


class FFmpegService:
    """Service providing higher level FFmpeg/ffprobe helpers."""

    def __init__(
        self,
        settings: Settings,
        *,
        ffmpeg_path: str | None = None,
        ffprobe_path: str | None = None,
    ) -> None:
        self._settings = settings
        self._ffmpeg = ffmpeg_path or shutil.which("ffmpeg") or "ffmpeg"
        self._ffprobe = ffprobe_path or shutil.which("ffprobe") or "ffprobe"

    # ------------------------------------------------------------------
    # Public API
    def get_video_metadata(self, input_path: Path) -> VideoMetadata:
        command = self.build_probe_command(input_path)
        result = self._run(command, capture_stdout=True, capture_stderr=True)
        payload = json.loads(result.stdout or "{}")

        stream = next(
            (item for item in payload.get("streams", []) if item.get("codec_type") == "video"),
            {},
        )
        format_section = payload.get("format", {})

        duration = self._safe_float(stream.get("duration"))
        if duration is None:
            duration = self._safe_float(format_section.get("duration"))

        fps = self._parse_fraction(stream.get("avg_frame_rate"))
        if fps is None:
            fps = self._parse_fraction(stream.get("r_frame_rate"))

        width = self._safe_int(stream.get("width"))
        height = self._safe_int(stream.get("height"))
        codec = stream.get("codec_name")

        return VideoMetadata(duration=duration, fps=fps, width=width, height=height, codec=codec)

    def detect_scenes(self, input_path: Path, *, threshold: float = 0.4) -> list[SceneDetectionResult]:
        command = self.build_scene_detection_command(input_path, threshold=threshold)
        result = self._run(command, capture_stdout=True, capture_stderr=True)
        payload = json.loads(result.stdout or "{}")

        detections: list[SceneDetectionResult] = []
        for frame in payload.get("frames", []) or []:
            score = self._safe_float(frame.get("tags", {}).get("lavfi.scene_score"))
            if score is None:
                continue
            timestamp = self._safe_float(frame.get("pts_time"))
            if timestamp is None:
                timestamp = self._safe_float(frame.get("pkt_pts_time"), default=0.0)
            detections.append(SceneDetectionResult(timestamp=timestamp or 0.0, score=score))

        detections.sort(key=lambda entry: entry.timestamp)
        return detections

    def detect_silence(
        self,
        input_path: Path,
        *,
        noise_threshold: float | str = -35.0,
        min_duration: float = 0.5,
    ) -> list[SilenceSegment]:
        command = self.build_silence_detection_command(
            input_path,
            noise_threshold=noise_threshold,
            min_duration=min_duration,
        )
        result = self._run(command, capture_stdout=False, capture_stderr=True)
        return self._parse_silence_output(result.stderr or "")

    def extract_audio_waveform(
        self,
        input_path: Path,
        *,
        width: int = 1280,
        height: int = 256,
        color: str = "#3b82f6",
    ) -> Path:
        output_name = f"{normalise_component(input_path.stem)}-waveform.png"
        final_path = self._settings.storage_temp / output_name

        with temporary_workspace(self._settings.storage_temp, prefix="waveform-") as workspace:
            temp_path = workspace / output_name
            command = self.build_waveform_command(
                input_path,
                temp_path,
                width=width,
                height=height,
                color=color,
            )
            self._run(command, capture_stdout=False, capture_stderr=True)
            shutil.move(str(temp_path), str(final_path))

        return final_path

    def extract_audio_track(self, input_path: Path, *, output_format: str = "wav") -> Path:
        suffix = f".{output_format.lstrip('.')}"
        output_name = f"{normalise_component(input_path.stem)}-audio{suffix}"
        final_path = self._settings.storage_temp / output_name

        with temporary_workspace(self._settings.storage_temp, prefix="audio-") as workspace:
            temp_path = workspace / output_name
            command = self.build_audio_extract_command(input_path, temp_path, output_format=output_format)
            self._run(command, capture_stdout=False, capture_stderr=True)
            shutil.move(str(temp_path), str(final_path))

        return final_path

    def generate_thumbnail(
        self,
        input_path: Path,
        *,
        timestamp: float = 0.0,
        width: int = 640,
    ) -> Path:
        output_name = f"{normalise_component(input_path.stem)}-thumbnail.jpg"
        final_path = self._settings.storage_temp / output_name

        with temporary_workspace(self._settings.storage_temp, prefix="thumb-") as workspace:
            temp_path = workspace / output_name
            command = self.build_thumbnail_command(input_path, temp_path, timestamp=timestamp, width=width)
            self._run(command, capture_stdout=False, capture_stderr=True)
            shutil.move(str(temp_path), str(final_path))

        return final_path

    def transcode_to_normalised_mp4(
        self,
        input_path: Path,
        *,
        target_fps: float | None = None,
    ) -> Path:
        output_name = f"{normalise_component(input_path.stem)}-normalized.mp4"
        final_path = self._settings.storage_temp / output_name

        with temporary_workspace(self._settings.storage_temp, prefix="transcode-") as workspace:
            temp_path = workspace / output_name
            command = self.build_transcode_command(
                input_path,
                temp_path,
                target_fps=target_fps,
                use_gpu=True,
            )
            try:
                self._run(command, capture_stdout=False, capture_stderr=True)
            except FFmpegCommandError as exc:
                if self._settings.gpu_enabled:
                    # Retry using CPU when GPU execution fails
                    fallback_command = self.build_transcode_command(
                        input_path,
                        temp_path,
                        target_fps=target_fps,
                        use_gpu=False,
                    )
                    self._run(fallback_command, capture_stdout=False, capture_stderr=True)
                else:
                    raise exc

            shutil.move(str(temp_path), str(final_path))

        return final_path

    # ------------------------------------------------------------------
    # Command builders
    def build_probe_command(self, input_path: Path) -> list[str]:
        return [
            self._ffprobe,
            "-hide_banner",
            "-loglevel",
            "error",
            "-print_format",
            "json",
            "-show_streams",
            "-show_format",
            str(input_path),
        ]

    def build_scene_detection_command(self, input_path: Path, *, threshold: float) -> list[str]:
        safe_threshold = f"{threshold:.6f}".rstrip("0").rstrip(".")
        filter_expr = f"movie={input_path.as_posix()},select=gt(scene\\,{safe_threshold})"
        return [
            self._ffprobe,
            "-hide_banner",
            "-loglevel",
            "error",
            "-print_format",
            "json",
            "-show_frames",
            "-show_entries",
            "frame=pkt_pts_time,pts_time:frame_tags=lavfi.scene_score",
            "-f",
            "lavfi",
            filter_expr,
        ]

    def build_silence_detection_command(
        self,
        input_path: Path,
        *,
        noise_threshold: float | str,
        min_duration: float,
    ) -> list[str]:
        if isinstance(noise_threshold, (float, int)):
            noise_value = f"{noise_threshold}dB"
        else:
            noise_value = str(noise_threshold)

        return [
            self._ffmpeg,
            "-hide_banner",
            "-loglevel",
            "info",
            "-i",
            str(input_path),
            "-af",
            f"silencedetect=noise={noise_value}:d={min_duration}",
            "-f",
            "null",
            "-",
        ]

    def build_waveform_command(
        self,
        input_path: Path,
        output_path: Path,
        *,
        width: int,
        height: int,
        color: str,
    ) -> list[str]:
        return [
            self._ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(input_path),
            "-filter_complex",
            f"aformat=channel_layouts=mono,showwavespic=s={width}x{height}:colors={color}",
            "-frames:v",
            "1",
            str(output_path),
        ]

    def build_audio_extract_command(
        self,
        input_path: Path,
        output_path: Path,
        *,
        output_format: str = "wav",
    ) -> list[str]:
        normalised_format = output_format.lower().lstrip(".")
        command = [
            self._ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(input_path),
            "-vn",
        ]
        if normalised_format == "wav":
            command += ["-ac", "1", "-ar", "44100", "-c:a", "pcm_s16le", str(output_path)]
        elif normalised_format == "mp3":
            command += ["-ac", "2", "-ar", "44100", "-c:a", "libmp3lame", "-b:a", "192k", str(output_path)]
        else:
            command += ["-ac", "2", str(output_path)]
        return command

    def build_thumbnail_command(
        self,
        input_path: Path,
        output_path: Path,
        *,
        timestamp: float,
        width: int,
    ) -> list[str]:
        timestamp_value = f"{timestamp:.3f}".rstrip("0").rstrip(".")
        return [
            self._ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-ss",
            timestamp_value,
            "-i",
            str(input_path),
            "-vframes",
            "1",
            "-vf",
            f"scale={width}:-1",
            "-q:v",
            "2",
            str(output_path),
        ]

    def build_transcode_command(
        self,
        input_path: Path,
        output_path: Path,
        *,
        target_fps: float | None,
        use_gpu: bool,
    ) -> list[str]:
        pre_args, video_codec_args = self._video_encoding_args(use_gpu=use_gpu)

        command = [self._ffmpeg, "-hide_banner", "-loglevel", "error", "-y", *pre_args, "-i", str(input_path)]
        if target_fps is not None:
            command += ["-r", f"{target_fps:g}"]

        command += video_codec_args
        command += ["-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(output_path)]
        return command

    # ------------------------------------------------------------------
    # Internal helpers
    def _video_encoding_args(self, *, use_gpu: bool) -> tuple[list[str], list[str]]:
        if use_gpu and self._settings.gpu_enabled:
            device = (self._settings.gpu_device or "").lower()
            if device.startswith("vaapi"):
                device_path = device.split(":", 1)[1] if ":" in device else "/dev/dri/renderD128"
                pre_args = [
                    "-hwaccel",
                    "vaapi",
                    "-hwaccel_device",
                    device_path,
                    "-hwaccel_output_format",
                    "vaapi",
                ]
                video_args = [
                    "-vf",
                    "format=nv12,hwupload",
                    "-c:v",
                    "h264_vaapi",
                ]
                return pre_args, video_args

            pre_args = ["-hwaccel", "cuda"]
            video_args = ["-c:v", "h264_nvenc", "-preset", "p4", "-pix_fmt", "yuv420p"]
            return pre_args, video_args

        return ([], ["-c:v", "libx264", "-preset", "medium", "-crf", "23", "-pix_fmt", "yuv420p"])

    def _run(
        self,
        command: Sequence[str],
        *,
        capture_stdout: bool,
        capture_stderr: bool,
    ) -> subprocess.CompletedProcess[str]:
        try:
            completed = subprocess.run(  # noqa: S603
                command,
                stdout=subprocess.PIPE if capture_stdout else None,
                stderr=subprocess.PIPE if capture_stderr else None,
                text=True,
                encoding="utf-8",
                check=False,
            )
        except FileNotFoundError as exc:  # pragma: no cover - defensive guard
            raise FFmpegCommandError(command, message=f"Executable not found: {command[0]}") from exc

        if completed.returncode != 0:
            raise FFmpegCommandError(
                command,
                stderr=completed.stderr or "",
                returncode=completed.returncode,
            )

        return completed

    @staticmethod
    def _safe_float(value: object, *, default: float | None = None) -> float | None:
        if value is None:
            return default
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _safe_int(value: object, *, default: int | None = None) -> int | None:
        if value is None:
            return default
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _parse_fraction(value: object) -> float | None:
        if value in (None, "", "N/A"):
            return None
        if isinstance(value, (int, float)):
            try:
                return float(value)
            except (TypeError, ValueError):
                return None
        if isinstance(value, str) and "/" in value:
            numerator, denominator = value.split("/", 1)
            try:
                num = float(numerator)
                den = float(denominator)
                if den == 0:
                    return None
                return num / den
            except (TypeError, ValueError):
                return None
        try:
            return float(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _parse_silence_output(stderr: str) -> list[SilenceSegment]:
        segments: list[SilenceSegment] = []
        current_start: float | None = None

        for raw_line in stderr.splitlines():
            line = raw_line.strip()
            start_match = _SILENCE_START_RE.search(line)
            if start_match:
                current_start = float(start_match.group("start"))
                continue
            end_match = _SILENCE_END_RE.search(line)
            if end_match and current_start is not None:
                end_value = float(end_match.group("end"))
                duration_value = end_match.group("duration")
                duration = float(duration_value) if duration_value is not None else max(0.0, end_value - current_start)
                segments.append(
                    SilenceSegment(
                        start=current_start,
                        end=end_value,
                        duration=duration,
                    )
                )
                current_start = None

        return segments


__all__ = [
    "FFmpegCommandError",
    "FFmpegService",
    "SceneDetectionResult",
    "SilenceSegment",
    "VideoMetadata",
]
