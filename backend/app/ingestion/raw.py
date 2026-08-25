import hashlib
import json
import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time import ensure_utc, utc_now
from app.db.models import RawVendorPayload

VENDOR_TIME_KEYS = ("as_of", "generated_at", "observed_at", "data_as_of")


def parse_vendor_observed_at(payload: Any) -> datetime | None:
    """Parse an explicit, timezone-aware vendor timestamp without local fallback."""

    if not isinstance(payload, dict):
        return None
    containers = [payload]
    for key in ("data", "meta", "_meta"):
        value = payload.get(key)
        if isinstance(value, dict):
            containers.append(value)
    for container in containers:
        for key in VENDOR_TIME_KEYS:
            value = container.get(key)
            if isinstance(value, datetime):
                try:
                    return ensure_utc(value)
                except ValueError:
                    continue
            if not isinstance(value, str):
                continue
            try:
                return ensure_utc(datetime.fromisoformat(value.replace("Z", "+00:00")))
            except ValueError:
                continue
    return None


class RawIngestor:
    """Persists untouched vendor evidence before normalization."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def persist(
        self,
        *,
        endpoint: str,
        request_id: str,
        payload: dict[str, Any] | list[Any],
        vendor_request_id: str | None = None,
        source: str = "nightwatch",
        ticker: str | None = None,
        expiration: date | None = None,
        vendor_observed_at: datetime | None = None,
        scan_run_id: uuid.UUID | None = None,
    ) -> RawVendorPayload:
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
        payload_sha256 = hashlib.sha256(encoded).hexdigest()
        existing = self._session.scalar(
            select(RawVendorPayload).where(
                RawVendorPayload.source == source,
                RawVendorPayload.request_id == request_id,
            )
        )
        if existing is not None:
            if (
                existing.endpoint != endpoint
                or existing.payload_sha256 != payload_sha256
                or existing.ticker != ticker
                or existing.expiration != expiration
            ):
                raise ValueError("Source evidence identity conflicts with preserved raw payload")
            return existing
        row = RawVendorPayload(
            scan_run_id=scan_run_id,
            source=source,
            endpoint=endpoint,
            request_id=request_id,
            vendor_request_id=vendor_request_id,
            ticker=ticker,
            expiration=expiration,
            observed_at=(
                ensure_utc(vendor_observed_at) if vendor_observed_at is not None else None
            ),
            received_at=utc_now(),
            payload_sha256=payload_sha256,
            payload=payload,
        )
        self._session.add(row)
        self._session.flush()
        return row
