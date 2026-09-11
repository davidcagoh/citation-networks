"""Add discovery provenance and corpus screening support."""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "discovery_events",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("paper_id", sa.String(), nullable=True),
        sa.Column("route", sa.String(length=80), nullable=False),
        sa.Column("query", sa.String(length=500), nullable=True),
        sa.Column("action", sa.String(length=30), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=True),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["paper_id"], ["papers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_discovery_events_project_id", "discovery_events", ["project_id"])
    op.create_index("ix_discovery_events_paper_id", "discovery_events", ["paper_id"])


def downgrade() -> None:
    op.drop_table("discovery_events")
