from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Any, Final

from app.config import get_settings
from app.core.time import MARKET_TIMEZONE, UTC

ACTIVE_DISCOVERY_FAMILIES: Final = (
    "RADAR_EVENT",
    "EXPIRY_ACTIVITY",
    "CONTRACT_PERSISTENCE",
)
REMOVED_ACTIVE_DISCOVERY_FAMILIES: Final = (
    "EXPIRY_PERSISTENCE",
    "STRUCTURAL_COLD_START",
    "EVIDENCE_BREADTH",
)


@dataclass(frozen=True)
class PersistenceFreshnessAssessment:
    eligible: bool
    state: str
    observation_age_days: int | None


@dataclass(frozen=True)
class PersistenceFreshnessPolicy:
    config_version: str
    max_vendor_observation_age_days: int | None

    @property
    def mode(self) -> str:
        return (
            "CALIBRATION_REQUIRED"
            if self.max_vendor_observation_age_days is None
            else "MAX_VENDOR_OBSERVATION_AGE_CALENDAR_DAYS"
        )

    def snapshot(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "config_version": self.config_version,
            "max_vendor_observation_age_days": self.max_vendor_observation_age_days,
            "age_basis": "ANALYSIS_NY_MARKET_DATE_MINUS_WINDOW_LAST_VENDOR_OI_DATE",
        }

    def assess(
        self, *, window_last_observation_date: date | None, analysis_date: date
    ) -> PersistenceFreshnessAssessment:
        if (
            window_last_observation_date is not None
            and window_last_observation_date > analysis_date
        ):
            return PersistenceFreshnessAssessment(False, "FUTURE_EVIDENCE_REJECTED", None)
        if self.max_vendor_observation_age_days is None:
            return PersistenceFreshnessAssessment(False, "CALIBRATION_REQUIRED", None)
        if window_last_observation_date is None:
            return PersistenceFreshnessAssessment(
                False, "WINDOW_LAST_OBSERVATION_DATE_UNAVAILABLE", None
            )
        age = (analysis_date - window_last_observation_date).days
        return PersistenceFreshnessAssessment(
            age <= self.max_vendor_observation_age_days,
            "CURRENT" if age <= self.max_vendor_observation_age_days else "STALE",
            age,
        )


def persistence_freshness_policy() -> PersistenceFreshnessPolicy:
    settings = get_settings()
    return PersistenceFreshnessPolicy(
        config_version=settings.phase2a_persistence_freshness_config_version,
        max_vendor_observation_age_days=(
            settings.phase2a_persistence_current_trigger_max_vendor_age_days
        ),
    )


def parse_observation_date(value: object) -> date | None:
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None
    return None


def persistence_window_last_observation_date(row: object) -> date | None:
    components = getattr(row, "persistent_components", None) or {}
    return parse_observation_date(components.get("window_last_observation_date"))


def analysis_date_exclusive_utc_cutoff(analysis_date: date) -> datetime:
    """Return the UTC instant immediately after an NY analysis date."""

    return datetime.combine(
        analysis_date + timedelta(days=1), time.min, tzinfo=MARKET_TIMEZONE
    ).astimezone(UTC)


def persistence_observation_is_time_admissible(row: object, *, analysis_date: date) -> bool:
    observed_at = getattr(row, "observed_at", None)
    return bool(
        isinstance(observed_at, datetime)
        and observed_at.tzinfo is not None
        and observed_at.astimezone(UTC) < analysis_date_exclusive_utc_cutoff(analysis_date)
    )


def select_current_persistence_observations(
    observations: Iterable[object],
    *,
    policy: PersistenceFreshnessPolicy,
    analysis_date: date,
) -> list[object]:
    """Select one admissible current observation per contract without lookahead.

    Callers provide observations newest-first.  Time admissibility and the configured
    freshness policy are evaluated before a contract identity is consumed, so a future,
    stale, or calibration-required row cannot hide an older admissible observation.
    """

    selected: list[object] = []
    seen_contracts: set[str] = set()
    for row in observations:
        if not persistence_observation_is_time_admissible(row, analysis_date=analysis_date):
            continue
        freshness = policy.assess(
            window_last_observation_date=persistence_window_last_observation_date(row),
            analysis_date=analysis_date,
        )
        if not freshness.eligible:
            continue
        contract_symbol = getattr(row, "contract_symbol", None)
        if not isinstance(contract_symbol, str) or contract_symbol in seen_contracts:
            continue
        seen_contracts.add(contract_symbol)
        selected.append(row)
    return selected


def group_product_candidates(
    anomalies: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build an in-memory ticker projection without ranking or discarding anomalies."""

    grouped: dict[str, list[dict[str, Any]]] = {}
    for anomaly in anomalies:
        family = anomaly.get("evidence_family")
        ticker = anomaly.get("ticker")
        if family not in ACTIVE_DISCOVERY_FAMILIES or not isinstance(ticker, str):
            continue
        grouped.setdefault(ticker, []).append(dict(anomaly))

    family_order = {family: index for index, family in enumerate(ACTIVE_DISCOVERY_FAMILIES)}
    projections: list[dict[str, Any]] = []
    for ticker in sorted(grouped):
        ticker_anomalies = sorted(
            grouped[ticker],
            key=lambda item: (
                family_order[str(item["evidence_family"])],
                str(item.get("anomaly_identity") or ""),
                str(item.get("evidence_date") or ""),
            ),
        )
        qualifying = [
            item for item in ticker_anomalies if item.get("qualifies_current_candidate") is True
        ]
        if not qualifying:
            continue
        projections.append(
            {
                "entity_type": "PRODUCT_CANDIDATE_PROJECTION",
                "ticker": ticker,
                "active_trigger_sources": [
                    family
                    for family in ACTIVE_DISCOVERY_FAMILIES
                    if any(item["evidence_family"] == family for item in qualifying)
                ],
                "anomaly_count": len(ticker_anomalies),
                "qualifying_anomaly_count": len(qualifying),
                "anomalies": ticker_anomalies,
            }
        )
    return projections
