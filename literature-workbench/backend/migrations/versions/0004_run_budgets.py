"""Persist run budget limits and estimates."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("runs") as batch_op:
        batch_op.add_column(
            sa.Column("max_papers", sa.Integer(), nullable=False, server_default="50")
        )
        batch_op.add_column(
            sa.Column(
                "max_external_api_calls", sa.Integer(), nullable=False, server_default="100"
            )
        )
        batch_op.add_column(
            sa.Column("max_cost_usd", sa.Float(), nullable=False, server_default="5.0")
        )
        batch_op.add_column(
            sa.Column("estimated_cost_usd", sa.Float(), nullable=False, server_default="0.0")
        )


def downgrade() -> None:
    with op.batch_alter_table("runs") as batch_op:
        batch_op.drop_column("estimated_cost_usd")
        batch_op.drop_column("max_cost_usd")
        batch_op.drop_column("max_external_api_calls")
        batch_op.drop_column("max_papers")
