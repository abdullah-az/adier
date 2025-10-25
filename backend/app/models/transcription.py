from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class SubtitleSegment(BaseModel):
    """Represents an individual subtitle segment produced by transcription."""

    index: int = Field(ge=0)
    start_seconds: float = Field(ge=0.0)
    end_seconds: float = Field(ge=0.0)
    start_timecode: str
    end_timecode: str
    text: str
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    speaker: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Transcript(BaseModel):
    """Full transcript made up of ordered subtitle segments."""

    id: str
    project_id: str
    asset_id: str
    language: str
    source: str = Field(default="openai-whisper")
    status: str = Field(default="completed")
    segments: list[SubtitleSegment] = Field(default_factory=list)
    full_text: str = Field(default="")
    duration_seconds: Optional[float] = None
    usage: dict[str, int] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {datetime: lambda value: value.isoformat()}
        use_enum_values = True
