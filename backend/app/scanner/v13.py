from __future__ import annotations

import hashlib
import json
from calendar import monthrange
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import desc, func, select

from app.config import get_settings
from app.core.time import is_xnys_session
from app.db.models import (
    ContractScanObservation,
    ExpiryObservation,
    OiChangeRadarObservation,
    StrikeCluster,
    TickerScanResult,
)
from app.scanner.config import LIMITS, SIGNAL_SPEC_VERSION, UNIVERSE
from app.scanner.v12 import Mag7Scanner as V12Mag7Scanner
from app.scanner.vnext import (
    analysis_date_exclusive_utc_cutoff,
    persistence_freshness_policy,
    persistence_window_last_observation_date,
    select_current_persistence_observations,
)


@dataclass(frozen=True)
class RadarThresholdProfile:
    """Immutable effective Radar gate configuration for one evaluation session."""

    profile_id: str
    version: str
    enabled: bool
    min_premium_usd: Decimal
    min_abs_oi_diff: int
    calibration_review_sessions: int

    def snapshot(self) -> dict[str, Any]:
        values: dict[str, Any] = {
            "profile_id": self.profile_id,
            "version": self.version,
            "enabled": self.enabled,
            "min_premium_usd": str(self.min_premium_usd),
            "min_abs_oi_diff": self.min_abs_oi_diff,
            "calibration_review_sessions": self.calibration_review_sessions,
        }
        values["configuration_hash"] = _configuration_hash(values)
        return values

    @property
    def configuration_hash(self) -> str:
        return str(self.snapshot()["configuration_hash"])


def active_radar_threshold_profile() -> RadarThresholdProfile:
    settings = get_settings()
    return RadarThresholdProfile(
        profile_id=settings.radar_threshold_profile_id,
        version=settings.radar_threshold_profile_version,
        enabled=settings.radar_threshold_enabled,
        min_premium_usd=settings.radar_min_premium_usd,
        min_abs_oi_diff=settings.radar_min_abs_oi_diff,
        calibration_review_sessions=settings.radar_calibration_review_sessions,
    )


@dataclass(frozen=True)
class RadarEligibility:
    eligible: bool
    reason: str
    risk_flags: tuple[str, ...]


@dataclass(frozen=True)
class RouteState:
    radar_route_eligible: bool
    persistent_route_eligible: bool
    expiry_activity_route_eligible: bool
    trigger_sources: tuple[str, ...]
    deep_dive_eligible: bool


def evaluate_radar_material_event(
    *,
    premium_usd: Decimal | float | int | None,
    oi_diff: int | None,
    previous_oi: int | None,
    profile: RadarThresholdProfile,
) -> RadarEligibility:
    """Evaluate only the supplied, versioned profile; no threshold lives in this logic."""

    flags = ("LOW_OI_BASE",) if previous_oi is not None and previous_oi < 100 else ()
    if not profile.enabled:
        return RadarEligibility(False, "PROFILE_DISABLED", flags)
    if premium_usd is None:
        return RadarEligibility(False, "MISSING_PREMIUM", flags)
    if oi_diff is None:
        return RadarEligibility(False, "MISSING_OI_DIFF", flags)
    if Decimal(str(premium_usd)) < profile.min_premium_usd:
        return RadarEligibility(False, "PREMIUM_BELOW_PROFILE_MINIMUM", flags)
    if abs(oi_diff) < profile.min_abs_oi_diff:
        return RadarEligibility(False, "ABS_OI_DIFF_BELOW_PROFILE_MINIMUM", flags)
    return RadarEligibility(True, "RADAR_MATERIAL_EVENT", flags)


def radar_scope(*, dte: int | None, exact_match: bool, chain_complete: bool) -> str:
    if not exact_match:
        return "UNJOINED"
    if dte is None or dte < 0 or dte > 180:
        return "OUTSIDE_ARCHIVE_SCOPE"
    if not chain_complete:
        return "INCOMPLETE_CHAIN"
    if dte > 90:
        return "LONG_DTE_RADAR_WATCH"
    return "FULL_DEEP_DIVE_ELIGIBLE"


def is_standard_monthly_expiry(expiration: date) -> bool:
    """Calendar-only third-Friday context; it never affects a score."""

    first_weekday, days = monthrange(expiration.year, expiration.month)
    first_friday = 1 + (4 - first_weekday) % 7
    third_friday = first_friday + 14
    return expiration.day == third_friday and expiration.day <= days


