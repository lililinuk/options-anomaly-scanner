from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Final

import exchange_calendars as xcals
import pandas as pd
from sqlalchemy import desc, select
from sqlalchemy.orm import Session, selectinload

from app.confirmation.config import Phase2bContextConfig, active_phase2b_config
from app.confirmation.domain import strike_location
from app.confirmation.provenance import EvaluationIdentity
from app.confirmation.vnext import dealer_gex_context_for_expiry
from app.core.time import ensure_utc, market_date, utc_now
from app.db.models import (
    ContractScanObservation,
    ExpiryObservation,
    OiChangeRadarObservation,
    ProductCandidate,
    ProductCandidateContext,
    ProductCandidateTrigger,
    ScanRun,
)
from app.dealer_archive.repository import best_archived_surface_at_or_before
from app.scanner.candidate_persistence import load_product_candidates_for_scan
from app.scanner.config import SIGNAL_SPEC_VERSION

FAMILY_ORDER: Final = ("RADAR_EVENT", "EXPIRY_ACTIVITY", "CONTRACT_PERSISTENCE")
FAMILY_LABELS: Final = {
    "RADAR_EVENT": "Radar",
    "EXPIRY_ACTIVITY": "Expiry Activity",
    "CONTRACT_PERSISTENCE": "Contract Persistence",
}
FRESHNESS_STATES: Final = frozenset({"CURRENT", "STALE", "UNAVAILABLE"})


def latest_successful_candidate_run(session: Session) -> ScanRun | None:
    """Return the latest accepted, completely materialized Candidate population."""

    return session.scalar(
        select(ScanRun)
        .where(
            ScanRun.status == "COMPLETE",
            ScanRun.specification_version == SIGNAL_SPEC_VERSION,
            ScanRun.candidate_materialized_at.is_not(None),
        )
        .order_by(
            desc(ScanRun.market_date),
            desc(ScanRun.completed_at),
            desc(ScanRun.started_at),
        )
        .limit(1)
    )


def trading_dashboard_read_model(
    session: Session, *, as_of: datetime | None = None
) -> dict[str, Any]:
    """Build a read-only Trading view without contacting a vendor or mutating evidence."""

    generated_at = ensure_utc(as_of or utc_now())
    run = latest_successful_candidate_run(session)
    if run is None:
        return {
            "generated_at": generated_at.isoformat(),
            "market_timezone": "America/New_York",
            "candidate_population": _unavailable_population(),
            "candidates": [],
            "contracts": {
                "vendor_requests_on_read": 0,
                "frozen_first_knowledge_mutated": False,
                "automatic_context_capture": False,
            },
        }

    candidates = load_product_candidates_for_scan(session, run.id)
    config = active_phase2b_config()
    cards = [
        _candidate_read_model(session, candidate, generated_at=generated_at, config=config)
        for candidate in candidates
    ]
    return {
        "generated_at": generated_at.isoformat(),
        "market_timezone": "America/New_York",
        "candidate_population": {
            "state": "AVAILABLE",
            # No accepted Candidate-population freshness duration exists. Per the
            # canonical Dashboard contract, availability therefore cannot claim CURRENT.
            "freshness": "STALE",
            "freshness_reason": "NO_ACCEPTED_CANDIDATE_FRESHNESS_RULE",
            "market_date": run.market_date.isoformat() if run.market_date else None,
            "scan_run_id": str(run.id),
            "started_at": _iso(run.started_at),
            "completed_at": _iso(run.completed_at),
            "candidate_materialized_at": _iso(run.candidate_materialized_at),
            "candidate_count": len(cards),
        },
        "candidates": cards,
        "contracts": {
            "vendor_requests_on_read": 0,
            "frozen_first_knowledge_mutated": False,
            "automatic_context_capture": False,
        },
    }


def expiration_is_active(expiration: date, *, as_of: datetime) -> bool:
    """Keep an expiry active only through its authoritative final XNYS close."""

    instant = ensure_utc(as_of)
    calendar = xcals.get_calendar("XNYS")
    label = calendar.date_to_session(pd.Timestamp(expiration.isoformat()), direction="previous")
    session_close = ensure_utc(calendar.session_close(label).to_pydatetime())
    return instant <= session_close


