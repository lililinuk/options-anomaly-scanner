"""Allow calibrated v1.2 activity to remain unavailable instead of zero."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260812_0007"
down_revision: str | None = "20260812_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "expiry_observations",
        "preliminary_score",
        existing_type=sa.Numeric(8, 3),
        nullable=True,
    )
    op.execute(
        sa.text(
            "UPDATE expiry_observations "
            "SET preliminary_score = NULL "
            "WHERE specification_version = 'signal_spec_v1.2_phase2a' "
            "AND same_day_activity_score IS NULL"
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE expiry_observations SET preliminary_score = 0 "
            "WHERE preliminary_score IS NULL"
        )
    )
    op.alter_column(
        "expiry_observations",
        "preliminary_score",
        existing_type=sa.Numeric(8, 3),
        nullable=False,
    )
