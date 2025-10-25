from __future__ import annotations

from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, ValidationInfo, field_validator


class AspectRatio(str, Enum):
    """Supported aspect ratios for timeline composition."""

    SIXTEEN_NINE = "16:9"
    NINE_SIXTEEN = "9:16"
    ONE_ONE = "1:1"

    @property
    def width_height(self) -> tuple[int, int]:
        width, height = self.value.split(":")
        return int(width), int(height)

    @property
    def numeric_ratio(self) -> float:
        width, height = self.width_height
        return width / height


class ResolutionPreset(str, Enum):
    """Common resolution presets expressed by their marketing alias."""

    P540 = "540p"
    P720 = "720p"
    P1080 = "1080p"


_RESOLUTION_MAP: dict[ResolutionPreset, dict[AspectRatio, tuple[int, int]]] = {
    ResolutionPreset.P540: {
        AspectRatio.SIXTEEN_NINE: (960, 540),
        AspectRatio.NINE_SIXTEEN: (540, 960),
        AspectRatio.ONE_ONE: (540, 540),
    },
    ResolutionPreset.P720: {
        AspectRatio.SIXTEEN_NINE: (1280, 720),
        AspectRatio.NINE_SIXTEEN: (720, 1280),
        AspectRatio.ONE_ONE: (720, 720),
    },
    ResolutionPreset.P1080: {
        AspectRatio.SIXTEEN_NINE: (1920, 1080),
        AspectRatio.NINE_SIXTEEN: (1080, 1920),
        AspectRatio.ONE_ONE: (1080, 1080),
    },
}


class TransitionType(str, Enum):
    CUT = "cut"
    CROSSFADE = "crossfade"
    FADE_TO_BLACK = "fade_to_black"
    FADE_TO_WHITE = "fade_to_white"


class TransitionSpec(BaseModel):
    """Describe the transition that should occur after the clip."""

    type: TransitionType = Field(default=TransitionType.CUT)
    duration: float = Field(default=0.5, ge=0.0, description="Transition duration in seconds")
    style: str = Field(
        default="fade",
        description="FFmpeg xfade style when using crossfade transitions",
    )

    @property
    def is_crossfade(self) -> bool:
        return self.type == TransitionType.CROSSFADE

    @property
    def is_fade(self) -> bool:
        return self.type in {TransitionType.FADE_TO_BLACK, TransitionType.FADE_TO_WHITE}


class SubtitleSpec(BaseModel):
    path: str = Field(..., description="Absolute or storage-relative path to the subtitle (SRT/VTT)")
    encoding: Optional[str] = Field(default=None, description="Character encoding override")
    force_style: Optional[str] = Field(
        default=None,
        description="Advanced ASS force-style directives passed to FFmpeg",
    )


class WatermarkSpec(BaseModel):
    path: str = Field(..., description="Absolute or storage-relative path to the watermark image/video")
    position: Literal["top-left", "top-right", "bottom-left", "bottom-right"] = Field(
        default="top-right",
        description="Screen position for the watermark overlay",
    )
    scale: float = Field(default=0.12, gt=0.0, lt=1.0, description="Relative size compared to the base video")
    opacity: float = Field(default=1.0, gt=0.0, le=1.0, description="Opacity multiplier for the watermark")


class MusicDuckingSpec(BaseModel):
    enabled: bool = Field(default=True, description="Whether to enable side-chain compression")
    threshold: float = Field(default=0.05, ge=0.0, description="Side-chain compressor threshold")
    ratio: float = Field(default=6.0, ge=1.0, description="Compression ratio when ducking")
    attack: float = Field(default=50.0, ge=0.0, description="Attack in milliseconds")
    release: float = Field(default=300.0, ge=0.0, description="Release in milliseconds")


class BackgroundMusicSpec(BaseModel):
    track: Optional[str] = Field(default=None, description="Filename located within the music library or absolute path")
    volume: float = Field(default=0.25, ge=0.0, le=2.0, description="Linear volume multiplier for the music bed")
    offset: float = Field(default=0.0, ge=0.0, description="Offset in seconds before music starts")
    fade_in: float = Field(default=1.5, ge=0.0, description="Audio fade-in duration for background music")
    fade_out: float = Field(default=1.5, ge=0.0, description="Audio fade-out duration for background music")
    loop: bool = Field(default=True, description="Loop background music to cover entire timeline duration")
    ducking: Optional[MusicDuckingSpec] = Field(default=None, description="Optional ducking configuration")

    @property
    def is_configured(self) -> bool:
        return bool(self.track)


