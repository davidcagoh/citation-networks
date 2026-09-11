"""Persist the review contract selected for each brief and run."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("research_briefs") as batch_op:
        batch_op.add_column(
            sa.Column("review_mode", sa.String(length=30), nullable=False, server_default="sufficient")
        )
    with op.batch_alter_table("runs") as batch_op:
        batch_op.add_column(
            sa.Column("review_mode", sa.String(length=30), nullable=False, server_default="sufficient")
        )


def downgrade() -> None:
    with op.batch_alter_table("runs") as batch_op:
        batch_op.drop_column("review_mode")
    with op.batch_alter_table("research_briefs") as batch_op:
        batch_op.drop_column("review_mode")