def same_day_score_basis(
    components: dict[str, Any] | None, *, dte: int | None = None
) -> tuple[float | None, float | None, str]:
    if dte == 0:
        return None, None, "ZERO_DTE_HISTORICAL_CALIBRATION"
    values = components or {}
    volume_share_points = float(values.get("expiry_volume_share") or 0)
    neighbor_points = float(values.get("comparable_expiry_volume_neighbor_ratio") or 0)
    if volume_share_points > neighbor_points + 10:
        classification = "VOLUME_SHARE_DOMINATED"
    elif neighbor_points > volume_share_points + 10:
        classification = "NEIGHBOR_DOMINATED"
    else:
        classification = "BALANCED"
    return volume_share_points, neighbor_points, classification


def ordered_trigger_sources(sources: Iterable[str]) -> list[str]:
    priority = {
        "RADAR_EVENT": 0,
        "EXPIRY_ACTIVITY": 1,
        "CONTRACT_PERSISTENCE": 2,
    }
    return sorted(
        {source for source in sources if source in priority},
        key=lambda value: priority[value],
    )


def resolve_route_state(
    *,
    radar_event: bool = False,
    contract_persistence: bool = False,
    expiry_persistence: bool = False,
    expiry_activity: bool = False,
    structural_cold_start: bool = False,
) -> RouteState:
    sources: list[str] = []
    if radar_event:
        sources.append("RADAR_EVENT")
    if contract_persistence:
        sources.append("CONTRACT_PERSISTENCE")
    if expiry_activity:
        sources.append("EXPIRY_ACTIVITY")
    ordered = tuple(ordered_trigger_sources(sources))
    return RouteState(
        radar_route_eligible=radar_event,
        persistent_route_eligible=contract_persistence,
        expiry_activity_route_eligible=expiry_activity,
        trigger_sources=ordered,
        deep_dive_eligible=bool(ordered),
    )


def deduplicate_deep_dive_requests(
    candidates: Iterable[tuple[str, date, str]],
) -> dict[tuple[str, date], list[str]]:
    result: dict[tuple[str, date], list[str]] = {}
    for ticker, expiration, source in candidates:
        key = (ticker, expiration)
        result[key] = ordered_trigger_sources([*result.get(key, []), source])
    return result


