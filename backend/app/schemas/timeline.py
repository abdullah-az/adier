from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field


class TransitionSchema(BaseModel):
    type: Literal["cut", "crossfade", "fade_to_black", "fade_to_white"] = "cut"
    duration: float = 0.0
    style: Optional[str] = None


class SubtitlesSchema(BaseModel):
    path: str
    encoding: Optional[str] = None
    force_style: Optional[str] = None


class TimelineClipSchema(BaseModel):
    id: str
    asset_id: str
    in_point: float
    out_point: float
    transition: TransitionSchema = Field(default_factory=lambda: TransitionSchema(type="cut"))
    subtitles: Optional[SubtitlesSchema] = None
    include_audio: bool = True
    order: int
    source_type: Literal["ai_scene", "transcript", "manual"] = "manual"
    source_id: Optional[str] = None
    quality_score: Optional[float] = None
    confidence: Optional[float] = None


class BackgroundMusicSchema(BaseModel):
    track: str
    volume: float = 1.0
    offset: float = 0.0
    fade_in: float = 0.0
    fade_out: float = 0.0
    loop: bool = False


class TimelineCreateRequest(BaseModel):
    project_id: str
    name: str
    clips: list[TimelineClipSchema] = Field(default_factory=list)
    aspect_ratio: Literal["16:9", "9:16", "1:1"] = "16:9"
    resolution: Literal["540p", "720p", "1080p"] = "1080p"
    proxy_resolution: Literal["540p", "720p", "1080p"] = "540p"
    background_music: Optional[BackgroundMusicSchema] = None
    global_subtitles: Optional[SubtitlesSchema] = None
    max_duration: Optional[float] = None


class TimelineUpdateRequest(BaseModel):
    name: Optional[str] = None
    clips: Optional[list[TimelineClipSchema]] = None
    aspect_ratio: Optional[Literal["16:9", "9:16", "1:1"]] = None
    resolution: Optional[Literal["540p", "720p", "1080p"]] = None
    proxy_resolution: Optional[Literal["540p", "720p", "1080p"]] = None
    background_music: Optional[BackgroundMusicSchema] = None
    global_subtitles: Optional[SubtitlesSchema] = None
    max_duration: Optional[float] = None


class TimelineResponse(BaseModel):
    id: str
    project_id: str
    name: str
    clips: list[TimelineClipSchema]
    aspect_ratio: str
    resolution: str
    proxy_resolution: str
    background_music: Optional[BackgroundMusicSchema] = None
    global_subtitles: Optional[SubtitlesSchema] = None
    max_duration: Optional[float] = None
    created_at: datetime
    updated_at: datetime


class AISceneResponse(BaseModel):
    id: str
    asset_id: str
    start_time: float
    end_time: float
    confidence: float
    quality_score: float
    scene_type: str
    thumbnail_url: Optional[str] = None
    description: Optional[str] = None
    keywords: list[str] = Field(default_factory=list)


class TranscriptSegmentResponse(BaseModel):
    id: str
    asset_id: str
    start_time: float
    end_time: float
    text: str
    speaker: Optional[str] = None
    confidence: Optional[float] = None


class TranscriptSearchRequest(BaseModel):
    query: str
    asset_ids: Optional[list[str]] = None
    min_duration: Optional[float] = None
    max_duration: Optional[float] = None


class TranscriptSearchResponse(BaseModel):
    segments: list[TranscriptSegmentResponse]
    total_count: int
