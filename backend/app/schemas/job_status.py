from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.db.models import JobStatusCode


class JobStatusBase(BaseModel):
    code: JobStatusCode
    description: Optional[str] = Field(default=None, max_length=255)


class JobStatusCreate(JobStatusBase):
    pass


class JobStatusUpdate(BaseModel):
    description: Optional[str] = Field(default=None, max_length=255)


class JobStatusRead(JobStatusBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
