from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from app.core.time import ensure_utc


class EvaluationIdentity(str, Enum):
    FIRST_KNOWLEDGE_BASELINE = "FIRST_KNOWLEDGE_BASELINE"
    REFRESH = "REFRESH"


@dataclass(frozen=True)
class CandidateFirstKnowledge:
    """Stage 3 contract for the ProductCandidate field persisted in Stage 5."""

    at: datetime | None = None
    materialization_rule_version: str | None = None

    def __post_init__(self) -> None:
        if self.at is None:
            if self.materialization_rule_version is not None:
                raise ValueError("Unresolved first knowledge cannot carry a rule version")
            return
        if not self.materialization_rule_version:
            raise ValueError("Known first knowledge requires a materialization rule version")
        object.__setattr__(self, "at", ensure_utc(self.at))

    def establish(
        self,
        *,
        at: datetime | None,
        materialization_rule_version: str | None,
    ) -> CandidateFirstKnowledge:
        """Set once; later evidence can never move an established value forward."""

        if self.at is not None or at is None:
            return self
        return CandidateFirstKnowledge(
            at=at,
            materialization_rule_version=materialization_rule_version,
        )


def source_time_entry(
    raw: Any,
    *,
    capability: str,
    trust_stored_vendor_time: bool = True,
) -> dict[str, Any]:
    """Build explicit time identities for one immutable raw source identity."""

    first_received = ensure_utc(raw.received_at)
    vendor_observed = (
        ensure_utc(raw.observed_at)
        if trust_stored_vendor_time and raw.observed_at is not None
        else None
    )
    freshness = vendor_observed or first_received
    return {
        "capability": capability,
        "availability": "AVAILABLE",
        "source_identity": {
            "source": raw.source,
            "request_id": raw.request_id,
            "raw_payload_id": str(raw.id),
            "payload_sha256": raw.payload_sha256,
        },
        "vendor_observed_at": _iso(vendor_observed),
        "local_captured_at": _iso(first_received),
        "source_first_received_at": _iso(first_received),
        "freshness_anchor_at": _iso(freshness),
        "freshness_basis": (
            "VENDOR_OBSERVED_AT" if vendor_observed is not None else "SOURCE_FIRST_RECEIVED_AT"
        ),
    }


def unavailable_source_time_entry(
    *, capability: str, local_captured_at: datetime
) -> dict[str, Any]:
    """Record an unavailable request attempt without manufacturing source evidence time."""

    captured = ensure_utc(local_captured_at)
    return {
        "capability": capability,
        "availability": "UNAVAILABLE",
        "source_identity": None,
        "vendor_observed_at": None,
        "local_captured_at": _iso(captured),
        "source_first_received_at": None,
        "freshness_anchor_at": _iso(captured),
        "freshness_basis": "LOCAL_REQUEST_ATTEMPT_ONLY",
    }


def aggregate_source_first_received_at(entries: dict[str, Any]) -> datetime | None:
    values = [
        parsed
        for entry in entries.values()
        if isinstance(entry, dict)
        and (parsed := _parse_datetime(entry.get("source_first_received_at"))) is not None
    ]
    return min(values) if values else None


def aggregate_freshness_anchor_at(entries: dict[str, Any]) -> datetime | None:
    if not entries:
        return None
    values: list[datetime] = []
    for entry in entries.values():
        if not isinstance(entry, dict):
            return None
        parsed = _parse_datetime(entry.get("freshness_anchor_at"))
        if parsed is None:
            return None
        values.append(parsed)
    return min(values) if values else None


def earliest_known(*values: datetime | None) -> datetime | None:
    known = [ensure_utc(value) for value in values if value is not None]
    return min(known) if known else None


def _parse_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        try:
            return ensure_utc(value)
        except ValueError:
            return None
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return ensure_utc(parsed)
    except ValueError:
        return None


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None
