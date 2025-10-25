from enum import StrEnum


class ProjectStatus(StrEnum):
    DRAFT = "draft"
    EDITING = "editing"
    REVIEW = "review"
    COMPLETED = "completed"


class AssetType(StrEnum):
    RAW = "raw"
    BROLL = "broll"
    TRANSITION = "transition"
    AUDIO = "audio"


class SubtitleFormat(StrEnum):
    SRT = "srt"
    VTT = "vtt"
    CUSTOM = "custom"


class AudioTrackType(StrEnum):
    VOICE_OVER = "voice_over"
    MUSIC = "music"
    EFFECTS = "effects"


class ExportJobType(StrEnum):
    VIDEO = "video"
    AUDIO = "audio"
    SUBTITLES = "subtitles"


class ExportJobStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TimelineTrackType(StrEnum):
    VIDEO = "video"
    AUDIO = "audio"
    OVERLAY = "overlay"
