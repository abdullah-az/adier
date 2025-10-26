from __future__ import annotations

import asyncio
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Sequence

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

        audio_stream = next(
            (stream for stream in probe["streams"] if stream["codec_type"] == "audio"), None
        )

        metadata = {
            "duration": float(probe["format"].get("duration", 0)),
            "width": int(video_stream.get("width", 0)),
            "height": int(video_stream.get("height", 0)),
            "codec": video_stream.get("codec_name", "unknown"),
            "fps": _parse_fps(video_stream.get("r_frame_rate", "0/1")),
            "bitrate": int(probe["format"].get("bit_rate", 0)),
            "size_bytes": int(probe["format"].get("size", 0)),
            "has_audio": audio_stream is not None,
        }
        if audio_stream is not None:
            metadata.update(
                {
                    "audio_codec": audio_stream.get("codec_name", "unknown"),
                    "audio_channels": int(audio_stream.get("channels", 0) or 0),
                    "audio_sample_rate": int(float(audio_stream.get("sample_rate", 0) or 0)),
                }
            )

        logger.info("Video metadata extracted", metadata=metadata)
        return metadata

    except Exception as e:
        logger.error("Failed to extract video metadata", error=str(e))
        raise FFmpegError(f"Metadata extraction failed: {e}") from e


async def probe_media_duration(media_path: Path) -> float:
    """Probe a media file and return its duration in seconds."""
    try:
        probe = await asyncio.to_thread(ffmpeg.probe, str(media_path))
        duration_value = probe.get("format", {}).get("duration")
        if duration_value is None:
            return 0.0
        return float(duration_value)
    except Exception as exc:  # pragma: no cover - defensive fallback for missing ffprobe
        logger.warning(
            "Failed to probe media duration",
            path=str(media_path),
            error=str(exc),
        )
        return 0.0


async def extract_audio_track(
    input_path: Path,
    output_path: Path,
    *,
    start: float = 0.0,
    duration: Optional[float] = None,
    sample_rate: int = 16000,
    channels: int = 1,
    codec: str = "pcm_s16le",
    fmt: str = "wav",
) -> Path:
    """Extract the audio track from a media file into a separate file."""
    logger.info(
        "Extracting audio track",
        source=str(input_path),
        destination=str(output_path),
        start=start,
        duration=duration,
    )
    _ensure_parent(output_path)
    input_kwargs: dict[str, float] = {}
    if start and start > 0:
        input_kwargs["ss"] = max(start, 0.0)
    if duration and duration > 0:
        input_kwargs["t"] = max(duration, 0.0)

    stream = ffmpeg.input(str(input_path), **input_kwargs)
    audio = stream.audio
    if audio is None:
        raise FFmpegError("Input media does not contain an audio stream")

    output_kwargs = {
        "ar": sample_rate,
        "ac": channels,
        "format": fmt,
        "acodec": codec,
    }

    result = ffmpeg.output(audio, str(output_path), **output_kwargs)
    await asyncio.to_thread(_run_ffmpeg, result)

    if not output_path.exists():
        raise FFmpegError("Audio extraction failed; output file missing")

    return output_path


def _parse_fps(fps_str: str) -> float:
    """Parse FPS from fraction string like '30000/1001'."""
    try:
        if "/" in fps_str:
            num, den = fps_str.split("/")
            return round(float(num) / float(den), 2)
        return float(fps_str)
    except (ValueError, ZeroDivisionError):
        return 0.0


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _watermark_offsets(position: str) -> tuple[str, str]:
    mapping = {
        "top-left": ("10", "10"),
        "top-right": ("W-w-10", "10"),
        "bottom-left": ("10", "H-h-10"),
        "bottom-right": ("W-w-10", "H-h-10"),
    }
    return mapping.get(position, ("W-w-10", "H-h-10"))


def _format_command(command: Sequence[str]) -> str:
    return " ".join(str(arg) for arg in command)