class TimelineClip(BaseModel):
    asset_id: str = Field(..., description="Identifier of the source asset in storage")
    in_point: float = Field(default=0.0, ge=0.0, description="Clip in-point in seconds")
    out_point: Optional[float] = Field(default=None, ge=0.0, description="Clip out-point in seconds; omit to use video duration")
    transition: TransitionSpec = Field(default_factory=TransitionSpec)
    subtitles: Optional[SubtitleSpec] = Field(default=None)
    watermark: Optional[WatermarkSpec] = Field(default=None)
    include_audio: bool = Field(default=True, description="Include the clip's native audio in the mix")

    @property
    def duration(self) -> Optional[float]:
        if self.out_point is None:
            return None
        return max(self.out_point - self.in_point, 0.0)


class ExportTemplate(BaseModel):
    name: str = Field(..., description="Human readable label for the export template")
    format: Literal["mp4", "mov", "webm"] = Field(default="mp4")
    width: int = Field(default=1080, gt=0)
    height: int = Field(default=1920, gt=0)
    aspect_ratio: AspectRatio = Field(default=AspectRatio.NINE_SIXTEEN)
    video_bitrate: Optional[str] = Field(default="8M", description="Optional target video bitrate")
    audio_bitrate: Optional[str] = Field(default="192k", description="Optional target audio bitrate")
    proxy: bool = Field(default=False, description="Mark the export as a lightweight proxy")
    generate_thumbnails: bool = Field(default=True, description="Generate thumbnails for this export output")
    watermark: Optional[WatermarkSpec] = Field(default=None, description="Override watermark to apply for this template")

    @field_validator("aspect_ratio")
    def _validate_aspect_ratio(cls, value: AspectRatio, info: ValidationInfo) -> AspectRatio:
        width = info.data.get("width") if info.data else None
        height = info.data.get("height") if info.data else None
        if width and height:
            computed = round(width / height, 2)
            expected = round(value.numeric_ratio, 2)
            if abs(computed - expected) > 0.05:
                raise ValueError(
                    f"Resolution {width}x{height} does not match aspect ratio {value.value}"
                )
        return value


class TimelineCompositionRequest(BaseModel):
    clips: list[TimelineClip] = Field(..., min_length=1)
    aspect_ratio: AspectRatio = Field(default=AspectRatio.SIXTEEN_NINE)
    resolution: ResolutionPreset = Field(default=ResolutionPreset.P1080)
    proxy_resolution: ResolutionPreset = Field(default=ResolutionPreset.P720)
    background_music: Optional[BackgroundMusicSpec] = Field(default=None)
    export_templates: list[ExportTemplate] = Field(default_factory=list)
    default_watermark: Optional[WatermarkSpec] = Field(default=None)
    global_subtitles: Optional[SubtitleSpec] = Field(default=None, description="Subtitles applied to the combined timeline")
    generate_thumbnails: bool = Field(default=True)

    @field_validator("export_templates", mode="after")
    def _ensure_templates(cls, export_templates: list[ExportTemplate], info: ValidationInfo) -> list[ExportTemplate]:
        if export_templates:
            return export_templates
        aspect_ratio: AspectRatio = (info.data or {}).get("aspect_ratio", AspectRatio.SIXTEEN_NINE)
        width, height = _RESOLUTION_MAP[ResolutionPreset.P1080][aspect_ratio]
        default_specs = [
            ExportTemplate(
                name="YouTube Shorts",
                format="mp4",
                width=width,
                height=height,
                aspect_ratio=aspect_ratio,
                video_bitrate="12M",
            ),
            ExportTemplate(
                name="TikTok",
                format="mp4",
                width=width,
                height=height,
                aspect_ratio=aspect_ratio,
                video_bitrate="10M",
            ),
            ExportTemplate(
                name="Instagram Reels",
                format="mp4",
                width=width,
                height=height,
                aspect_ratio=aspect_ratio,
                video_bitrate="10M",
            ),
        ]
        return default_specs

    def resolution_dimensions(self) -> tuple[int, int]:
        return _RESOLUTION_MAP[self.resolution][self.aspect_ratio]

    def proxy_dimensions(self) -> tuple[int, int]:
        return _RESOLUTION_MAP[self.proxy_resolution][self.aspect_ratio]


class GeneratedMedia(BaseModel):
    asset_id: str
    name: str
    category: str
    relative_path: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class ThumbnailInfo(BaseModel):
    path: str
    clip_index: Optional[int] = None
    timestamp: float = 0.0
    context: Literal["clip", "timeline", "export"] = "clip"


class TimelineCompositionResult(BaseModel):
    timeline: GeneratedMedia
    proxy: Optional[GeneratedMedia] = None
    exports: list[GeneratedMedia] = Field(default_factory=list)
    thumbnails: list[ThumbnailInfo] = Field(default_factory=list)


__all__ = [
    "AspectRatio",
    "ResolutionPreset",
    "TransitionType",
    "TransitionSpec",
    "SubtitleSpec",
    "WatermarkSpec",
    "MusicDuckingSpec",
    "BackgroundMusicSpec",
    "TimelineClip",
    "ExportTemplate",
    "TimelineCompositionRequest",
    "GeneratedMedia",
    "ThumbnailInfo",
    "TimelineCompositionResult",
]
