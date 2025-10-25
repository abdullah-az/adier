from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class SceneDetectionBase(BaseModel):
    project_id: int = Field(..., description="Associated project ID")
    video_asset_id: Optional[int] = Field(None, description="Associated video asset ID")
    start_time: float = Field(..., ge=0, description="Scene start time in seconds")
    end_time: float = Field(..., gt=0, description="Scene end time in seconds")
    confidence: Optional[float] = Field(None, ge=0, le=1, description="Detection confidence score")
    scene_type: Optional[str] = Field(None, max_length=50, description="Scene classification")
    description: Optional[str] = Field(None, description="Scene description")
    thumbnail_path: Optional[str] = Field(None, max_length=512, description="Thumbnail path for the scene")


class SceneDetectionCreate(SceneDetectionBase):
    pass


class SceneDetectionUpdate(BaseModel):
    start_time: Optional[float] = Field(None, ge=0)
    end_time: Optional[float] = Field(None, gt=0)
    confidence: Optional[float] = Field(None, ge=0, le=1)
    scene_type: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    thumbnail_path: Optional[str] = Field(None, max_length=512)


class SceneDetectionResponse(SceneDetectionBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
