"""Record explicit approval for paid scholarly providers."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "provider_approvals",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("approved", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("approved_by", sa.String(length=200), nullable=False),
        sa.Column("justification", sa.Text(), nullable=False),
        sa.Column("non_replicable_reason", sa.Text(), nullable=False),
        sa.Column("approved_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "provider"),
    )
    op.create_index("ix_provider_approvals_project_id", "provider_approvals", ["project_id"])


def downgrade() -> None:
    op.drop_index("ix_provider_approvals_project_id", table_name="provider_approvals")
    op.drop_table("provider_approvals")
