"""Add plan metadata column to clip versions.

Revision ID: 20241030_0002
Revises: 20241029_0001
Create Date: 2024-10-30 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20241030_0002"
down_revision = "20241029_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("clip_versions", sa.Column("plan_metadata", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("clip_versions", "plan_metadata")
