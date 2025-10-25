from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, constr

from app.models.enums import AudioTrackType


class AudioTrackBase(BaseModel):
    project_id: int = Field(..., description="Associated project ID")
    video_asset_id: Optional[int] = Field(None, description="Associated video asset ID")
    name: constr(min_length=1, max_length=255) = Field(..., description="Audio track name")
    track_type: AudioTrackType = Field(default=AudioTrackType.VOICE_OVER, description="Type of audio track")
    file_path: constr(min_length=1, max_length=512) = Field(..., description="Audio file path")
    duration: Optional[float] = Field(None, ge=0, description="Audio duration in seconds")
    volume: float = Field(default=1.0, ge=0, le=2, description="Audio volume multiplier")
    sample_rate: Optional[int] = Field(None, gt=0, description="Audio sample rate in Hz")
    channels: Optional[int] = Field(None, gt=0, description="Number of audio channels")
    codec: Optional[str] = Field(None, max_length=50, description="Audio codec")


class AudioTrackCreate(AudioTrackBase):
    pass


class AudioTrackUpdate(BaseModel):
    name: Optional[constr(min_length=1, max_length=255)] = None
    track_type: Optional[AudioTrackType] = None
    duration: Optional[float] = Field(None, ge=0)
    volume: Optional[float] = Field(None, ge=0, le=2)
    sample_rate: Optional[int] = Field(None, gt=0)
    channels: Optional[int] = Field(None, gt=0)
    codec: Optional[str] = Field(None, max_length=50)


class AudioTrackResponse(AudioTrackBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
