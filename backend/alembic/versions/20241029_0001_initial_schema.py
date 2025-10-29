from __future__ import annotations

from alembic import op
import sqlalchemy as sa

from backend.app.models.enums import (
    ClipStatus,
    ClipVersionStatus,
    MediaAssetType,
    PresetCategory,
    ProcessingJobStatus,
    ProcessingJobType,
    ProjectStatus,
)

# revision identifiers, used by Alembic.
revision = "20241029_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(ProjectStatus, name="project_status_enum"),
            nullable=False,
            server_default=ProjectStatus.ACTIVE.value,
        ),
        sa.Column("storage_path", sa.String(length=1024), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_projects_id", "projects", ["id"], unique=False)

    op.create_table(
        "presets",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("category", sa.Enum(PresetCategory, name="preset_category_enum"), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("configuration", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key", name="uq_presets_key"),
    )
    op.create_index("ix_presets_id", "presets", ["id"], unique=False)

    op.create_table(
        "media_assets",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("type", sa.Enum(MediaAssetType, name="media_asset_type_enum"), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=1024), nullable=False),
        sa.Column("mime_type", sa.String(length=128), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("checksum", sa.String(length=128), nullable=True),
        sa.Column("analysis_cache", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_media_assets_id", "media_assets", ["id"], unique=False)
    op.create_index("ix_media_assets_project_id", "media_assets", ["project_id"], unique=False)

    op.create_table(
        "clips",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("source_asset_id", sa.String(length=36), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(ClipStatus, name="clip_status_enum"),
            nullable=False,
            server_default=ClipStatus.DRAFT.value,
        ),
        sa.Column("start_time", sa.Float(), nullable=True),
        sa.Column("end_time", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_asset_id"], ["media_assets.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_clips_id", "clips", ["id"], unique=False)
    op.create_index("ix_clips_project_id", "clips", ["project_id"], unique=False)

    op.create_table(
        "clip_versions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("clip_id", sa.String(length=36), nullable=False),
        sa.Column("output_asset_id", sa.String(length=36), nullable=True),
        sa.Column("preset_id", sa.String(length=36), nullable=True),
        sa.Column("version_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "status",
            sa.Enum(ClipVersionStatus, name="clip_version_status_enum"),
            nullable=False,
            server_default=ClipVersionStatus.DRAFT.value,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["clip_id"], ["clips.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["output_asset_id"], ["media_assets.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["preset_id"], ["presets.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("clip_id", "version_number", name="uq_clip_version_number"),
    )
    op.create_index("ix_clip_versions_id", "clip_versions", ["id"], unique=False)
    op.create_index("ix_clip_versions_clip_id", "clip_versions", ["clip_id"], unique=False)

    op.create_table(
        "processing_jobs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("clip_version_id", sa.String(length=36), nullable=True),
        sa.Column("job_type", sa.Enum(ProcessingJobType, name="processing_job_type_enum"), nullable=False),
        sa.Column(
            "status",
            sa.Enum(ProcessingJobStatus, name="processing_job_status_enum"),
            nullable=False,
            server_default=ProcessingJobStatus.PENDING.value,
        ),
        sa.Column("queue_name", sa.String(length=128), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("result_payload", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.String(length=2048), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["clip_version_id"], ["clip_versions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_processing_jobs_id", "processing_jobs", ["id"], unique=False)
    op.create_index("ix_processing_jobs_clip_version_id", "processing_jobs", ["clip_version_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_processing_jobs_clip_version_id", table_name="processing_jobs")
    op.drop_index("ix_processing_jobs_id", table_name="processing_jobs")
    op.drop_table("processing_jobs")

    op.drop_index("ix_clip_versions_clip_id", table_name="clip_versions")
    op.drop_index("ix_clip_versions_id", table_name="clip_versions")
    op.drop_table("clip_versions")

    op.drop_index("ix_clips_project_id", table_name="clips")
    op.drop_index("ix_clips_id", table_name="clips")
    op.drop_table("clips")

    op.drop_index("ix_media_assets_project_id", table_name="media_assets")
    op.drop_index("ix_media_assets_id", table_name="media_assets")
    op.drop_table("media_assets")

    op.drop_index("ix_presets_id", table_name="presets")
    op.drop_table("presets")

    op.drop_index("ix_projects_id", table_name="projects")
    op.drop_table("projects")

    bind = op.get_bind()
    if bind.dialect.name != "sqlite":
        op.execute("DROP TYPE IF EXISTS project_status_enum")
        op.execute("DROP TYPE IF EXISTS preset_category_enum")
        op.execute("DROP TYPE IF EXISTS media_asset_type_enum")
        op.execute("DROP TYPE IF EXISTS clip_status_enum")
        op.execute("DROP TYPE IF EXISTS clip_version_status_enum")
        op.execute("DROP TYPE IF EXISTS processing_job_type_enum")
        op.execute("DROP TYPE IF EXISTS processing_job_status_enum")