async def _run_cli(command: Sequence[str]) -> None:
    display = _format_command(command)
    logger.debug("Executing FFmpeg command", command=display)
    process = await asyncio.create_subprocess_exec(
        *[str(arg) for arg in command],
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        err_output = (stderr or b"").decode("utf-8", errors="ignore")
        logger.error("FFmpeg command failed", command=display, stderr=err_output)
        raise FFmpegError(f"FFmpeg command failed: {display}\n{err_output}")
    if stdout:
        logger.trace("FFmpeg stdout", output=stdout.decode("utf-8", errors="ignore"))


async def trim_video(
    input_path: Path,
    output_path: Path,
    *,
    start: float = 0.0,
    end: Optional[float] = None,
    include_audio: bool = True,
    threads: Optional[int] = None,
) -> Path:
    """Trim a clip between start and end timestamps."""
    _ensure_parent(output_path)
    input_kwargs: dict[str, float] = {}
    if start and start > 0:
        input_kwargs["ss"] = max(start, 0)
    if end is not None and end > start:
        input_kwargs["t"] = max(end - start, 0)

    stream = ffmpeg.input(str(input_path), **input_kwargs)
    video = stream.video
    audio = stream.audio if include_audio else None

    output_kwargs = {"vcodec": "libx264", "preset": "medium", "movflags": "+faststart"}
    if threads:
        output_kwargs["threads"] = threads

    if audio is not None:
        output_kwargs["acodec"] = "aac"
        result = ffmpeg.output(video, audio, str(output_path), **output_kwargs)
    else:
        result = ffmpeg.output(video, str(output_path), **output_kwargs)

    await asyncio.to_thread(_run_ffmpeg, result)
    return output_path


async def apply_fade(
    input_path: Path,
    output_path: Path,
    *,
    fade_in: Optional[float] = None,
    fade_out: Optional[float] = None,
    total_duration: Optional[float] = None,
    fade_in_color: str = "black",
    fade_out_color: str = "black",
    threads: Optional[int] = None,
) -> Path:
    """Apply fade in/out effects to video (and audio when present)."""
    _ensure_parent(output_path)
    stream = ffmpeg.input(str(input_path))
    video = stream.video
    audio = stream.audio

    if fade_in and fade_in > 0:
        video = video.filter("fade", type="in", start_time=0, duration=fade_in, color=fade_in_color)
        if audio is not None:
            audio = audio.filter("afade", type="in", start_time=0, duration=fade_in)

    if fade_out and fade_out > 0:
        start_time = max((total_duration or 0.0) - fade_out, 0.0)
        video = video.filter("fade", type="out", start_time=start_time, duration=fade_out, color=fade_out_color)
        if audio is not None:
            audio = audio.filter("afade", type="out", start_time=start_time, duration=fade_out)

    output_kwargs = {"vcodec": "libx264", "preset": "medium", "movflags": "+faststart"}
    if threads:
        output_kwargs["threads"] = threads

    if audio is not None:
        output_kwargs["acodec"] = "aac"
        result = ffmpeg.output(video, audio, str(output_path), **output_kwargs)
    else:
        result = ffmpeg.output(video, str(output_path), **output_kwargs)

    await asyncio.to_thread(_run_ffmpeg, result)
    return output_path


async def concat_videos(input_paths: Sequence[Path], output_path: Path) -> Path:
    """Concatenate multiple videos into a single timeline."""
    if not input_paths:
        raise FFmpegError("No input clips provided for concatenation")
    _ensure_parent(output_path)

    if len(input_paths) == 1:
        shutil.copy(input_paths[0], output_path)
        return output_path

    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as file_list:
        for path in input_paths:
            file_list.write(f"file '{Path(path).as_posix()}'\n")
        list_path = Path(file_list.name)

    command = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(list_path),
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        "-movflags",
        "+faststart",
        str(output_path),
    ]

    try:
        await _run_cli(command)
    finally:
        if list_path.exists():
            list_path.unlink()
    return output_path


