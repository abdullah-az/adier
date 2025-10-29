from __future__ import annotations

from enum import Enum


class ProjectStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class MediaAssetType(str, Enum):
    SOURCE = "source"
    GENERATED = "generated"
    THUMBNAIL = "thumbnail"
    TRANSCRIPT = "transcript"


class ClipStatus(str, Enum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    ARCHIVED = "archived"


class ClipVersionStatus(str, Enum):
    DRAFT = "draft"
    RENDERING = "rendering"
    READY = "ready"
    FAILED = "failed"


class ProcessingJobStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProcessingJobType(str, Enum):
    INGEST = "ingest"
    TRANSCRIBE = "transcribe"
    GENERATE_CLIP = "generate_clip"
    RENDER = "render"
    EXPORT = "export"


class PresetCategory(str, Enum):
    EXPORT = "export"
    STYLE = "style"
    AUDIO = "audio"


__all__ = [
    "ProjectStatus",
    "MediaAssetType",
    "ClipStatus",
    "ClipVersionStatus",
    "ProcessingJobStatus",
    "ProcessingJobType",
    "PresetCategory",
]
