"""Allow usage events for provider calls outside a pipeline run."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("usage_cost_events") as batch_op:
        batch_op.alter_column("run_id", existing_type=sa.String(), nullable=True)
        batch_op.alter_column("stage_run_id", existing_type=sa.String(), nullable=True)


def downgrade() -> None:
    with op.batch_alter_table("usage_cost_events") as batch_op:
        batch_op.alter_column("stage_run_id", existing_type=sa.String(), nullable=False)
        batch_op.alter_column("run_id", existing_type=sa.String(), nullable=False)
