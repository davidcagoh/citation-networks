"""Persist directional citation-network edges."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "citation_edges",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("source_paper_id", sa.String(), nullable=False),
        sa.Column("target_paper_id", sa.String(), nullable=False),
        sa.Column("direction", sa.String(length=20), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False, server_default="manual"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_paper_id"], ["papers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_paper_id"], ["papers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_citation_edges_project_id", "citation_edges", ["project_id"])
    op.create_index("ix_citation_edges_source_paper_id", "citation_edges", ["source_paper_id"])
    op.create_index("ix_citation_edges_target_paper_id", "citation_edges", ["target_paper_id"])


def downgrade() -> None:
    op.drop_index("ix_citation_edges_target_paper_id", table_name="citation_edges")
    op.drop_index("ix_citation_edges_source_paper_id", table_name="citation_edges")
    op.drop_index("ix_citation_edges_project_id", table_name="citation_edges")
    op.drop_table("citation_edges")
