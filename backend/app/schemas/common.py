from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class PaginationMeta(BaseModel):
    page: int = Field(..., ge=1, example=1)
    page_size: int = Field(..., ge=1, example=20)
    total_items: int = Field(..., ge=0, example=125)
    total_pages: int = Field(..., ge=0, example=7)
    sort: Optional[str] = Field(default=None, example="created_at:desc")
    locale: Optional[str] = Field(default=None, example="en-US")


class AsyncOperationResponse(BaseModel):
    job_id: str = Field(..., example="c7df1f82-49d3-4e29-ae2f-666b3477ac08")
    status: str = Field(..., example="queued")
    message: str = Field(default="Job enqueued successfully")
    metadata: dict[str, Any] = Field(default_factory=dict)