def freshness_state(
    source_as_of: datetime | str | None,
    *,
    as_of: datetime,
    max_age_minutes: int,
) -> str:
    source_time = _datetime(source_as_of)
    if source_time is None:
        return "UNAVAILABLE"
    age = ensure_utc(as_of) - source_time
    if timedelta(0) <= age <= timedelta(minutes=max_age_minutes):
        return "CURRENT"
    return "STALE"


def select_featured_anomalies(anomalies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Select at most one active item per family using accepted native ordering only."""

    featured: list[dict[str, Any]] = []
    radar = [item for item in anomalies if item["family"] == "RADAR_EVENT"]
    if radar:
        featured.append(
            max(
                radar,
                key=lambda item: (
                    _number(item.get("premium_usd")) or 0,
                    abs(_number(item.get("delta_oi")) or 0),
                    str(item.get("identity") or ""),
                ),
            )
        )
    activity = [item for item in anomalies if item["family"] == "EXPIRY_ACTIVITY"]
    scored_activity = [
        item for item in activity if _number(item.get("same_day_activity_score")) is not None
    ]
    if scored_activity:
        featured.append(
            max(
                scored_activity,
                key=lambda item: (
                    _number(item.get("same_day_activity_score")) or 0,
                    str(item.get("identity") or ""),
                ),
            )
        )
    # Contract Persistence has no Founder-accepted native presentation ranking.
    return featured[:3]


def _candidate_read_model(
    session: Session,
    candidate: ProductCandidate,
    *,
    generated_at: datetime,
    config: Phase2bContextConfig,
) -> dict[str, Any]:
    contexts = list(
        session.scalars(
            select(ProductCandidateContext)
            .options(selectinload(ProductCandidateContext.details))
            .where(ProductCandidateContext.product_candidate_id == candidate.id)
            .order_by(desc(ProductCandidateContext.context_evaluated_at))
        )
    )
    current = next(
        (item for item in contexts if item.evaluation_kind == EvaluationIdentity.REFRESH.value),
        None,
    )
    frozen_available = any(
        item.evaluation_kind == EvaluationIdentity.FIRST_KNOWLEDGE_BASELINE.value
        for item in contexts
    )
    details = {
        detail.product_candidate_trigger_id: detail
        for detail in (current.details if current is not None else [])
    }
    active: list[dict[str, Any]] = []
    for trigger in candidate.triggers:
        anomaly = _active_anomaly(
            session,
            trigger,
            detail=details.get(trigger.id),
            as_of=generated_at,
        )
        if anomaly is not None:
            active.append(anomaly)

    price = _price_context(current, as_of=generated_at, config=config)
    for anomaly in active:
        anomaly["price_relationship"] = _price_relationship(
            anomaly,
            price=price,
            context=current,
            config=config,
        )
    featured = select_featured_anomalies(active)
    featured_ids = {item["id"] for item in featured}
    for anomaly in active:
        anomaly["featured"] = anomaly["id"] in featured_ids
        if anomaly["featured"]:
            anomaly["featured_semantic"] = "PRIORITY_TO_INSPECT"

    counts = {family: sum(item["family"] == family for item in active) for family in FAMILY_ORDER}
    active_expirations = {
        _date(item.get("expiration"))
        for item in active
        if _date(item.get("expiration")) is not None
    }
    return {
        "id": str(candidate.id),
        "scan_run_id": str(candidate.scan_run_id),
        "ticker": candidate.ticker,
        "candidate_first_knowledge_at": _iso(candidate.candidate_first_knowledge_at),
        "active_anomaly_count": len(active),
        "active_family_counts": counts,
        "featured_anomalies": featured,
        "active_anomalies": active,
        "current_trading_context": {
            "identity": {
                "state": "AVAILABLE" if current is not None else "UNAVAILABLE",
                "context_id": str(current.id) if current is not None else None,
                "evaluated_at": _iso(current.context_evaluated_at) if current else None,
                # The existing schema does not preserve a REFRESH origin. Null is
                # intentionally truthful and leaves room for a later accepted origin.
                "origin": None,
                "origin_state": "NOT_PERSISTED",
            },
            "price": price,
            "volatility": _volatility_context(
                current,
                active_expirations=active_expirations,
                as_of=generated_at,
                config=config,
            ),
            "dealer_gex": _dealer_gex_context(
                session,
                ticker=candidate.ticker,
                price=price,
                as_of=generated_at,
                config=config,
            ),
        },
        "frozen_first_knowledge": {
            "state": "PRESERVED_OUTSIDE_TRADING_VIEW",
            "available": frozen_available,
            "rendered_as_current": False,
        },
    }


def _active_anomaly(
    session: Session,
    trigger: ProductCandidateTrigger,
    *,
    detail: Any | None,
    as_of: datetime,
) -> dict[str, Any] | None:
    source: Any | None = None
    if trigger.evidence_family == "RADAR_EVENT" and trigger.source_radar_observation_id:
        source = session.get(OiChangeRadarObservation, trigger.source_radar_observation_id)
        expiration = getattr(source, "matched_expiration", None)
    elif trigger.evidence_family == "EXPIRY_ACTIVITY" and trigger.source_expiry_observation_id:
        source = session.get(ExpiryObservation, trigger.source_expiry_observation_id)
        expiration = getattr(source, "expiration", None)
    elif trigger.source_contract_observation_id:
        source = session.get(ContractScanObservation, trigger.source_contract_observation_id)
        expiration = getattr(source, "expiration", None)
    else:
        expiration = None
    if source is None or not isinstance(expiration, date):
        return None
    if not expiration_is_active(expiration, as_of=as_of):
        return None

    contract = _record(getattr(detail, "contract_snapshot", None))
    expiry = _record(getattr(detail, "expiry_activity_recap", None))
    right = getattr(source, "matched_right", None)
    strike = _number(getattr(source, "matched_strike", None))
    detection_dte = getattr(source, "matched_dte", None)
    detection_bucket = None
    if trigger.evidence_family == "EXPIRY_ACTIVITY":
        detection_dte = getattr(source, "dte_at_detection", None)
        detection_bucket = getattr(source, "bucket_at_detection", None)
    elif trigger.evidence_family == "CONTRACT_PERSISTENCE":
        detection_dte = getattr(source, "dte_at_detection", None)
        detection_bucket = getattr(source, "bucket_at_detection", None)
        right = getattr(source, "right", None)
        strike = _number(getattr(source, "strike", None))

    return {
        "id": str(trigger.id),
        "family": trigger.evidence_family,
        "family_label": FAMILY_LABELS[trigger.evidence_family],
        "entity_type": trigger.anomaly_entity_type,
        "identity": trigger.anomaly_identity,
        "expiration": expiration.isoformat(),
        "current_dte": max(0, (expiration - market_date(as_of)).days),
        "detection_dte": detection_dte,
        "detection_bucket": detection_bucket,
        "qualifies_candidate": trigger.qualifies_candidate,
        "right": right,
        "strike": strike,
        "delta_oi": getattr(source, "delta_oi", None),
        "premium_usd": _number(getattr(source, "premium", None)),
        "same_day_activity_score": _number(getattr(source, "same_day_activity_score", None)),
        "same_day_score_basis": getattr(source, "same_day_score_basis", None),
        "quote": {
            "freshness": "UNAVAILABLE" if detail is None else "STALE",
            "as_of": _iso(getattr(detail, "quote_as_of", None)),
            "iv": _number(contract.get("contract_iv")),
            "delta": _number(contract.get("delta")),
            "bid_usd": _number(contract.get("bid")),
            "ask_usd": _number(contract.get("ask")),
            "spread_pct": _number(contract.get("spread_pct")),
        },
        "expiry_activity": {
            "call_volume": expiry.get("call_volume"),
            "put_volume": expiry.get("put_volume"),
            "call_oi": expiry.get("call_oi"),
            "put_oi": expiry.get("put_oi"),
        }
        if trigger.evidence_family == "EXPIRY_ACTIVITY"
        else None,
    }


def _price_context(
    context: ProductCandidateContext | None,
    *,
    as_of: datetime,
    config: Phase2bContextConfig,
) -> dict[str, Any]:
    if context is None:
        return _unavailable_block("NO_PERSISTED_CURRENT_CONTEXT")
    price_context = _record(context.price_context)
    stock = _record(price_context.get("stock_state"))
    history = _record(price_context.get("history"))
    stock_as_of = _context_source_time(context, "stock_state", stock.get("as_of"))
    stock_freshness = freshness_state(
        stock_as_of,
        as_of=as_of,
        max_age_minutes=config.stock_state_freshness_minutes,
    )
    stock_value = _number(stock.get("current_price_usd"))
    if stock_value is not None and stock_freshness == "CURRENT":
        return {
            "freshness": "CURRENT",
            "label": "Current Price",
            "value_usd": stock_value,
            "source": "stock_state.current_price_usd",
            "as_of": _iso(stock_as_of),
            "session": stock.get("session"),
            "fallback_used": False,
            "stock_state_freshness": stock_freshness,
        }

    close = _number(history.get("latest_regular_close_usd"))
    close_as_of = _context_source_time(context, "daily_ohlc", context.price_as_of)
    close_freshness = freshness_state(
        close_as_of,
        as_of=as_of,
        max_age_minutes=config.ohlc_freshness_minutes,
    )
    if close is not None:
        return {
            "freshness": close_freshness,
            "label": "Previous Close",
            "value_usd": close,
            "source": "daily_ohlc.valid_regular_session_close",
            "as_of": _iso(close_as_of),
            "session": "REGULAR_CLOSE",
            "market_date": history.get("latest_trading_date"),
            "fallback_used": True,
            "stock_state_freshness": stock_freshness,
        }
    if stock_value is not None:
        return {
            "freshness": "STALE",
            "label": "Latest Vendor Price",
            "value_usd": stock_value,
            "source": "stock_state.current_price_usd",
            "as_of": _iso(stock_as_of),
            "session": stock.get("session"),
            "fallback_used": False,
            "stock_state_freshness": stock_freshness,
        }
    return _unavailable_block("NO_ELIGIBLE_PERSISTED_PRICE")


def _volatility_context(
    context: ProductCandidateContext | None,
    *,
    active_expirations: set[date | None],
    as_of: datetime,
    config: Phase2bContextConfig,
) -> dict[str, Any]:
    if context is None:
        return _unavailable_block("NO_PERSISTED_CURRENT_CONTEXT")
    volatility = _record(context.volatility_context)
    iv_rank = _record(volatility.get("iv_rank"))
    term = _record(volatility.get("term_structure"))
    iv_as_of = _context_source_time(context, "iv_rank", iv_rank.get("as_of"))
    term_as_of = _context_source_time(context, "term_structure", term.get("as_of"))
    iv_freshness = freshness_state(
        iv_as_of,
        as_of=as_of,
        max_age_minutes=config.iv_rank_freshness_minutes,
    )
    term_freshness = freshness_state(
        term_as_of,
        as_of=as_of,
        max_age_minutes=config.term_structure_freshness_minutes,
    )
    expiry_contexts = _record(volatility.get("expiry_contexts"))
    active_keys = {item.isoformat() for item in active_expirations if item is not None}
    active_terms = {
        key: value
        for key, value in expiry_contexts.items()
        if key in active_keys and isinstance(value, dict)
    }
    overall = term_freshness if active_terms else "UNAVAILABLE"
    return {
        "freshness": overall,
        "source": "persisted_current_context",
        "term_as_of": _iso(term_as_of),
        "iv_rank": {
            "freshness": iv_freshness,
            "value": iv_rank.get("value"),
            "as_of": _iso(iv_as_of),
            "vendor_semantics": iv_rank.get("vendor_semantics", "UNVERIFIED"),
            "classification": None,
            "core_eligibility": iv_rank.get("core_eligibility"),
        },
        "active_expiry_terms": active_terms,
    }


def _dealer_gex_context(
    session: Session,
    *,
    ticker: str,
    price: dict[str, Any],
    as_of: datetime,
    config: Phase2bContextConfig,
) -> dict[str, Any]:
    archived = best_archived_surface_at_or_before(session, ticker=ticker, as_of=as_of)
    if archived is None:
        return _unavailable_block("NO_ELIGIBLE_PERSISTED_GEX_ARCHIVE")
    snapshot, payload = archived
    source_as_of = snapshot.vendor_observed_at or snapshot.captured_at
    freshness = freshness_state(
        source_as_of,
        as_of=as_of,
        max_age_minutes=config.heatmap_freshness_minutes,
    )
    active_expirations = sorted(
        {
            parsed
            for row in payload.get("cells", [])
            if isinstance(row, dict)
            and (parsed := _date(row.get("expiration"))) is not None
            and expiration_is_active(parsed, as_of=as_of)
        }
    )
    reference_price = _number(price.get("value_usd"))
    relative_payload = {**payload, "spot_usd": reference_price}
    expiry_contexts = {
        expiration.isoformat(): dealer_gex_context_for_expiry(
            relative_payload, expiration=expiration
        )
        for expiration in active_expirations
    }
    return {
        "freshness": freshness,
        "source": "DEALER_GEX_ARCHIVE",
        "archive_snapshot_id": str(snapshot.id),
        "as_of": _iso(source_as_of),
        "captured_at": _iso(snapshot.captured_at),
        "availability": snapshot.availability,
        "vendor_snapshot_spot_usd": _number(snapshot.spot_usd),
        "vendor_snapshot_spot_semantic": "HISTORICAL_SOURCE_METADATA",
        "relative_price_context_label": price.get("label"),
        "relative_price_usd": reference_price,
        "active_expiry_contexts": expiry_contexts,
        "sign_disclosure": "GEX sign is not equivalent to bullish/bearish direction.",
    }


def _price_relationship(
    anomaly: dict[str, Any],
    *,
    price: dict[str, Any],
    context: ProductCandidateContext | None,
    config: Phase2bContextConfig,
) -> dict[str, Any]:
    strike = _number(anomaly.get("strike"))
    current_price = _number(price.get("value_usd"))
    if strike is None or current_price is None:
        return _unavailable_block("STRIKE_OR_REFERENCE_PRICE_UNAVAILABLE")
    history = _record(_record(context.price_context).get("history")) if context else {}
    relation = strike_location(
        strike=strike,
        current_price=current_price,
        atr14=_number(history.get("atr_14")),
        tolerance_pct=config.at_spot_tolerance_pct,
    )
    return {
        **relation,
        "price_context_label": price.get("label"),
        "price_context_freshness": price.get("freshness"),
        "reference_price_usd": current_price,
    }


def _context_source_time(
    context: ProductCandidateContext, source: str, fallback: Any = None
) -> datetime | None:
    provenance = _record(context.provenance)
    sources = _record(provenance.get("sources"))
    entry = _record(sources.get(source))
    for key in (
        "freshness_anchor_at",
        "vendor_observed_at",
        "local_captured_at",
        "source_first_received_at",
    ):
        parsed = _datetime(entry.get(key))
        if parsed is not None:
            return parsed
    return _datetime(fallback)


def _unavailable_population() -> dict[str, Any]:
    return {
        "state": "UNAVAILABLE",
        "freshness": "UNAVAILABLE",
        "freshness_reason": "NO_SUCCESSFUL_MATERIALIZED_CANDIDATE_POPULATION",
        "market_date": None,
        "scan_run_id": None,
        "started_at": None,
        "completed_at": None,
        "candidate_materialized_at": None,
        "candidate_count": 0,
    }


def _unavailable_block(reason: str) -> dict[str, Any]:
    return {"freshness": "UNAVAILABLE", "reason": reason}


def _record(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return ensure_utc(value)
    if not isinstance(value, str):
        return None
    try:
        return ensure_utc(datetime.fromisoformat(value.replace("Z", "+00:00")))
    except ValueError:
        return None


def _date(value: Any) -> date | None:
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _iso(value: datetime | None) -> str | None:
    return ensure_utc(value).isoformat() if value is not None else None
