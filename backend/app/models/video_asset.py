from __future__ import annotations

from datetime import datetime
from typing import Any, Optional, Literal

from pydantic import BaseModel, Field


class VideoAsset(BaseModel):
    """Represents a stored video asset and associated metadata."""

    id: str = Field(..., description="Unique asset identifier")
    project_id: str = Field(..., description="Project the asset belongs to")
    filename: str = Field(..., description="Stored filename")
    original_filename: str = Field(..., description="Original uploaded filename")
    relative_path: str = Field(..., description="Path relative to storage root")
    checksum: str = Field(..., description="SHA-256 checksum of file contents")
    size_bytes: int = Field(..., ge=0, description="File size in bytes")
    mime_type: str = Field(..., description="MIME type of the uploaded file")
    category: Literal["source", "processed", "proxy", "export", "thumbnail", "music"] = Field(
        default="source",
        description="Logical category for the asset within the video pipeline",
    )
    status: str = Field(default="uploaded", description="Processing status of the asset")
    thumbnail_path: Optional[str] = Field(
        default=None,
        description="Relative path to generated thumbnail if available",
    )
    source_asset_ids: list[str] = Field(
        default_factory=list,
        description="Identifiers of source assets used to produce this derivative file",
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional extracted metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
