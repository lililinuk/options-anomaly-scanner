"""Separate Dealer/GEX execution attempts from logical scheduled slots.

Revision ID: 20260815_0013
Revises: 20260814_0012
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260815_0013"
down_revision: str | None = "20260814_0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

RUN_TABLE = "dealer_gex_archive_runs"
OLD_SLOT_CONSTRAINT = "uq_dealer_gex_run_market_date_slot_scope"
SLOT_STATUS_INDEX = "ix_dealer_gex_run_slot_status"


def upgrade() -> None:
    op.drop_constraint(OLD_SLOT_CONSTRAINT, RUN_TABLE, type_="unique")
    op.create_index(
        SLOT_STATUS_INDEX,
        RUN_TABLE,
        ["ny_market_date", "intended_capture_slot", "scope_key", "status"],
    )


def downgrade() -> None:
    op.drop_index(SLOT_STATUS_INDEX, table_name=RUN_TABLE)
    duplicate_slot = op.get_bind().execute(
        sa.text(
            """
            SELECT 1
            FROM dealer_gex_archive_runs
            GROUP BY ny_market_date, intended_capture_slot, scope_key
            HAVING count(*) > 1
            LIMIT 1
            """
        )
    ).first()
    if duplicate_slot is not None:
        raise RuntimeError(
            "Cannot restore the legacy Dealer/GEX slot uniqueness constraint while "
            "append-only retry attempts exist; no historical rows were changed."
        )
    op.create_unique_constraint(
        OLD_SLOT_CONSTRAINT,
        RUN_TABLE,
        ["ny_market_date", "intended_capture_slot", "scope_key"],
    )
