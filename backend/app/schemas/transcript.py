from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field

from app.models.transcription import SubtitleSegment, Transcript


class SubtitleSegmentResponse(BaseModel):
    index: int
    start_seconds: float
    end_seconds: float
    start_timecode: str
    end_timecode: str
    text: str
    confidence: Optional[float] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_model(cls, segment: SubtitleSegment) -> "SubtitleSegmentResponse":
        return cls(**segment.model_dump())


class TranscriptResponse(BaseModel):
    transcript_id: str = Field(alias="id")
    project_id: str
    asset_id: str
    language: str
    source: str
    status: str
    segments: List[SubtitleSegmentResponse]
    full_text: str
    duration_seconds: Optional[float] = None
    usage: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, transcript: Transcript) -> "TranscriptResponse":
        return cls(
            id=transcript.id,
            project_id=transcript.project_id,
            asset_id=transcript.asset_id,
            language=transcript.language,
            source=transcript.source,
            status=transcript.status,
            segments=[SubtitleSegmentResponse.from_model(segment) for segment in transcript.segments],
            full_text=transcript.full_text,
            duration_seconds=transcript.duration_seconds,
            usage=transcript.usage,
            metadata=transcript.metadata,
            created_at=transcript.created_at,
            updated_at=transcript.updated_at,
        )
