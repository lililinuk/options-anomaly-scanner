"""Represent vendor total-only expiry aggregates without invented side values."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260812_0004"
down_revision: str | None = "20260812_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    for column in ("call_volume", "put_volume", "call_oi", "put_oi"):
        op.alter_column(
            "expiry_observations",
            column,
            existing_type=sa.BigInteger(),
            nullable=True,
        )


def downgrade() -> None:
    for column in ("call_volume", "put_volume", "call_oi", "put_oi"):
        op.execute(
            sa.text(
                f"UPDATE expiry_observations SET {column} = 0 WHERE {column} IS NULL"
            )
        )
        op.alter_column(
            "expiry_observations",
            column,
            existing_type=sa.BigInteger(),
            nullable=False,
        )
