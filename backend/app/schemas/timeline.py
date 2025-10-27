from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

from app.models.pipeline import BackgroundMusicSpec, SubtitleSpec, TimelineCompositionRequest
from app.models.project import ClipTiming, TimelineState


class TimelineLayoutItemRequest(BaseModel):
    clip_id: str = Field(..., example="clip-1")
    asset_id: str = Field(..., example="asset-123")
    start: float = Field(..., ge=0.0, example=0.0)
    duration: float = Field(..., gt=0.0, example=5.2)
    in_point: float = Field(default=0.0, ge=0.0, example=1.0)
    out_point: Optional[float] = Field(default=None, ge=0.0, example=6.2)
    include_audio: bool = Field(default=True)
    label: Optional[str] = Field(default=None, example="Hook")
    metadata: dict[str, Any] = Field(default_factory=dict)


class TimelineUpdateRequest(BaseModel):
    locale: Optional[str] = Field(default=None, example="en-US")
    composition: TimelineCompositionRequest
    layout: list[TimelineLayoutItemRequest]
    metadata: dict[str, Any] = Field(default_factory=dict)
    global_subtitles: Optional[SubtitleSpec] = None
    background_music: Optional[BackgroundMusicSpec] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "locale": "en-US",
                "composition": {
                    "clips": [
                        {
                            "asset_id": "asset-123",
                            "in_point": 1.0,
                            "out_point": 6.2,
                            "transition": {"type": "crossfade", "duration": 0.5},
                        },
                        {
                            "asset_id": "asset-456",
                            "in_point": 0.0,
                            "out_point": 5.0,
                            "transition": {"type": "cut"},
                        },
                    ],
                    "background_music": {"track": "upbeat.mp3", "volume": 0.25},
                    "generate_thumbnails": True,
                },
                "layout": [
                    {"clip_id": "clip-1", "asset_id": "asset-123", "start": 0.0, "duration": 5.2, "in_point": 1.0},
                    {"clip_id": "clip-2", "asset_id": "asset-456", "start": 4.7, "duration": 4.8, "in_point": 0.0},
                ],
                "metadata": {"theme": "high-energy"},
            }
        }
    }


class TimelineResponse(BaseModel):
    timeline: TimelineState
    layout: list[ClipTiming]
    total_duration: float
