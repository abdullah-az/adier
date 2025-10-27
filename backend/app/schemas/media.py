from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from app.models.pipeline import BackgroundMusicSpec


class MusicOption(BaseModel):
    track: str
    path: str
    size_bytes: int


class MusicOptionsResponse(BaseModel):
    items: list[MusicOption]


class MusicSelectionRequest(BaseModel):
    background_music: Optional[BackgroundMusicSpec] = Field(default=None)


class ThumbnailResponse(BaseModel):
    asset_id: str
    path: str
    clip_index: Optional[int] = Field(default=None)
    generated_at: Optional[str] = None