async def crossfade_videos(
    first_path: Path,
    second_path: Path,
    output_path: Path,
    *,
    duration: float = 0.5,
    style: str = "fade",
    first_duration: Optional[float] = None,
    threads: Optional[int] = None,
) -> Path:
    """Crossfade between two clips using FFmpeg's xfade filter."""
    _ensure_parent(output_path)
    first = ffmpeg.input(str(first_path))
    second = ffmpeg.input(str(second_path))

    offset = max((first_duration or 0.0) - duration, 0.0)
    video = ffmpeg.filter(
        [first.video, second.video],
        "xfade",
        transition=style,
        duration=duration,
        offset=offset,
    )

    audio = None
    try:
        if first.audio is not None and second.audio is not None:
            audio = ffmpeg.filter([first.audio, second.audio], "acrossfade", d=duration)
    except ffmpeg.Error as error:
        logger.warning("Acrossfade failed; continuing without mixed audio", error=str(error))
        audio = None

    output_kwargs = {"vcodec": "libx264", "preset": "medium", "movflags": "+faststart"}
    if threads:
        output_kwargs["threads"] = threads

    if audio is not None:
        output_kwargs["acodec"] = "aac"
        result = ffmpeg.output(video, audio, str(output_path), **output_kwargs)
    else:
        result = ffmpeg.output(video, str(output_path), **output_kwargs)

    await asyncio.to_thread(_run_ffmpeg, result)
    return output_path


async def burn_subtitles(
    input_path: Path,
    subtitles_path: Path,
    output_path: Path,
    *,
    encoding: Optional[str] = None,
    force_style: Optional[str] = None,
    threads: Optional[int] = None,
) -> Path:
    """Burn subtitles into a video stream."""
    _ensure_parent(output_path)
    stream = ffmpeg.input(str(input_path))
    subtitle_kwargs = {}
    if encoding:
        subtitle_kwargs["charenc"] = encoding
    if force_style:
        subtitle_kwargs["force_style"] = force_style

    video = stream.video.filter("subtitles", str(subtitles_path), **subtitle_kwargs)
    audio = stream.audio

    output_kwargs = {"vcodec": "libx264", "preset": "medium", "movflags": "+faststart"}
    if threads:
        output_kwargs["threads"] = threads

    if audio is not None:
        output_kwargs["acodec"] = "aac"
        result = ffmpeg.output(video, audio, str(output_path), **output_kwargs)
    else:
        result = ffmpeg.output(video, str(output_path), **output_kwargs)

    await asyncio.to_thread(_run_ffmpeg, result)
    return output_path


async def overlay_watermark(
    input_path: Path,
    watermark_path: Path,
    output_path: Path,
    *,
    position: str = "top-right",
    scale: float = 0.12,
    opacity: float = 1.0,
    threads: Optional[int] = None,
) -> Path:
    """Overlay a watermark onto a video."""
    _ensure_parent(output_path)
    base = ffmpeg.input(str(input_path))
    watermark = ffmpeg.input(str(watermark_path))

    scaled_wm, base_video = ffmpeg.filter(
        [watermark, base.video],
        "scale2ref",
        f"iw*{max(scale, 0.01)}",
        f"ih*{max(scale, 0.01)}",
    )

    if opacity < 1.0:
        scaled_wm = scaled_wm.filter("format", "rgba").filter("colorchannelmixer", aa=opacity)

    x_pos, y_pos = _watermark_offsets(position)
    video = ffmpeg.overlay(base_video, scaled_wm, x=x_pos, y=y_pos)
    audio = base.audio

    output_kwargs = {"vcodec": "libx264", "preset": "medium", "movflags": "+faststart"}
    if threads:
        output_kwargs["threads"] = threads

    if audio is not None:
        output_kwargs["acodec"] = "aac"
        result = ffmpeg.output(video, audio, str(output_path), **output_kwargs)
    else:
        result = ffmpeg.output(video, str(output_path), **output_kwargs)

    await asyncio.to_thread(_run_ffmpeg, result)
    return output_path


async def transcode_video(
    input_path: Path,
    output_path: Path,
    *,
    width: int,
    height: int,
    video_bitrate: Optional[str] = None,
    audio_bitrate: Optional[str] = None,
    video_codec: str = "libx264",
    audio_codec: Optional[str] = "aac",
    threads: Optional[int] = None,
) -> Path:
    """Transcode a video to a target resolution and codecs."""
    _ensure_parent(output_path)
    stream = ffmpeg.input(str(input_path))
    video = stream.video.filter(
        "scale",
        width,
        height,
        force_original_aspect_ratio="decrease",
    )
    video = video.filter("pad", width, height, "(ow-iw)/2", "(oh-ih)/2", color="black")

    output_kwargs = {"vcodec": video_codec, "preset": "medium", "movflags": "+faststart"}
    if threads:
        output_kwargs["threads"] = threads
    if video_bitrate:
        output_kwargs["video_bitrate"] = video_bitrate

    audio_stream = stream.audio
    if audio_codec and audio_stream is not None:
        output_kwargs["acodec"] = audio_codec
        if audio_bitrate:
            output_kwargs["audio_bitrate"] = audio_bitrate
        result = ffmpeg.output(video, audio_stream, str(output_path), **output_kwargs)
    else:
        result = ffmpeg.output(video, str(output_path), **output_kwargs)

    await asyncio.to_thread(_run_ffmpeg, result)
    return output_path


