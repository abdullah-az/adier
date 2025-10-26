"""Initial database schema

Revision ID: 202410270001
Revises: 
Create Date: 2024-10-27 00:00:00

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "202410270001"
down_revision = None
branch_labels = None
depends_on = None


video_asset_type_enum = sa.Enum(
    "source",
    "proxy",
    "audio",
    "image",
    "export",
    name="video_asset_type",
    native_enum=False,
)

video_asset_status_enum = sa.Enum(
    "uploaded",
    "processing",
    "ready",
    "failed",
    name="video_asset_status",
    native_enum=False,
)

export_format_enum = sa.Enum(
    "mp4",
    "mov",
    "mkv",
    "gif",
    "wav",
    name="export_format",
    native_enum=False,
)

job_status_code_enum = sa.Enum(
    "queued",
    "running",
    "completed",
    "failed",
    "cancelled",
    name="job_status_code",
    native_enum=False,
)


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("frame_rate", sa.Float(), nullable=False, server_default=sa.text("24.0")),
        sa.Column("resolution_width", sa.Integer(), nullable=False, server_default=sa.text("1920")),
        sa.Column("resolution_height", sa.Integer(), nullable=False, server_default=sa.text("1080")),
        sa.Column("duration_seconds", sa.Float(), nullable=False, server_default=sa.text("0.0")),
        sa.Column("thumbnail_path", sa.String(length=512), nullable=True),
        sa.Column("color_profile", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("slug", name="uq_projects_slug"),
        sa.CheckConstraint("frame_rate > 0", name="ck_projects_frame_rate_positive"),
        sa.CheckConstraint("resolution_width > 0", name="ck_projects_resolution_width_positive"),
        sa.CheckConstraint("resolution_height > 0", name="ck_projects_resolution_height_positive"),
        sa.CheckConstraint("duration_seconds >= 0", name="ck_projects_duration_non_negative"),
    )

    op.create_table(
        "video_assets",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("project_id", sa.String(length=36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("relative_path", sa.String(length=512), nullable=False),
        sa.Column("mime_type", sa.String(length=128), nullable=False),
        sa.Column("checksum", sa.String(length=128), nullable=False, unique=True),
        sa.Column("file_size", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("duration_seconds", sa.Float(), nullable=False, server_default=sa.text("0.0")),
        sa.Column("frame_rate", sa.Float(), nullable=False, server_default=sa.text("24.0")),
        sa.Column("resolution_width", sa.Integer(), nullable=False, server_default=sa.text("1920")),
        sa.Column("resolution_height", sa.Integer(), nullable=False, server_default=sa.text("1080")),
        sa.Column("waveform_path", sa.String(length=512), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("asset_type", video_asset_type_enum, nullable=False, server_default=sa.text("'source'")),
        sa.Column("status", video_asset_status_enum, nullable=False, server_default=sa.text("'uploaded'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("duration_seconds >= 0", name="ck_video_assets_duration_non_negative"),
        sa.CheckConstraint("frame_rate > 0", name="ck_video_assets_frame_rate_positive"),
        sa.CheckConstraint("file_size >= 0", name="ck_video_assets_file_size_non_negative"),
        sa.CheckConstraint("resolution_width > 0", name="ck_video_assets_resolution_width_positive"),
        sa.CheckConstraint("resolution_height > 0", name="ck_video_assets_resolution_height_positive"),
    )
    op.create_index("ix_video_assets_project_id", "video_assets", ["project_id"])

    op.create_table(
        "scene_detections",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("project_id", sa.String(length=36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("video_asset_id", sa.String(length=36), sa.ForeignKey("video_assets.id", ondelete="CASCADE"), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=True),
        sa.Column("start_time", sa.Float(), nullable=False),
        sa.Column("end_time", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("end_time > start_time", name="ck_scene_detections_valid_scene_duration"),
        sa.CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="ck_scene_detections_confidence_range",
        ),
    )
    op.create_index("ix_scene_detections_project_id", "scene_detections", ["project_id"])
    op.create_index("ix_scene_detections_video_asset_id", "scene_detections", ["video_asset_id"])

    op.create_table(
        "subtitle_segments",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("project_id", sa.String(length=36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("video_asset_id", sa.String(length=36), sa.ForeignKey("video_assets.id", ondelete="SET NULL"), nullable=True),
        sa.Column("language", sa.String(length=16), nullable=False, server_default=sa.text("'en'")),
        sa.Column("speaker", sa.String(length=128), nullable=True),
        sa.Column("start_time", sa.Float(), nullable=False),
        sa.Column("end_time", sa.Float(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("is_approved", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("end_time > start_time", name="ck_subtitle_segments_valid_subtitle_duration"),
    )
    op.create_index("ix_subtitle_segments_project_id", "subtitle_segments", ["project_id"])
    op.create_index("ix_subtitle_segments_video_asset_id", "subtitle_segments", ["video_asset_id"])

    op.create_table(
        "timeline_clips",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("project_id", sa.String(length=36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("video_asset_id", sa.String(length=36), sa.ForeignKey("video_assets.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("track_index", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("sequence_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("start_time", sa.Float(), nullable=False),
        sa.Column("end_time", sa.Float(), nullable=False),
        sa.Column("clip_start", sa.Float(), nullable=False),
        sa.Column("clip_end", sa.Float(), nullable=False),
        sa.Column("speed", sa.Float(), nullable=False, server_default=sa.text("1.0")),
        sa.Column("is_locked", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("transition_in", sa.String(length=64), nullable=True),
        sa.Column("transition_out", sa.String(length=64), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("end_time > start_time", name="ck_timeline_clips_valid_clip_duration"),
        sa.CheckConstraint("clip_end > clip_start", name="ck_timeline_clips_valid_clip_range"),
        sa.CheckConstraint("speed > 0", name="ck_timeline_clips_positive_speed"),
        sa.CheckConstraint("track_index >= 0", name="ck_timeline_clips_non_negative_track_index"),
        sa.CheckConstraint("sequence_order >= 0", name="ck_timeline_clips_non_negative_sequence_order"),
    )
    op.create_index("ix_timeline_clips_project_id", "timeline_clips", ["project_id"])
    op.create_index("ix_timeline_clips_video_asset_id", "timeline_clips", ["video_asset_id"])

    op.create_table(
        "audio_tracks",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("project_id", sa.String(length=36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("video_asset_id", sa.String(length=36), sa.ForeignKey("video_assets.id", ondelete="SET NULL"), nullable=True),
        sa.Column("timeline_clip_id", sa.String(length=36), sa.ForeignKey("timeline_clips.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("start_time", sa.Float(), nullable=False),
        sa.Column("end_time", sa.Float(), nullable=False),
        sa.Column("fade_in", sa.Float(), nullable=False, server_default=sa.text("0.0")),
        sa.Column("fade_out", sa.Float(), nullable=False, server_default=sa.text("0.0")),
        sa.Column("volume", sa.Float(), nullable=False, server_default=sa.text("1.0")),
        sa.Column("pan", sa.Float(), nullable=False, server_default=sa.text("0.0")),
        sa.Column("is_muted", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("end_time > start_time", name="ck_audio_tracks_valid_audio_duration"),
        sa.CheckConstraint("fade_in >= 0", name="ck_audio_tracks_non_negative_fade_in"),
        sa.CheckConstraint("fade_out >= 0", name="ck_audio_tracks_non_negative_fade_out"),
        sa.CheckConstraint("volume >= 0 AND volume <= 2", name="ck_audio_tracks_volume_range"),
        sa.CheckConstraint("pan >= -1 AND pan <= 1", name="ck_audio_tracks_pan_range"),
    )
    op.create_index("ix_audio_tracks_project_id", "audio_tracks", ["project_id"])
    op.create_index("ix_audio_tracks_video_asset_id", "audio_tracks", ["video_asset_id"])
    op.create_index("ix_audio_tracks_timeline_clip_id", "audio_tracks", ["timeline_clip_id"])

    op.create_table(
        "job_statuses",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("code", job_status_code_enum, nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.UniqueConstraint("code", name="uq_job_statuses_code"),
    )

    op.create_table(
        "export_jobs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("project_id", sa.String(length=36), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("output_asset_id", sa.String(length=36), sa.ForeignKey("video_assets.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status_id", sa.Integer(), sa.ForeignKey("job_statuses.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("format", export_format_enum, nullable=False),
        sa.Column("preset", sa.String(length=64), nullable=True),
        sa.Column("resolution_width", sa.Integer(), nullable=False, server_default=sa.text("1920")),
        sa.Column("resolution_height", sa.Integer(), nullable=False, server_default=sa.text("1080")),
        sa.Column("frame_rate", sa.Float(), nullable=False, server_default=sa.text("24.0")),
        sa.Column("progress", sa.Float(), nullable=False, server_default=sa.text("0.0")),
        sa.Column("output_path", sa.String(length=512), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("resolution_width > 0", name="ck_export_jobs_resolution_width_positive"),
        sa.CheckConstraint("resolution_height > 0", name="ck_export_jobs_resolution_height_positive"),
        sa.CheckConstraint("frame_rate > 0", name="ck_export_jobs_frame_rate_positive"),
        sa.CheckConstraint("progress >= 0 AND progress <= 100", name="ck_export_jobs_progress_range"),
    )
    op.create_index("ix_export_jobs_project_id", "export_jobs", ["project_id"])
    op.create_index("ix_export_jobs_output_asset_id", "export_jobs", ["output_asset_id"])
    op.create_index("ix_export_jobs_status_id", "export_jobs", ["status_id"])

    job_status_table = sa.table(
        "job_statuses",
        sa.column("code", sa.String(length=50)),
        sa.column("description", sa.String(length=255)),
    )
    op.bulk_insert(
        job_status_table,
        [
            {"code": "queued", "description": "Job is queued"},
            {"code": "running", "description": "Job is currently running"},
            {"code": "completed", "description": "Job finished successfully"},
            {"code": "failed", "description": "Job failed"},
            {"code": "cancelled", "description": "Job was cancelled"},
        ],
    )


def downgrade() -> None:
    op.drop_index("ix_export_jobs_status_id", table_name="export_jobs")
    op.drop_index("ix_export_jobs_output_asset_id", table_name="export_jobs")
    op.drop_index("ix_export_jobs_project_id", table_name="export_jobs")
    op.drop_table("export_jobs")

    op.drop_table("job_statuses")

    op.drop_index("ix_audio_tracks_timeline_clip_id", table_name="audio_tracks")
    op.drop_index("ix_audio_tracks_video_asset_id", table_name="audio_tracks")
    op.drop_index("ix_audio_tracks_project_id", table_name="audio_tracks")
    op.drop_table("audio_tracks")

    op.drop_index("ix_timeline_clips_video_asset_id", table_name="timeline_clips")
    op.drop_index("ix_timeline_clips_project_id", table_name="timeline_clips")
    op.drop_table("timeline_clips")

    op.drop_index("ix_subtitle_segments_video_asset_id", table_name="subtitle_segments")
    op.drop_index("ix_subtitle_segments_project_id", table_name="subtitle_segments")
    op.drop_table("subtitle_segments")

    op.drop_index("ix_scene_detections_video_asset_id", table_name="scene_detections")
    op.drop_index("ix_scene_detections_project_id", table_name="scene_detections")
    op.drop_table("scene_detections")

    op.drop_index("ix_video_assets_project_id", table_name="video_assets")
    op.drop_table("video_assets")

    op.drop_table("projects")

    video_asset_type_enum.drop(op.get_bind(), checkfirst=True)
    video_asset_status_enum.drop(op.get_bind(), checkfirst=True)
    export_format_enum.drop(op.get_bind(), checkfirst=True)
    job_status_code_enum.drop(op.get_bind(), checkfirst=True)
