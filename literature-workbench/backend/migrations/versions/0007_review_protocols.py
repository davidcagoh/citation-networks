"""Add a reproducible review protocol for each project."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "review_protocols",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("review_mode", sa.String(length=30), nullable=False, server_default="sufficient"),
        sa.Column("research_questions", sa.JSON(), nullable=False),
        sa.Column("inclusion_criteria", sa.JSON(), nullable=False),
        sa.Column("exclusion_criteria", sa.JSON(), nullable=False),
        sa.Column("sources", sa.JSON(), nullable=False),
        sa.Column("cutoff_date", sa.String(length=10), nullable=True),
        sa.Column("update_policy", sa.String(length=30), nullable=False, server_default="on_demand"),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id"),
    )
    op.create_index("ix_review_protocols_project_id", "review_protocols", ["project_id"])


def downgrade() -> None:
    op.drop_index("ix_review_protocols_project_id", table_name="review_protocols")
    op.drop_table("review_protocols")
