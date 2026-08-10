import hashlib
import json
from datetime import date, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.core.time import ensure_utc, utc_now
from app.db.models import RawVendorPayload


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
        ticker: str | None = None,
        expiration: date | None = None,
        observed_at: datetime | None = None,
    ) -> RawVendorPayload:
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
        row = RawVendorPayload(
            endpoint=endpoint,
            request_id=request_id,
            vendor_request_id=vendor_request_id,
            ticker=ticker,
            expiration=expiration,
            observed_at=ensure_utc(observed_at) if observed_at else None,
            received_at=utc_now(),
            payload_sha256=hashlib.sha256(encoded).hexdigest(),
            payload=payload,
        )
        self._session.add(row)
        self._session.flush()
        return row