def _configuration_hash(values: dict[str, Any]) -> str:
    encoded = json.dumps(values, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


class Mag7Scanner(V12Mag7Scanner):
    """Phase 2A vNext scanner over the accepted Stage 3 persistence structures."""

    def _preflight_v11(self, market_day: date) -> None:
        if not is_xnys_session(market_day):
            raise RuntimeError(
                f"Current-candidate analysis requires an XNYS trading session: {market_day}"
            )
        super()._preflight_v11(market_day)
        profile = active_radar_threshold_profile()
        self.run.radar_threshold_profile_id = profile.profile_id
        self.run.radar_threshold_profile_version = profile.version
        self.run.radar_threshold_config_hash = profile.configuration_hash
        self.session.commit()

    async def _activity_surface(
        self, market_day: date
    ) -> tuple[list[TickerScanResult], list[ExpiryObservation]]:
        tickers, expiries = await super()._activity_surface(market_day)
        for row in expiries:
            same_day = _number(row.same_day_activity_score)
            activity_eligible = bool(
                same_day is not None and same_day >= LIMITS.same_day_eligibility_score
            )
            sources = ["EXPIRY_ACTIVITY"] if activity_eligible else []
            volume_points, neighbor_points, basis = same_day_score_basis(
                (row.components or {}).get("same_day"), dte=row.dte_at_detection
            )
            row.persistent_route_eligible = False
            row.expiry_activity_route_eligible = activity_eligible
            row.trigger_sources = ordered_trigger_sources(sources)
            row.deep_dive_eligible = bool(sources)
            row.structural_cold_start_eligible = False
            row.classification = "DISCOVERY_ELIGIBLE" if activity_eligible else "OBSERVE"
            # Preserve the accepted columns for historical reads, but do not write the removed
            # universal/breadth semantics into new vNext evidence.
            row.discovery_score = None
            row.discovery_source = None
            row.discovery_primary_score = None
            row.discovery_secondary_score = None
            row.discovery_confirmation_bonus = None
            row.discovery_evidence_breadth = None
            row.standard_monthly_inferred = is_standard_monthly_expiry(row.expiration)
            row.monthly_context_source = "INFERRED" if row.standard_monthly_inferred else None
            row.volume_share_points = (
                Decimal(str(volume_points)) if volume_points is not None else None
            )
            row.neighbor_points = (
                Decimal(str(neighbor_points)) if neighbor_points is not None else None
            )
            row.same_day_score_basis = basis
            row.specification_version = SIGNAL_SPEC_VERSION
        for ticker in tickers:
            ticker.preliminary_score = None
            ticker.specification_version = SIGNAL_SPEC_VERSION
        self.session.commit()
        self._stage(
            "S3_VNEXT_ACTIVE_DISCOVERY",
            active_families=["RADAR_EVENT", "EXPIRY_ACTIVITY", "CONTRACT_PERSISTENCE"],
            removed_active_families=[
                "EXPIRY_PERSISTENCE",
                "STRUCTURAL_COLD_START",
                "EVIDENCE_BREADTH",
            ],
            universal_score=False,
        )
        return tickers, expiries

    def _select_dual(
        self, tickers: list[TickerScanResult], expiries: list[ExpiryObservation]
    ) -> list[ExpiryObservation]:
        assert self.run and self.run.market_date
        policy = persistence_freshness_policy()
        analysis_date = self.run.market_date
        by_key = {(row.ticker, row.expiration): row for row in expiries}
        latest_radar_dates = {
            ticker: self.session.scalar(
                select(func.max(OiChangeRadarObservation.observation_date)).where(
                    OiChangeRadarObservation.ticker == ticker,
                    OiChangeRadarObservation.material_event_eligible.is_(True),
                )
            )
            for ticker in UNIVERSE
        }
        radar_rows: list[OiChangeRadarObservation] = []
        for ticker, latest in latest_radar_dates.items():
            if latest:
                radar_rows.extend(
                    self.session.scalars(
                        select(OiChangeRadarObservation).where(
                            OiChangeRadarObservation.ticker == ticker,
                            OiChangeRadarObservation.observation_date == latest,
                            OiChangeRadarObservation.material_event_eligible.is_(True),
                        )
                    )
                )
        radar_premium: dict[tuple[str, date], float] = {}
        for event in radar_rows:
            if not event.matched_expiration:
                continue
            key = (event.ticker, event.matched_expiration)
            expiry = by_key.get(key)
            if expiry is None:
                continue
            if event.radar_scope == "FULL_DEEP_DIVE_ELIGIBLE":
                expiry.radar_route_eligible = True
                expiry.deep_dive_eligible = True
                expiry.trigger_sources = ordered_trigger_sources(
                    [*(expiry.trigger_sources or []), "RADAR_EVENT"]
                )
            radar_premium[key] = max(radar_premium.get(key, 0), _number(event.premium) or 0)

        # Contract persistence discovered by prior complete archived analysis remains independent
        # of the current expiry-activity score.
        latest_contracts = list(
            self.session.scalars(
                select(ContractScanObservation)
                .where(
                    ContractScanObservation.persistent_positioning_score
                    >= LIMITS.persistent_eligibility_score,
                    ContractScanObservation.observed_at
                    < analysis_date_exclusive_utc_cutoff(analysis_date),
                )
                .order_by(desc(ContractScanObservation.observed_at))
            )
        )
        contract_persistence: dict[tuple[str, date], float] = {}
        current_persistence = select_current_persistence_observations(
            latest_contracts,
            policy=policy,
            analysis_date=analysis_date,
        )
        for contract in current_persistence:
            key = (contract.ticker, contract.expiration)
            expiry = by_key.get(key)
            if expiry is None:
                continue
            expiry.persistent_route_eligible = True
            expiry.deep_dive_eligible = True
            expiry.trigger_sources = ordered_trigger_sources(
                [*(expiry.trigger_sources or []), "CONTRACT_PERSISTENCE"]
            )
            contract_persistence[key] = _number(contract.persistent_positioning_score) or 0

        candidates = [
            row
            for row in expiries
            if row.deep_dive_eligible and row.dte_at_detection <= 90
        ]

        def priority(row: ExpiryObservation) -> tuple[Any, ...]:
            sources = set(row.trigger_sources or [])
            route_rank = (
                0
                if "RADAR_EVENT" in sources
                else 1
                if "EXPIRY_ACTIVITY" in sources
                else 2
                if "CONTRACT_PERSISTENCE" in sources
                else 3
            )
            key = (row.ticker, row.expiration)
            route_value = (
                radar_premium.get(key, 0)
                if route_rank == 0
                else _number(row.same_day_activity_score) or 0
                if route_rank == 1
                else contract_persistence.get(key, 0)
            )
            return route_rank, -route_value, row.ticker, row.expiration

        ordered = sorted(candidates, key=priority)
        selected: list[ExpiryObservation] = []
        ticker_counts: dict[str, int] = {}
        selected_tickers: set[str] = set()
        for row in ordered:
            if (
                row.ticker not in selected_tickers
                and len(selected_tickers) >= LIMITS.max_deep_tickers
            ):
                continue
            if ticker_counts.get(row.ticker, 0) >= LIMITS.max_expiries_per_ticker:
                continue
            selected.append(row)
            selected_tickers.add(row.ticker)
            ticker_counts[row.ticker] = ticker_counts.get(row.ticker, 0) + 1
            row.selected_for_deep_scan = True
        for ticker in tickers:
            ticker.selected_for_deep_scan = ticker.ticker in selected_tickers
        self.session.commit()
        selected_ids = {row.id for row in selected}
        truncated = [
            {"ticker": row.ticker, "expiration": row.expiration.isoformat()}
            for row in ordered
            if row.id not in selected_ids
        ]
        self._stage(
            "S4_VNEXT_DEEP_BUDGET_SELECTION",
            route_priority=["RADAR_EVENT", "EXPIRY_ACTIVITY", "CONTRACT_PERSISTENCE"],
            selected_expiries=len(selected),
            eligible_expiries=len(ordered),
            operational_truncation=bool(truncated),
            truncated_expiries=truncated,
            candidate_identity_affected=False,
            deduplicated_chain_loads=len({(row.ticker, row.expiration) for row in selected}),
        )
        return selected

    async def _radar(
        self,
        selected: list[ExpiryObservation],
        contracts: list[ContractScanObservation],
    ) -> int:
        """Attach latest persisted Radar; interactive scans make no oi-change request."""

        by_symbol = {row.contract_symbol: row for row in contracts}
        matches = 0
        for ticker in {row.ticker for row in selected}:
            latest = self.session.scalar(
                select(func.max(OiChangeRadarObservation.observation_date)).where(
                    OiChangeRadarObservation.ticker == ticker
                )
            )
            if latest is None:
                continue
            events = self.session.scalars(
                select(OiChangeRadarObservation).where(
                    OiChangeRadarObservation.ticker == ticker,
                    OiChangeRadarObservation.observation_date == latest,
                )
            )
            for event in events:
                contract = by_symbol.get(event.contract_symbol)
                if contract is None:
                    continue
                matches += 1
                contract.oi_change_radar_status = "OBSERVED"
                contract.oi_change_radar_evidence = {
                    "delta_oi": event.delta_oi,
                    "premium": _number(event.premium),
                    "rank": event.rank,
                    "observation_date": latest.isoformat(),
                    "material_event_eligible": event.material_event_eligible,
                    "threshold_profile_version": event.threshold_profile_version,
                }
                if event.material_event_eligible:
                    contract.radar_route_eligible = True
                    contract.deep_dive_eligible = bool(event.deep_dive_eligible)
                    contract.trigger_sources = ordered_trigger_sources(
                        [*(contract.trigger_sources or []), "RADAR_EVENT"]
                    )
        self.session.commit()
        return matches

    async def _structure_scan(
        self, selected: list[ExpiryObservation], market_day: date
    ) -> tuple[list[ContractScanObservation], list[StrikeCluster], int]:
        partial_before_deep_dive = self.partial
        contracts, clusters, radar_matches = await super()._structure_scan(selected, market_day)
        # Structure is optional post-candidate context in vNext.  The inherited scanner marks a
        # missing complete chain archive as run-level PARTIAL; keep the missing structure rows
        # absent, but do not let that Deep-Dive-only condition suppress candidate materialization.
        # A legitimate partial condition established before Deep Dive remains authoritative.
        self.partial = partial_before_deep_dive
        policy = persistence_freshness_policy()
        expiry_by_id = {row.id: row for row in selected}
        for contract in contracts:
            persistent = _number(contract.persistent_positioning_score)
            last_observation_date = persistence_window_last_observation_date(contract)
            freshness = policy.assess(
                window_last_observation_date=last_observation_date,
                analysis_date=market_day,
            )
            persistent_components = dict(contract.persistent_components or {})
            persistent_components["current_trigger_freshness"] = {
                **policy.snapshot(),
                "state": freshness.state,
                "eligible": freshness.eligible,
                "observation_age_days": freshness.observation_age_days,
            }
            contract.persistent_components = persistent_components
            persistence_current = bool(
                persistent is not None
                and persistent >= LIMITS.persistent_eligibility_score
                and freshness.eligible
            )
            contract.persistent_route_eligible = persistence_current
            if persistence_current:
                contract.persistent_route_eligible = True
                contract.trigger_sources = ordered_trigger_sources(
                    [*(contract.trigger_sources or []), "CONTRACT_PERSISTENCE"]
                )
            expiry = expiry_by_id.get(contract.expiry_observation_id)
            if expiry:
                contract.deep_dive_eligible = expiry.deep_dive_eligible
                contract.trigger_sources = ordered_trigger_sources(
                    [*(contract.trigger_sources or []), *(expiry.trigger_sources or [])]
                )
            contract.specification_version = SIGNAL_SPEC_VERSION
        self.session.commit()
        return contracts, clusters, radar_matches


def _number(value: Any) -> float | None:
    return float(value) if value is not None else None
