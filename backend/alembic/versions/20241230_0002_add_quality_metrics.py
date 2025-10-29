from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20241230_0002"
down_revision = "20241029_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "clip_versions",
        sa.Column("quality_metrics", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("clip_versions", "quality_metrics")
