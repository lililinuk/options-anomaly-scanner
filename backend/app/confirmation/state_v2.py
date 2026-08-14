from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Final

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.db.models import (
    ContractScanObservation,
    ExpiryObservation,
    Phase2bCandidateEvaluation,
    Phase2bCandidateState,
    Phase2bTickerContextSnapshot,
    StrikeCluster,
)

PHASE2B_V2_SPEC_VERSION: Final = "signal_spec_v2.0_phase2b"
TOPOLOGY_RULE_VERSION: Final = "phase2b_term_topology_v1"
READINESS_RULE_VERSION: Final = "phase2b_research_readiness_v1"
EQUALITY_TOLERANCE: Final = 1e-12
STATE_CONFIG_VERSION: Final = "phase2b_v2_state_config_v1"


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _state_config() -> dict[str, Any]:
    return {
        "version": STATE_CONFIG_VERSION,
        "equality_tolerance": EQUALITY_TOLERANCE,
        "topology_rule_version": TOPOLOGY_RULE_VERSION,
        "readiness_rule_version": READINESS_RULE_VERSION,
        "economic_thresholds_added": False,
    }


def state_config_hash() -> str:
    encoded = json.dumps(_state_config(), sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def classify_term_topology(
    shorter_iv: Any, candidate_iv: Any, longer_iv: Any,
    *, tolerance: float = EQUALITY_TOLERANCE,
) -> str:
    shorter = _number(shorter_iv)
    candidate = _number(candidate_iv)
    longer = _number(longer_iv)
    if shorter is None or candidate is None or longer is None:
        return "INCOMPLETE"
    if abs(candidate - shorter) <= tolerance or abs(candidate - longer) <= tolerance:
        return "FLAT_OR_EQUAL"
    if candidate > shorter and candidate > longer:
        return "LOCAL_PEAK"
    if candidate < shorter and candidate < longer:
        return "LOCAL_TROUGH"
    if shorter < candidate < longer:
        return "RISING_THROUGH_CANDIDATE"
    if shorter > candidate > longer:
        return "FALLING_THROUGH_CANDIDATE"
    return "FLAT_OR_EQUAL"


def build_volatility_state(
    iv_rank: dict[str, Any], term: dict[str, Any]
) -> dict[str, Any]:
    candidate = term.get("candidate_node") if isinstance(term.get("candidate_node"), dict) else {}
    shorter = (
        term.get("nearest_shorter_node")
        if isinstance(term.get("nearest_shorter_node"), dict)
        else {}
    )
    longer = (
        term.get("nearest_longer_node")
        if isinstance(term.get("nearest_longer_node"), dict)
        else {}
    )
    candidate_iv = _number(term.get("candidate_term_iv"))
    shorter_iv = _number(shorter.get("implied_vol_pct"))
    longer_iv = _number(longer.get("implied_vol_pct"))
    topology = classify_term_topology(shorter_iv, candidate_iv, longer_iv)
    neighbor_mean = (
        (shorter_iv + longer_iv) / 2
        if shorter_iv is not None and longer_iv is not None
        else None
    )
    return {
        "iv_rank": _number(iv_rank.get("value")),
        "iv_rank_vendor_date": iv_rank.get("vendor_date"),
        "iv_rank_as_of": iv_rank.get("as_of"),
        "term_availability": term.get("availability", "UNAVAILABLE"),
        "exact_match_status": term.get("exact_match_status", "NOT_PRESENT"),
        "topology": topology,
        "candidate_iv": candidate_iv,
        "shorter_iv": shorter_iv,
        "longer_iv": longer_iv,
        "candidate_iv_minus_shorter": term.get("candidate_iv_minus_shorter"),
        "candidate_iv_minus_longer": term.get("candidate_iv_minus_longer"),
        "candidate_iv_minus_neighbor_mean": (
            candidate_iv - neighbor_mean
            if candidate_iv is not None and neighbor_mean is not None
            else None
        ),
        "neighbor_mean_iv": neighbor_mean,
        "candidate_expiration": candidate.get("expiry"),
        "shorter_expiration": shorter.get("expiry"),
        "longer_expiration": longer.get("expiry"),
        "implied_move_usd": candidate.get("implied_move_usd"),
        "implied_move_pct": candidate.get("implied_move_pct"),
        "term_vendor_date": term.get("vendor_date"),
        "term_as_of": term.get("as_of"),
        "topology_rule_version": TOPOLOGY_RULE_VERSION,
        "equality_tolerance": EQUALITY_TOLERANCE,
    }


def classify_gex_sign(dealer: dict[str, Any]) -> str:
    if dealer.get("candidate_heatmap_cell_status") != "EXACT_MATCH":
        return "UNKNOWN"
    value = _number(dealer.get("candidate_net_gex_usd"))
    if value is None and isinstance(dealer.get("candidate_cell"), dict):
        value = _number(dealer["candidate_cell"].get("net_dealer_gex_usd"))
    if value is None:
        return "UNKNOWN"
    if value > 0:
        return "POSITIVE_NET_GEX"
    if value < 0:
        return "NEGATIVE_NET_GEX"
    return "ZERO_NET_GEX"


def build_dealer_state(dealer: dict[str, Any]) -> dict[str, Any]:
    cell = dealer.get("candidate_cell") if isinstance(dealer.get("candidate_cell"), dict) else {}

    def candidate_value(flat_key: str, cell_key: str) -> Any:
        value = dealer.get(flat_key)
        return value if value is not None else cell.get(cell_key)

    return {
        "sign": classify_gex_sign(dealer),
        "source_quality": dealer.get("quality", dealer.get("availability", "UNAVAILABLE")),
        "candidate_cell_status": dealer.get("candidate_heatmap_cell_status", "UNAVAILABLE"),
        "row_stack_status": dealer.get("row_stack_status", "ROW_UNAVAILABLE"),
        "candidate_net_gex_usd": candidate_value(
            "candidate_net_gex_usd", "net_dealer_gex_usd"
        ),
        "candidate_call_gex_usd": candidate_value(
            "candidate_call_gex_usd", "call_gex_usd"
        ),
        "candidate_put_gex_usd": candidate_value(
            "candidate_put_gex_usd", "put_gex_usd"
        ),
        "row_net_gex_usd": dealer.get("row_net_gex_usd"),
        "row_abs_gex_usd": dealer.get("row_abs_gex_usd"),
        "vendor_row_rank": dealer.get("vendor_row_rank"),
        "generated_at": dealer.get("generated_at"),
        "session_date_et": dealer.get("session_date_et"),
        "truncated": dealer.get("truncated"),
        "availability_reason": dealer.get("availability_reason"),
    }


def _persistence_presence(score: Any, confidence: Any, count: Any) -> str:
    if _number(score) is not None:
        return "PRESENT"
    numeric_count = _number(count)
    if confidence in {None, "INSUFFICIENT", "LOW"} and (
        numeric_count is None or numeric_count < 3
    ):
        return "NOT_YET_AVAILABLE"
    return "ABSENT"


def build_positioning_state(
    phase2a: dict[str, Any], *, trigger_sources: list[str],
    contract_history_confidence: Any = None, contract_history_count: Any = None,
    expiry_history_confidence: Any = None, expiry_history_count: Any = None,
    exact_cluster_membership: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    clusters = exact_cluster_membership or []
    radar_present = bool(
        phase2a.get("radar_material_event") is True or "RADAR_EVENT" in trigger_sources
    )
    states = {
        "radar_event": "RADAR_EVENT_PRESENT" if radar_present else "RADAR_EVENT_ABSENT",
        "contract_persistence": "CONTRACT_PERSISTENCE_" + _persistence_presence(
            phase2a.get("contract_persistence"),
            contract_history_confidence,
            contract_history_count,
        ),
        "expiry_persistence": "EXPIRY_PERSISTENCE_" + _persistence_presence(
            phase2a.get("expiry_persistence"), expiry_history_confidence, expiry_history_count
        ),
        "structure": (
            "STRUCTURE_PRESENT"
            if _number(phase2a.get("structure_score")) is not None
            else "STRUCTURE_ABSENT"
        ),
        "cluster": "CLUSTER_PRESENT" if clusters else "CLUSTER_ABSENT",
    }
    present = [
        family
        for family, state in states.items()
        if state.endswith("_PRESENT")
    ]
    count = len(present)
    breadth = "SINGLE_EVIDENCE" if count == 1 else "MULTI_EVIDENCE" if count >= 2 else "NO_EVIDENCE"
    return {
        "presence_states": states,
        "evidence_family_count": count,
        "evidence_breadth": breadth,
        "present_evidence_families": present,
        "radar_event": {
            key: phase2a.get(key)
            for key in (
                "radar_material_event", "radar_observation_date", "premium_usd", "oi_diff",
                "relative_oi_change", "volume", "trades", "archive_completeness",
            )
        },
        "contract_persistence_score": phase2a.get("contract_persistence"),
        "expiry_persistence_score": phase2a.get("expiry_persistence"),
        "structure_score": phase2a.get("structure_score"),
        "exact_cluster_membership": clusters,
        "family_count_rule": "EACH_EVIDENCE_FAMILY_COUNTS_AT_MOST_ONCE",
    }


def build_price_state(price: dict[str, Any]) -> dict[str, Any]:
    return {
        "availability": price.get("availability", "UNAVAILABLE"),
        "trend": price.get("trend", "UNKNOWN"),
        "latest_trading_date": price.get("latest_trading_date"),
        "latest_regular_close_usd": price.get("latest_regular_close_usd"),
        "return_1d": price.get("return_1d"),
        "return_5d": price.get("return_5d"),
        "return_20d": price.get("return_20d"),
        "sma_20": price.get("sma_20"),
        "sma_50": price.get("sma_50"),
        "distance_to_sma20_pct": price.get("distance_to_sma20_pct"),
        "distance_to_sma50_pct": price.get("distance_to_sma50_pct"),
        "atr_14": price.get("atr_14"),
        "coverage_quality": price.get("coverage_quality"),
        "price_adjustment_semantics": price.get("price_adjustment_semantics"),
    }


def build_execution_state(
    execution: dict[str, Any], *, contract: ContractScanObservation | None = None
) -> dict[str, Any]:
    result = dict(execution)
    result.update(
        {
            "accepted_liquidity_component": (
                (contract.structure_components or {}).get("liquidity_quality")
                if contract else None
            ),
            "accepted_risk_flags": list(contract.risk_flags or []) if contract else [],
            "accepted_hard_reject_reason": contract.hard_reject_reason if contract else None,
            "threshold_policy": "REUSE_PHASE2A_ACCEPTED_FLAGS_NO_NEW_THRESHOLDS",
        }
    )
    return result


def build_research_readiness(
    positioning: dict[str, Any], price: dict[str, Any], volatility: dict[str, Any],
    dealer: dict[str, Any], execution: dict[str, Any],
) -> dict[str, Any]:
    layers: dict[str, dict[str, Any]] = {}

    def layer(name: str, status: str, reason: str) -> None:
        layers[name] = {"status": status, "reason": reason}

    layer(
        "positioning",
        "READY" if positioning["evidence_family_count"] > 0 else "NOT_READY",
        (
            "PHASE2A_PROVENANCE_PRESENT"
            if positioning["evidence_family_count"] > 0
            else "NO_PHASE2A_POSITIONING_EVIDENCE"
        ),
    )
    price_ready = price.get("availability") in {"AVAILABLE", "AVAILABLE_WITH_GAPS"}
    layer("price", "READY" if price_ready else "NOT_READY", str(price.get("availability")))
    iv_ready = _number(volatility.get("iv_rank")) is not None and bool(
        volatility.get("iv_rank_vendor_date") or volatility.get("iv_rank_as_of")
    )
    layer(
        "iv_rank",
        "READY" if iv_ready else "NOT_READY",
        "VALID_VALUE_AND_AS_OF" if iv_ready else "MISSING_VALUE_OR_AS_OF",
    )
    term_ready = (
        volatility.get("exact_match_status") == "EXACT_MATCH"
        and _number(volatility.get("candidate_iv")) is not None
    )
    layer(
        "candidate_term",
        "READY" if term_ready else "NOT_READY",
        "EXACT_CANDIDATE_NODE" if term_ready else "EXACT_CANDIDATE_NODE_MISSING",
    )
    dealer_exact = (
        dealer.get("candidate_cell_status") == "EXACT_MATCH"
        and dealer.get("sign") != "UNKNOWN"
    )
    dealer_quality = dealer.get("source_quality")
    dealer_ready = dealer_exact and dealer_quality == "AVAILABLE"
    dealer_degraded = dealer_exact and dealer_quality in {
        "AVAILABLE_DEGRADED", "INCOMPLETE_OR_TRUNCATED"
    }
    layer(
        "dealer_gex",
        "READY" if dealer_ready else "DEGRADED" if dealer_degraded else "NOT_READY",
        (
            "EXACT_CELL_COMPLETE_SOURCE"
            if dealer_ready
            else "EXACT_CELL_DEGRADED_SOURCE"
            if dealer_degraded
            else "EXACT_USABLE_CELL_MISSING"
        ),
    )
    execution_ready = (
        execution.get("availability") == "AVAILABLE"
        and _number(execution.get("bid")) is not None
        and _number(execution.get("ask")) is not None
        and _number(execution.get("delta")) is not None
    )
    layer(
        "execution",
        "READY" if execution_ready else "NOT_READY",
        (
            "PHASE2A_EXECUTION_EVIDENCE_PRESENT"
            if execution_ready
            else "EXECUTION_OR_GREEKS_MISSING"
        ),
    )
    missing = [name for name, item in layers.items() if item["status"] != "READY"]
    state = (
        "CONTEXT_COMPLETE"
        if not missing
        else "CONTEXT_PARTIAL"
        if len(missing) == 1
        else "CONTEXT_LIMITED"
    )
    return {
        "state": state,
        "layers": layers,
        "missing_or_degraded_count": len(missing),
        "missing_or_degraded_layers": missing,
        "why": [layers[name]["reason"] for name in missing],
        "rule_version": READINESS_RULE_VERSION,
        "interpretation": "RESEARCH_CONTEXT_COMPLETENESS_NOT_ALPHA_OR_TRADE_QUALITY",
    }


def build_candidate_state(
    evaluation: Phase2bCandidateEvaluation,
    context: Phase2bTickerContextSnapshot,
    *, contract: ContractScanObservation | None = None,
    expiry: ExpiryObservation | None = None,
    exact_clusters: list[StrikeCluster] | None = None,
) -> dict[str, Any]:
    cluster_evidence = [
        {
            "cluster_id": str(row.id), "right": row.right,
            "score": _number(row.cluster_score), "classification": row.classification,
        }
        for row in (exact_clusters or [])
    ]
    positioning = build_positioning_state(
        evaluation.phase2a_evidence,
        trigger_sources=list(evaluation.trigger_sources or []),
        contract_history_confidence=contract.history_confidence if contract else None,
        contract_history_count=contract.history_observation_count if contract else None,
        expiry_history_confidence=expiry.history_confidence if expiry else None,
        expiry_history_count=(
            (expiry.persistent_components or {}).get("history_observation_count")
            if expiry
            else None
        ),
        exact_cluster_membership=cluster_evidence,
    )
    price = build_price_state(context.price_context)
    volatility = build_volatility_state(context.iv_rank, evaluation.volatility_context)
    dealer = build_dealer_state(evaluation.dealer_context)
    execution = build_execution_state(evaluation.execution_context, contract=contract)
    readiness = build_research_readiness(positioning, price, volatility, dealer, execution)
    return {
        "positioning": positioning,
        "price": price,
        "volatility": volatility,
        "dealer_gex": dealer,
        "execution": execution,
        "research_readiness": readiness,
        "direction": "UNRESOLVED",
    }


@dataclass(frozen=True)
class StateBuildSummary:
    created: int
    reused: int
    missing: tuple[str, ...]
    state_ids: tuple[str, ...]


class Phase2bV2StateService:
    """Materialize v2 states solely from preserved database evidence; never contacts a vendor."""

    def __init__(self, session: Session):
        self.session = session

    def materialize_contracts(self, symbols: list[str]) -> StateBuildSummary:
        created = 0
        reused = 0
        missing: list[str] = []
        state_ids: list[str] = []
        for symbol in dict.fromkeys(symbols):
            evaluation = self.session.scalar(
                select(Phase2bCandidateEvaluation)
                .where(Phase2bCandidateEvaluation.contract_symbol == symbol)
                .order_by(desc(Phase2bCandidateEvaluation.evaluated_at)).limit(1)
            )
            if evaluation is None:
                missing.append(symbol)
                continue
            existing = self.session.scalar(
                select(Phase2bCandidateState).where(
                    Phase2bCandidateState.candidate_evaluation_id == evaluation.id,
                    Phase2bCandidateState.specification_version == PHASE2B_V2_SPEC_VERSION,
                )
            )
            if existing is not None:
                reused += 1
                state_ids.append(str(existing.id))
                continue
            context = self.session.get(Phase2bTickerContextSnapshot, evaluation.ticker_context_id)
            if context is None:
                missing.append(symbol)
                continue
            contract = self.session.scalar(
                select(ContractScanObservation)
                .where(ContractScanObservation.contract_symbol == symbol)
                .order_by(desc(ContractScanObservation.observed_at)).limit(1)
            )
            expiry = self.session.scalar(
                select(ExpiryObservation).where(
                    ExpiryObservation.ticker == evaluation.ticker,
                    ExpiryObservation.expiration == evaluation.expiration,
                ).order_by(desc(ExpiryObservation.observed_at)).limit(1)
            )
            clusters = list(self.session.scalars(
                select(StrikeCluster).where(
                    StrikeCluster.ticker == evaluation.ticker,
                    StrikeCluster.expiration == evaluation.expiration,
                    StrikeCluster.right == evaluation.right,
                )
            ))
            exact_clusters = [
                row for row in clusters
                if contract is not None and str(contract.id) in (row.source_contract_ids or [])
            ]
            built = build_candidate_state(
                evaluation, context, contract=contract, expiry=expiry, exact_clusters=exact_clusters
            )
            row = Phase2bCandidateState(
                candidate_evaluation_id=evaluation.id,
                ticker_context_id=context.id,
                contract_symbol=evaluation.contract_symbol,
                ticker=evaluation.ticker,
                evaluated_at=utc_now(),
                positioning_state=built["positioning"],
                price_state=built["price"],
                volatility_state=built["volatility"],
                dealer_gex_state=built["dealer_gex"],
                execution_state=built["execution"],
                research_readiness=built["research_readiness"],
                phase2a_provenance={
                    "candidate_evaluation_id": str(evaluation.id),
                    "ticker_context_id": str(context.id),
                    "contract_observation_id": str(contract.id) if contract else None,
                    "expiry_observation_id": str(expiry.id) if expiry else None,
                    "exact_cluster_ids": [str(item.id) for item in exact_clusters],
                    "trigger_sources": list(evaluation.trigger_sources or []),
                    "source_timestamps": evaluation.source_timestamps,
                },
                direction="UNRESOLVED",
                specification_version=PHASE2B_V2_SPEC_VERSION,
                source_context_specification_version=evaluation.specification_version,
                config_version=STATE_CONFIG_VERSION,
                config_hash=state_config_hash(),
                context_config_version=evaluation.config_version,
                context_config_hash=evaluation.config_hash,
                topology_rule_version=TOPOLOGY_RULE_VERSION,
                readiness_rule_version=READINESS_RULE_VERSION,
            )
            self.session.add(row)
            self.session.flush()
            created += 1
            state_ids.append(str(row.id))
        if created:
            self.session.commit()
        return StateBuildSummary(created, reused, tuple(missing), tuple(state_ids))


def latest_v2_state(
    session: Session,
    contract_symbol: str,
    *,
    candidate_evaluation_id: Any = None,
) -> dict[str, Any] | None:
    statement = select(Phase2bCandidateState).where(
        Phase2bCandidateState.contract_symbol == contract_symbol
    )
    if candidate_evaluation_id is not None:
        statement = statement.where(
            Phase2bCandidateState.candidate_evaluation_id == candidate_evaluation_id
        )
    row = session.scalar(statement.order_by(desc(Phase2bCandidateState.evaluated_at)).limit(1))
    if row is None:
        return None
    return {
        "positioning": row.positioning_state,
        "price": row.price_state,
        "volatility": row.volatility_state,
        "dealer_gex": row.dealer_gex_state,
        "execution": row.execution_state,
        "research_readiness": row.research_readiness,
        "phase2a_provenance": row.phase2a_provenance,
        "direction": row.direction,
        "specification_version": row.specification_version,
        "source_context_specification_version": row.source_context_specification_version,
        "config_version": row.config_version,
        "config_hash": row.config_hash,
        "topology_rule_version": row.topology_rule_version,
        "readiness_rule_version": row.readiness_rule_version,
        "evaluated_at": row.evaluated_at.isoformat(),
    }
