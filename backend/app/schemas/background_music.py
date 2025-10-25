from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, constr


class BackgroundMusicBase(BaseModel):
    project_id: int = Field(..., description="Associated project ID")
    name: constr(min_length=1, max_length=255) = Field(..., description="Track name")
    file_path: constr(min_length=1, max_length=512) = Field(..., description="File path")
    duration: Optional[float] = Field(None, ge=0, description="Track duration in seconds")
    bpm: Optional[int] = Field(None, gt=0, description="Track tempo in BPM")
    volume: float = Field(default=0.5, ge=0, le=2, description="Volume multiplier")
    license: Optional[str] = Field(None, max_length=255, description="License information")


class BackgroundMusicCreate(BackgroundMusicBase):
    pass


class BackgroundMusicUpdate(BaseModel):
    name: Optional[constr(min_length=1, max_length=255)] = None
    duration: Optional[float] = Field(None, ge=0)
    bpm: Optional[int] = Field(None, gt=0)
    volume: Optional[float] = Field(None, ge=0, le=2)
    license: Optional[str] = Field(None, max_length=255)


class BackgroundMusicResponse(BackgroundMusicBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
