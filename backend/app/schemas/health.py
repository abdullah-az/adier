from datetime import datetime

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime


class ProjectInfoResponse(BaseModel):
    name: str
    version: str
    debug: bool
