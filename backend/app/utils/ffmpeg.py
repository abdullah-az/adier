from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

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
