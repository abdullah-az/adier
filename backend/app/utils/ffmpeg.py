from __future__ import annotations

import asyncio
from pathlib import Path
from typing import List, Optional

import ffmpeg
from loguru import logger


class FFmpegError(Exception):
    """Custom exception for FFmpeg operations."""

    pass


async def extract_thumbnail(
    video_path: Path,
    output_path: Path,
    timestamp: float = 1.0,
    width: int = 640,
    height: int = 360,
) -> Path:
    """
    Extract a thumbnail from a video file.
    
    Args:
        video_path: Path to video file
        output_path: Path where thumbnail should be saved
        timestamp: Time in seconds to extract frame from
        width: Thumbnail width
        height: Thumbnail height
        
    Returns:
        Path to generated thumbnail
        
    Raises:
        FFmpegError: If thumbnail extraction fails
    """
    logger.info(
        "Extracting thumbnail",
        video=str(video_path),
        output=str(output_path),
        timestamp=timestamp,
    )

    try:
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Build FFmpeg command
        stream = ffmpeg.input(str(video_path), ss=timestamp)
        stream = ffmpeg.filter(stream, "scale", width, height)
        stream = ffmpeg.output(stream, str(output_path), vframes=1, format="image2")

        # Run command asynchronously
        await asyncio.to_thread(_run_ffmpeg, stream)

        if not output_path.exists():
            raise FFmpegError("Thumbnail file was not created")

        logger.info("Thumbnail extracted successfully", output=str(output_path))
        return output_path

    except Exception as e:
        logger.error("Failed to extract thumbnail", error=str(e))
        raise FFmpegError(f"Thumbnail extraction failed: {e}") from e


def _select_audio_codec(audio_format: str) -> str:
    if audio_format.lower() in {"wav", "wave"}:
        return "pcm_s16le"
    if audio_format.lower() == "mp3":
        return "libmp3lame"
    if audio_format.lower() in {"m4a", "aac"}:
        return "aac"
    return "pcm_s16le"


async def extract_audio_track(
    video_path: Path,
    output_path: Path,
    *,
    sample_rate: int = 16000,
    channels: int = 1,
    audio_format: str = "wav",
    audio_codec: Optional[str] = None,
) -> Path:
    """Extract the audio track from a video file into a standalone audio file."""
    codec = audio_codec or _select_audio_codec(audio_format)
    logger.info(
        "Extracting audio track",
        video=str(video_path),
        output=str(output_path),
        sample_rate=sample_rate,
        channels=channels,
        format=audio_format,
        codec=codec,
    )

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        stream = (
            ffmpeg.input(str(video_path))
            .output(
                str(output_path),
                format=audio_format,
                ac=channels,
                ar=sample_rate,
                acodec=codec,
            )
        )
        await asyncio.to_thread(_run_ffmpeg, stream)
        if not output_path.exists():
            raise FFmpegError("Audio extraction failed: file not created")
        return output_path
    except Exception as exc:  # pragma: no cover - relies on ffmpeg installation
        logger.error("Failed to extract audio", error=str(exc))
        raise FFmpegError(f"Audio extraction failed: {exc}") from exc


async def split_audio_into_chunks(
    audio_path: Path,
    output_dir: Path,
    *,
    chunk_duration: float,
    prefix: str = "chunk",
) -> List[Path]:
    """Split an audio file into smaller chunks using ffmpeg segment muxer."""
    if chunk_duration <= 0:
        raise ValueError("chunk_duration must be greater than zero")

    logger.info(
        "Splitting audio into chunks",
        audio=str(audio_path),
        output_dir=str(output_dir),
        segment_seconds=chunk_duration,
    )

    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        for existing in output_dir.glob(f"{prefix}_*{audio_path.suffix}"):
            existing.unlink(missing_ok=True)

        pattern = output_dir / f"{prefix}_%03d{audio_path.suffix}"
        stream = ffmpeg.input(str(audio_path)).output(
            str(pattern),
            f="segment",
            segment_time=chunk_duration,
            reset_timestamps=1,
            c="copy",
        )
        await asyncio.to_thread(_run_ffmpeg, stream)

        chunks = sorted(output_dir.glob(f"{prefix}_*{audio_path.suffix}"))
        if not chunks:
            logger.debug("Segmentation produced no chunks; returning original audio")
            return [audio_path]
        logger.info("Generated audio chunks", count=len(chunks))
        return chunks
    except Exception as exc:  # pragma: no cover - depends on ffmpeg binary
        logger.error("Failed to segment audio", error=str(exc))
        raise FFmpegError(f"Audio segmentation failed: {exc}") from exc


async def get_media_duration(media_path: Path) -> float:
    """Return the duration in seconds for a media file using ffprobe."""
    try:
        probe = await asyncio.to_thread(ffmpeg.probe, str(media_path))
        duration = float(probe.get("format", {}).get("duration", 0.0))
        return duration
    except Exception as exc:  # pragma: no cover - depends on ffmpeg availability
        logger.error("Failed to probe media duration", path=str(media_path), error=str(exc))
        raise FFmpegError(f"Unable to determine media duration: {exc}") from exc


def _run_ffmpeg(stream) -> None:
    """Helper to run ffmpeg command with error handling."""
    try:
        stream.run(capture_stdout=True, capture_stderr=True, overwrite_output=True)
    except ffmpeg.Error as e:
        stderr = e.stderr.decode() if e.stderr else ""
        raise FFmpegError(f"FFmpeg command failed: {stderr}") from e


async def get_video_metadata(video_path: Path) -> dict:
    """
    Extract metadata from video file.
    
    Args:
        video_path: Path to video file
        
    Returns:
        Dictionary containing video metadata
        
    Raises:
        FFmpegError: If metadata extraction fails
    """
    logger.info("Extracting video metadata", video=str(video_path))

    try:
        probe = await asyncio.to_thread(ffmpeg.probe, str(video_path))

        video_stream = next(
            (stream for stream in probe["streams"] if stream["codec_type"] == "video"), None
        )

        if not video_stream:
            raise FFmpegError("No video stream found")

        metadata = {
            "duration": float(probe["format"].get("duration", 0)),
            "width": int(video_stream.get("width", 0)),
            "height": int(video_stream.get("height", 0)),
            "codec": video_stream.get("codec_name", "unknown"),
            "fps": _parse_fps(video_stream.get("r_frame_rate", "0/1")),
            "bitrate": int(probe["format"].get("bit_rate", 0)),
            "size_bytes": int(probe["format"].get("size", 0)),
        }

        logger.info("Video metadata extracted", metadata=metadata)
        return metadata

    except Exception as e:
        logger.error("Failed to extract video metadata", error=str(e))
        raise FFmpegError(f"Metadata extraction failed: {e}") from e


def _parse_fps(fps_str: str) -> float:
    """Parse FPS from fraction string like '30000/1001'."""
    try:
        if "/" in fps_str:
            num, den = fps_str.split("/")
            return round(float(num) / float(den), 2)
        return float(fps_str)
    except (ValueError, ZeroDivisionError):
        return 0.0
