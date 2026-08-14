from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.time import ensure_utc
from app.db.models import (
    DealerGexArchiveRun,
    DealerGexSnapshot,
    DealerGexSnapshotCell,
    RawVendorPayload,
)
from app.dealer_archive.config import (
    DEALER_GEX_CAPABILITY,
    DEALER_GEX_SURFACE_SCHEMA_VERSION,
    DealerGexArchiveConfig,
)
from app.dealer_archive.domain import NormalizedDealerGexSurface


def existing_archive_run(
    session: Session,
    *,
    market_date: Any,
    intended_capture_slot: str,
    scope_key: str,
) -> DealerGexArchiveRun | None:
    return session.scalar(
        select(DealerGexArchiveRun).where(
            DealerGexArchiveRun.ny_market_date == market_date,
            DealerGexArchiveRun.intended_capture_slot == intended_capture_slot,
            DealerGexArchiveRun.scope_key == scope_key,
        )
    )


def persist_surface(
    session: Session,
    *,
    run: DealerGexArchiveRun,
    surface: NormalizedDealerGexSurface,
    captured_at: datetime,
    endpoint: str,
    source_request_id: str | None,
    source_http_status: int | None,
    raw: RawVendorPayload | None,
    config: DealerGexArchiveConfig,
) -> tuple[DealerGexSnapshot, bool]:
    """Persist one surface, reusing a replayed analytical observation identity."""

    if surface.observation_identity is not None:
        existing = session.scalar(
            select(DealerGexSnapshot).where(
                DealerGexSnapshot.observation_identity == surface.observation_identity
            )
        )
        if existing is not None:
            return existing, True

    row = DealerGexSnapshot(
        archive_run_id=run.id,
        ticker=surface.ticker,
        vendor_observed_at=surface.vendor_observed_at,
        captured_at=ensure_utc(captured_at),
        spot_usd=surface.spot_usd,
        source_quality=surface.source_quality,
        availability=surface.availability,
        endpoint=endpoint,
        capability=DEALER_GEX_CAPABILITY,
        endpoint_parameters=(
            {"format": config.endpoint_format} if config.endpoint_format is not None else {}
        ),
        source_request_id=source_request_id,
        raw_payload_id=raw.id if raw else None,
        source_http_status=source_http_status,
        safe_error_code=surface.safe_error_code,
        truncated=surface.truncated,
        cell_count=len(surface.cells) if surface.usable else 0,
        expiration_count=(
            len({cell.expiration for cell in surface.cells}) if surface.usable else 0
        ),
        surface_schema_version=DEALER_GEX_SURFACE_SCHEMA_VERSION,
        observation_identity=surface.observation_identity,
        is_analytical_observation=surface.usable,
        quality_details=surface.quality_details,
        specification_version=run.specification_version,
        config_version=config.version,
        config_hash=config.hash(),
    )
    session.add(row)
    session.flush()
    if surface.usable:
        session.add_all(
            [
                DealerGexSnapshotCell(
                    snapshot_id=row.id,
                    expiration=cell.expiration,
                    strike=cell.strike,
                    net_dealer_gex_usd=cell.net_dealer_gex_usd,
                    call_gex_usd=cell.call_gex_usd,
                    put_gex_usd=cell.put_gex_usd,
                )
                for cell in surface.cells
            ]
        )
    session.flush()
    return row, False


def archived_surface_payload(
    session: Session, snapshot: DealerGexSnapshot
) -> dict[str, Any]:
    cells = list(
        session.scalars(
            select(DealerGexSnapshotCell)
            .where(DealerGexSnapshotCell.snapshot_id == snapshot.id)
            .order_by(
                DealerGexSnapshotCell.expiration,
                DealerGexSnapshotCell.strike,
            )
        )
    )
    return {
        "ticker": snapshot.ticker,
        "generated_at": (
            snapshot.vendor_observed_at.isoformat() if snapshot.vendor_observed_at else None
        ),
        "capture_timestamp": snapshot.captured_at.isoformat(),
        "spot_usd": float(snapshot.spot_usd) if snapshot.spot_usd is not None else None,
        "availability": snapshot.source_quality,
        "availability_reason": snapshot.safe_error_code,
        "truncated": snapshot.truncated,
        "cells": [
            {
                "expiration": cell.expiration.isoformat(),
                "strike_usd": float(cell.strike),
                "net_dealer_gex_usd": (
                    float(cell.net_dealer_gex_usd)
                    if cell.net_dealer_gex_usd is not None
                    else None
                ),
                "call_gex_usd": (
                    float(cell.call_gex_usd) if cell.call_gex_usd is not None else None
                ),
                "put_gex_usd": (
                    float(cell.put_gex_usd) if cell.put_gex_usd is not None else None
                ),
            }
            for cell in cells
        ],
        "row_stacks": [],
        "archive_snapshot_id": str(snapshot.id),
        "raw_payload_id": str(snapshot.raw_payload_id) if snapshot.raw_payload_id else None,
        "source_request_id": snapshot.source_request_id,
    }


def best_archived_surface_at_or_before(
    session: Session,
    *,
    ticker: str,
    as_of: datetime,
) -> tuple[DealerGexSnapshot, dict[str, Any]] | None:
    """Return evidence that both existed and was vendor-observed by the cutoff."""

    cutoff = ensure_utc(as_of)
    snapshot = session.scalar(
        select(DealerGexSnapshot)
        .where(
            DealerGexSnapshot.ticker == ticker,
            DealerGexSnapshot.is_analytical_observation.is_(True),
            DealerGexSnapshot.vendor_observed_at <= cutoff,
            DealerGexSnapshot.captured_at <= cutoff,
        )
        .order_by(
            desc(DealerGexSnapshot.vendor_observed_at),
            desc(DealerGexSnapshot.captured_at),
        )
        .limit(1)
    )
    if snapshot is None:
        return None
    return snapshot, archived_surface_payload(session, snapshot)


def dealer_gex_history_coverage(
    session: Session, tickers: tuple[str, ...]
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for ticker in tickers:
        rows = list(
            session.scalars(
                select(DealerGexSnapshot)
                .where(DealerGexSnapshot.ticker == ticker)
                .order_by(DealerGexSnapshot.vendor_observed_at)
            )
        )
        valid = [row for row in rows if row.is_analytical_observation]
        result.append(
            {
                "ticker": ticker,
                "distinct_valid_observations": len(valid),
                "first_vendor_observed_at": (
                    valid[0].vendor_observed_at.isoformat() if valid else None
                ),
                "latest_vendor_observed_at": (
                    valid[-1].vendor_observed_at.isoformat() if valid else None
                ),
                "usable_observations": sum(
                    row.source_quality == "AVAILABLE" for row in valid
                ),
                "degraded_observations": sum(
                    row.source_quality == "AVAILABLE_DEGRADED" for row in valid
                ),
                "incomplete_attempts": sum(
                    row.source_quality == "INCOMPLETE_OR_TRUNCATED" for row in rows
                ),
                "unavailable_attempts": sum(
                    row.source_quality == "UNAVAILABLE" for row in rows
                ),
            }
        )
    return result