async def mix_audio_tracks(
    video_path: Path,
    music_path: Path,
    output_path: Path,
    *,
    music_volume: float = 0.3,
    fade_in: float = 1.5,
    fade_out: float = 1.5,
    duration: Optional[float] = None,
    offset: float = 0.0,
    ducking: Optional[dict[str, float]] = None,
    loop: bool = True,
    base_has_audio: bool = True,
) -> Path:
    """Mix a background music track with a video's audio using FFmpeg filter_complex."""
    _ensure_parent(output_path)

    filter_parts: list[str] = []
    label = "music"
    filter_parts.append(f"[1:a]volume={music_volume}[{label}]")

    if offset and offset > 0:
        delay_ms = int(offset * 1000)
        filter_parts.append(f"[{label}]adelay={delay_ms}|{delay_ms}[{label}d]")
        label = f"{label}d"

    if loop:
        filter_parts.append(f"[{label}]aloop=loop=-1:size=2e9[{label}l]")
        label = f"{label}l"

    if duration:
        filter_parts.append(f"[{label}]atrim=0:{duration}[{label}t]")
        label = f"{label}t"

    if fade_in and fade_in > 0:
        filter_parts.append(f"[{label}]afade=t=in:st=0:d={fade_in}[{label}fi]")
        label = f"{label}fi"

    if fade_out and fade_out > 0 and duration:
        start = max(duration - fade_out, 0)
        filter_parts.append(f"[{label}]afade=t=out:st={start}:d={fade_out}[{label}fo]")
        label = f"{label}fo"

    processed_music = label

    final_audio_label = processed_music
    if base_has_audio:
        if ducking and ducking.get("enabled", True):
            threshold = ducking.get("threshold", 0.05)
            ratio = ducking.get("ratio", 6.0)
            attack = ducking.get("attack", 50.0)
            release = ducking.get("release", 300.0)
            filter_parts.append(
                f"[0:a][{processed_music}]sidechaincompress=threshold={threshold}:ratio={ratio}:attack={attack}:release={release}[ducked]"
            )
            final_audio_label = "ducked"
        else:
            filter_parts.append(
                f"[0:a][{processed_music}]amix=inputs=2:duration=longest:dropout_transition=2[mixed]"
            )
            final_audio_label = "mixed"
    else:
        final_audio_label = processed_music

    filter_complex = ";".join(filter_parts)
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-i",
        str(music_path),
    ]

    if filter_complex:
        command.extend(["-filter_complex", filter_complex])
    command.extend([
        "-map",
        "0:v:0",
    ])
    if final_audio_label:
        command.extend(["-map", f"[{final_audio_label}]"])
    else:
        command.extend(["-map", "0:a:0"])
    command.extend([
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-shortest",
        str(output_path),
    ])

    await _run_cli(command)
    return output_path


async def generate_keyframe_thumbnails(
    input_path: Path,
    output_dir: Path,
    prefix: str,
    *,
    scene_threshold: float = 0.3,
    limit: int = 3,
    width: int = 640,
    height: int = 360,
) -> list[Path]:
    """Generate multiple thumbnails from key frames using FFmpeg filters."""
    output_dir.mkdir(parents=True, exist_ok=True)
    template = output_dir / f"{prefix}_%02d.jpg"
    filter_expr = f"select=gt(scene\\,{scene_threshold}),scale={width}:{height}"

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-vf",
        filter_expr,
        "-frames:v",
        str(limit),
        str(template),
    ]

    await _run_cli(command)
    generated = sorted(output_dir.glob(f"{prefix}_*.jpg"))
    if not generated:
        # Fallback to a simple thumbnail if scene detection yielded nothing
        fallback_path = output_dir / f"{prefix}_fallback.jpg"
        await extract_thumbnail(input_path, fallback_path, timestamp=1.0, width=width, height=height)
        generated = [fallback_path]
    return generated
