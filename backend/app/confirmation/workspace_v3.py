from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date
from typing import Any, Final

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.db.models import (
    ContractScanObservation,
    DealerGexSnapshot,
    Phase2bCandidateEvaluation,
    Phase2bCandidateState,
    Phase2bTickerContextSnapshot,
    Phase2bV3ResearchWorkspace,
)
from app.dealer_archive.repository import best_archived_surface_at_or_before

PHASE2B_V3_SPEC_VERSION: Final = "signal_spec_v3.1_phase2b"
PRIMARY_FLOOR_RULE_VERSION: Final = "dealer_gex_primary_floor_v1"
PRIMARY_UPPER_NODE_RULE_VERSION: Final = "dealer_gex_primary_upper_node_v1"
BELOW_FLOOR_PATH_RULE_VERSION: Final = "dealer_gex_below_floor_path_v1"
ADJACENT_EXPIRY_RULE_VERSION: Final = "dealer_gex_adjacent_expiry_context_v1"
WORKSPACE_CONFIG_VERSION: Final = "phase2b_v31_research_workspace_v2"
USABLE_DEALER_QUALITIES: Final = frozenset({"AVAILABLE", "AVAILABLE_DEGRADED"})


def _number(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _date_text(value: Any) -> str | None:
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        try:
            return date.fromisoformat(value[:10]).isoformat()
        except ValueError:
            return None
    return None


def _workspace_config() -> dict[str, Any]:
    return {
        "version": WORKSPACE_CONFIG_VERSION,
        "usable_dealer_qualities": sorted(USABLE_DEALER_QUALITIES),
        "adjacent_expiry_limit": {"previous": 1, "next": 1},
        "nearby_lower_node_limit": 5,
        "economic_scores_added": False,
        "trade_recommendations_added": False,
        "rule_versions": {
            "primary_floor": PRIMARY_FLOOR_RULE_VERSION,
            "primary_upper_node": PRIMARY_UPPER_NODE_RULE_VERSION,
            "below_floor_path": BELOW_FLOOR_PATH_RULE_VERSION,
            "adjacent_expiry": ADJACENT_EXPIRY_RULE_VERSION,
        },
    }


def workspace_config_hash() -> str:
    payload = json.dumps(_workspace_config(), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def _normalized_cells(heatmap: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    cells = heatmap.get("cells")
    if not isinstance(cells, list):
        return result
    for source in cells:
        if not isinstance(source, dict):
            continue
        expiration = _date_text(source.get("expiration"))
        strike = _number(source.get("strike_usd"))
        net = _number(source.get("net_dealer_gex_usd"))
        if expiration is None or strike is None or net is None:
            continue
        result.append(
            {
                "expiration": expiration,
                "strike_usd": strike,
                "net_dealer_gex_usd": net,
                "call_gex_usd": _number(source.get("call_gex_usd")),
                "put_gex_usd": _number(source.get("put_gex_usd")),
            }
        )
    return result


def _node(cell: dict[str, Any], *, spot: float | None = None) -> dict[str, Any]:
    strike = float(cell["strike_usd"])
    net = float(cell["net_dealer_gex_usd"])
    return {
        **cell,
        "sign": "POSITIVE" if net > 0 else "NEGATIVE" if net < 0 else "ZERO",
        "distance_from_spot_usd": strike - spot if spot is not None else None,
    }


def _empty_dealer_structure(
    *, anchor_expiration: str, source_quality: str, reason: str,
    source_timestamp: Any = None,
) -> dict[str, Any]:
    return {
        "availability": "DATA_UNAVAILABLE",
        "availability_reason": reason,
        "source_quality": source_quality,
        "source_timestamp": source_timestamp,
        "anchor_expiry": anchor_expiration,
        "spot_usd": None,
        "primary_floor": None,
        "floor_state": "NO_POSITIVE_FLOOR_IDENTIFIED",
        "primary_upper_positive_gex_node": None,
        "upper_node_state": "NO_POSITIVE_UPPER_NODE_IDENTIFIED",
        "immediate_below_floor_node": None,
        "below_floor_structure": "UNAVAILABLE",
        "floor_hold_condition": "UNAVAILABLE",
        "floor_break_condition": "UNAVAILABLE",
        "adjacent_expiry_context": {
            "state": "UNAVAILABLE", "previous": None, "anchor": None, "next": None,
        },
        "nearby_lower_nodes": [],
        "audit": {
            "primary_floor": {"rule_version": PRIMARY_FLOOR_RULE_VERSION},
            "primary_upper_node": {"rule_version": PRIMARY_UPPER_NODE_RULE_VERSION},
            "below_floor_path": {"rule_version": BELOW_FLOOR_PATH_RULE_VERSION},
            "adjacent_expiry": {"rule_version": ADJACENT_EXPIRY_RULE_VERSION},
            "specification_version": PHASE2B_V3_SPEC_VERSION,
        },
    }


def _adjacent_context(
    cells: list[dict[str, Any]], *, anchor_expiration: str,
    floor: dict[str, Any] | None,
) -> dict[str, Any]:
    expirations = sorted({cell["expiration"] for cell in cells})
    previous_expiry = max(
        (item for item in expirations if item < anchor_expiration), default=None
    )
    next_expiry = min(
        (item for item in expirations if item > anchor_expiration), default=None
    )
    floor_strike = floor.get("strike_usd") if floor else None

    def evidence(expiration: str | None) -> dict[str, Any] | None:
        if expiration is None:
            return None
        match = next(
            (
                cell for cell in cells
                if cell["expiration"] == expiration
                and floor_strike is not None
                and cell["strike_usd"] == floor_strike
            ),
            None,
        )
        if match is None:
            return {
                "expiration": expiration,
                "strike_usd": floor_strike,
                "net_dealer_gex_usd": None,
                "sign": "NOT_PRESENT",
            }
        return _node(match)

    previous = evidence(previous_expiry)
    next_node = evidence(next_expiry)
    anchor = _node(floor) if floor is not None else None
    usable = [
        item for item in (previous, next_node)
        if item is not None and _number(item.get("net_dealer_gex_usd")) is not None
    ]
    if floor is None or not usable:
        state = "UNAVAILABLE"
    elif len(usable) == 2:
        positive = [float(item["net_dealer_gex_usd"]) > 0 for item in usable]
        if all(positive):
            state = "ALIGNED"
        elif any(positive):
            state = "MIXED"
        else:
            state = "NOT_ALIGNED"
    elif float(usable[0]["net_dealer_gex_usd"]) > 0:
        state = "PARTIALLY_ALIGNED"
    else:
        state = "NOT_ALIGNED"
    return {
        "state": state,
        "previous": previous,
        "anchor": anchor,
        "next": next_node,
        "rule_version": ADJACENT_EXPIRY_RULE_VERSION,
        "scope": "NEAREST_PREVIOUS_ANCHOR_NEAREST_NEXT_ONLY",
    }


def build_dealer_gex_structure(
    heatmap: dict[str, Any], *, anchor_expiration: date | str, spot: Any = None,
) -> dict[str, Any]:
    """Derive a threshold-free anchor-expiry GEX structure from normalized cells."""
    anchor = _date_text(anchor_expiration)
    if anchor is None:
        raise ValueError("anchor_expiration must be an ISO date")
    quality = str(heatmap.get("availability") or "UNAVAILABLE")
    source_timestamp = heatmap.get("generated_at") or heatmap.get("capture_timestamp")
    if quality not in USABLE_DEALER_QUALITIES:
        return _empty_dealer_structure(
            anchor_expiration=anchor,
            source_quality=quality,
            reason="DEALER_SOURCE_NOT_USABLE",
            source_timestamp=source_timestamp,
        )
    spot_value = _number(spot)
    if spot_value is None:
        spot_value = _number(heatmap.get("spot_usd"))
    if spot_value is None:
        return _empty_dealer_structure(
            anchor_expiration=anchor,
            source_quality=quality,
            reason="SPOT_NOT_AVAILABLE",
            source_timestamp=source_timestamp,
        )
    cells = _normalized_cells(heatmap)
    anchor_cells = sorted(
        (cell for cell in cells if cell["expiration"] == anchor),
        key=lambda item: item["strike_usd"],
    )
    if not anchor_cells:
        return _empty_dealer_structure(
            anchor_expiration=anchor,
            source_quality=quality,
            reason="ANCHOR_EXPIRY_LADDER_NOT_AVAILABLE",
            source_timestamp=source_timestamp,
        )

    positive_below = [
        cell for cell in anchor_cells
        if cell["strike_usd"] < spot_value and cell["net_dealer_gex_usd"] > 0
    ]
    positive_above = [
        cell for cell in anchor_cells
        if cell["strike_usd"] > spot_value and cell["net_dealer_gex_usd"] > 0
    ]
    floor_cell = max(
        positive_below,
        key=lambda item: (item["net_dealer_gex_usd"], item["strike_usd"]),
        default=None,
    )
    upper_cell = max(
        positive_above,
        key=lambda item: (item["net_dealer_gex_usd"], -item["strike_usd"]),
        default=None,
    )
    floor = _node(floor_cell, spot=spot_value) if floor_cell else None
    upper = _node(upper_cell, spot=spot_value) if upper_cell else None
    lower_cells = (
        [cell for cell in anchor_cells if cell["strike_usd"] < floor["strike_usd"]]
        if floor else []
    )
    immediate_cell = max(lower_cells, key=lambda item: item["strike_usd"], default=None)
    immediate = _node(immediate_cell, spot=spot_value) if immediate_cell else None
    if immediate is not None and floor is not None:
        immediate["distance_from_floor_usd"] = (
            immediate["strike_usd"] - floor["strike_usd"]
        )
    risk_present = bool(
        floor is not None
        and immediate is not None
        and immediate["net_dealer_gex_usd"] < 0
    )
    nearby_lower = [
        _node(cell, spot=spot_value)
        for cell in sorted(lower_cells, key=lambda item: item["strike_usd"], reverse=True)[:5]
    ]
    adjacent = _adjacent_context(cells, anchor_expiration=anchor, floor=floor_cell)
    return {
        "availability": "AVAILABLE",
        "availability_reason": heatmap.get("availability_reason"),
        "source_quality": quality,
        "source_timestamp": source_timestamp,
        "anchor_expiry": anchor,
        "spot_usd": spot_value,
        "anchor_ladder_usable_cell_count": len(anchor_cells),
        "primary_floor": floor,
        "floor_state": (
            "PRIMARY_FLOOR_IDENTIFIED" if floor else "NO_POSITIVE_FLOOR_IDENTIFIED"
        ),
        "primary_upper_positive_gex_node": upper,
        "upper_node_state": (
            "PRIMARY_UPPER_NODE_IDENTIFIED"
            if upper else "NO_POSITIVE_UPPER_NODE_IDENTIFIED"
        ),
        "immediate_below_floor_node": immediate,
        "below_floor_structure": (
            "NEGATIVE_GEX_IMMEDIATELY_BELOW"
            if risk_present else "NOT_IDENTIFIED" if floor else "UNAVAILABLE"
        ),
        "floor_hold_condition": (
            "STABILIZATION_BIAS" if floor and spot_value > floor["strike_usd"] else "UNAVAILABLE"
        ),
        "floor_break_condition": (
            "DOWNSIDE_ACCELERATION_RISK"
            if risk_present else "NOT_IDENTIFIED" if floor else "UNAVAILABLE"
        ),
        "adjacent_expiry_context": adjacent,
        "nearby_lower_nodes": nearby_lower,
        "audit": {
            "primary_floor": {
                "rule": "MAXIMUM_POSITIVE_NET_GEX_STRICTLY_BELOW_SPOT_ON_ANCHOR_EXPIRY",
                "rule_version": PRIMARY_FLOOR_RULE_VERSION,
                "positive_nodes_below_spot": [
                    _node(cell, spot=spot_value) for cell in positive_below
                ],
            },
            "primary_upper_node": {
                "rule": "MAXIMUM_POSITIVE_NET_GEX_STRICTLY_ABOVE_SPOT_ON_ANCHOR_EXPIRY",
                "rule_version": PRIMARY_UPPER_NODE_RULE_VERSION,
                "positive_nodes_above_spot_count": len(positive_above),
            },
            "below_floor_path": {
                "rule": "IMMEDIATE_LOWER_STRIKE_NEGATIVE_NET_GEX",
                "rule_version": BELOW_FLOOR_PATH_RULE_VERSION,
                "sign_transition": (
                    f"POSITIVE_TO_{immediate['sign']}" if immediate else None
                ),
            },
            "adjacent_expiry": {
                "rule": "NEAREST_PREVIOUS_AND_NEXT_AT_PRIMARY_FLOOR_STRIKE",
                "rule_version": ADJACENT_EXPIRY_RULE_VERSION,
            },
            "source_quality": quality,
            "source_timestamp": source_timestamp,
            "specification_version": PHASE2B_V3_SPEC_VERSION,
        },
    }


def _price_audit(price: dict[str, Any]) -> dict[str, Any]:
    close = _number(price.get("latest_regular_close_usd"))
    sma20 = _number(price.get("sma_20"))
    sma50 = _number(price.get("sma_50"))
    return {
        "accepted_state": price.get("trend", "UNKNOWN"),
        "rule": "REUSE_ACCEPTED_PHASE2B_PRICE_TREND_NO_TRADE_RECOMMENDATION",
        "source_fields": {
            "latest_regular_close_usd": close,
            "sma_20": sma20,
            "sma_50": sma50,
            "close_gt_sma20": close > sma20 if close is not None and sma20 is not None else None,
            "sma20_gt_sma50": sma20 > sma50 if sma20 is not None and sma50 is not None else None,
        },
        "interpretation": "UNDERLYING_PRICE_STRUCTURE_CONTEXT_ONLY",
    }


def build_workspace_payload(
    evaluation: Phase2bCandidateEvaluation,
    context: Phase2bTickerContextSnapshot,
    state: Phase2bCandidateState,
    *,
    contract: ContractScanObservation | None = None,
    dealer_heatmap: dict[str, Any] | None = None,
    dealer_archive_snapshot: DealerGexSnapshot | None = None,
) -> dict[str, Any]:
    phase2a = evaluation.phase2a_evidence or {}
    positioning = state.positioning_state or {}
    execution = state.execution_state or {}
    price = dict(state.price_state or {})
    price["audit"] = _price_audit(price)
    volatility = dict(state.volatility_state or {})
    volatility["semantics"] = "FACTUAL_VOLATILITY_CONTEXT_NOT_DIRECTION_OR_RECOMMENDATION"
    dealer_source = dealer_heatmap if dealer_heatmap is not None else context.dealer_heatmap
    spot = dealer_source.get("spot_usd") if dealer_source else None
    if spot is None:
        spot = context.stock_state.get("current_price_usd") if context.stock_state else None
    dealer = build_dealer_gex_structure(
        dealer_source or {},
        anchor_expiration=evaluation.expiration,
        spot=spot,
    )
    contract_identity = {
        "ticker": evaluation.ticker,
        "contract_symbol": evaluation.contract_symbol,
        "expiration": evaluation.expiration.isoformat(),
        "right": evaluation.right,
        "right_label": "Call" if evaluation.right == "C" else "Put",
        "strike": _number(evaluation.strike),
        "dte_at_detection": evaluation.dte_at_detection,
        "bucket_at_detection": contract.bucket_at_detection if contract else None,
        "entity_type": "CONTRACT",
    }
    opportunity = {
        "contract_activity": {
            "premium_activity_usd": phase2a.get("premium_usd"),
            "volume": phase2a.get("volume"),
            "trades": phase2a.get("trades"),
            "radar_observation_date": phase2a.get("radar_observation_date"),
            "semantics": (
                "VENDOR_REPORTED_AGGREGATE_EXACT_CONTRACT_ACTIVITY;_NOT_ONE_ORDER;_"
                "BUYER_SELLER_OPENING_AND_DIRECTION_UNRESOLVED"
            ),
        },
        "open_interest": {
            "delta_oi": phase2a.get("oi_diff"),
            "relative_oi_change": phase2a.get("relative_oi_change"),
            "current_oi": execution.get("open_interest"),
            "radar_observation_date": phase2a.get("radar_observation_date"),
            "chain_observation_date": evaluation.source_timestamps.get("chain"),
            "chain_quote_as_of": evaluation.source_timestamps.get("chain_quote"),
            "semantics": (
                "POSITIVE_DELTA_OI_IS_NET_OI_INCREASE;_NOT_BOUGHT_CONTRACTS_OR_DIRECTION"
            ),
        },
        "positioning_evidence": positioning,
        "observed_flow_direction": {
            "state": "UNRESOLVED",
            "reason": (
                "EVIDENCE_DOES_NOT_ESTABLISH_BUYER_OR_SELLER_INITIATION_OPENING_OR_CLOSING_"
                "INTENT_SPREAD_HEDGE_OR_OTHER_MULTI_LEG_STRUCTURE"
            ),
            "interpretation": "PROVENANCE_WARNING_NOT_NEUTRAL",
            "audit": {
                "source_candidate_evaluation_id": str(evaluation.id),
                "source_direction": evaluation.direction,
            },
        },
    }
    raw_payload_ids = list(context.raw_payload_ids or [])
    source_request_ids = list(context.source_request_ids or [])
    if dealer_archive_snapshot and dealer_archive_snapshot.raw_payload_id:
        raw_payload_ids.append(str(dealer_archive_snapshot.raw_payload_id))
    if dealer_archive_snapshot and dealer_archive_snapshot.source_request_id:
        source_request_ids.append(dealer_archive_snapshot.source_request_id)
    source_timestamps = {
        **(context.source_timestamps or {}),
        **(evaluation.source_timestamps or {}),
    }
    if dealer_archive_snapshot:
        source_timestamps.update(
            {
                "dealer_gex_archive_vendor_observed_at": (
                    dealer_archive_snapshot.vendor_observed_at.isoformat()
                    if dealer_archive_snapshot.vendor_observed_at
                    else None
                ),
                "dealer_gex_archive_captured_at": (
                    dealer_archive_snapshot.captured_at.isoformat()
                ),
            }
        )
    provenance = {
        "source_v2_state_id": str(state.id),
        "candidate_evaluation_id": str(evaluation.id),
        "ticker_context_id": str(context.id),
        "contract_observation_id": str(contract.id) if contract else None,
        "dealer_snapshot_reference": (
            str(dealer_archive_snapshot.id) if dealer_archive_snapshot else str(context.id)
        ),
        "dealer_snapshot_source": (
            "DEALER_GEX_ARCHIVE"
            if dealer_archive_snapshot
            else "PHASE2B_TICKER_CONTEXT"
        ),
        "dealer_snapshot_source_time_eligible": (
            dealer_archive_snapshot.captured_at <= evaluation.evaluated_at
            and dealer_archive_snapshot.vendor_observed_at is not None
            and dealer_archive_snapshot.vendor_observed_at <= evaluation.evaluated_at
            if dealer_archive_snapshot
            else True
        ),
        "raw_payload_ids": list(dict.fromkeys(raw_payload_ids)),
        "source_request_ids": list(dict.fromkeys(source_request_ids)),
        "source_timestamps": source_timestamps,
        "source_context_specification_version": evaluation.specification_version,
        "source_v2_specification_version": state.specification_version,
    }
    return {
        "specification_version": PHASE2B_V3_SPEC_VERSION,
        "contract_identity": contract_identity,
        "opportunity_positioning": opportunity,
        "underlying_price": price,
        "trade_structure": {
            "volatility": volatility,
            "dealer_gex": dealer,
            "execution": execution,
        },
        "provenance": provenance,
        "rule_versions": {
            "primary_floor": PRIMARY_FLOOR_RULE_VERSION,
            "primary_upper_node": PRIMARY_UPPER_NODE_RULE_VERSION,
            "below_floor_path": BELOW_FLOOR_PATH_RULE_VERSION,
            "adjacent_expiry": ADJACENT_EXPIRY_RULE_VERSION,
        },
        "config_version": WORKSPACE_CONFIG_VERSION,
        "config_hash": workspace_config_hash(),
    }


@dataclass(frozen=True)
class WorkspaceBuildSummary:
    created: int
    reused: int
    missing: tuple[str, ...]
    workspace_ids: tuple[str, ...]


class Phase2bV3WorkspaceService:
    """Materialize v3 workspaces solely from preserved database evidence."""

    def __init__(self, session: Session):
        self.session = session

    def materialize_contracts(self, symbols: list[str]) -> WorkspaceBuildSummary:
        created = 0
        reused = 0
        missing: list[str] = []
        workspace_ids: list[str] = []
        for symbol in dict.fromkeys(symbols):
            evaluation = self.session.scalar(
                select(Phase2bCandidateEvaluation)
                .where(Phase2bCandidateEvaluation.contract_symbol == symbol)
                .order_by(desc(Phase2bCandidateEvaluation.evaluated_at)).limit(1)
            )
            if evaluation is None:
                missing.append(symbol)
                continue
            state = self.session.scalar(
                select(Phase2bCandidateState).where(
                    Phase2bCandidateState.candidate_evaluation_id == evaluation.id
                ).order_by(desc(Phase2bCandidateState.evaluated_at)).limit(1)
            )
            if state is None:
                missing.append(symbol)
                continue
            existing = self.session.scalar(
                select(Phase2bV3ResearchWorkspace).where(
                    Phase2bV3ResearchWorkspace.source_v2_state_id == state.id,
                    Phase2bV3ResearchWorkspace.specification_version
                    == PHASE2B_V3_SPEC_VERSION,
                )
            )
            if existing is not None:
                reused += 1
                workspace_ids.append(str(existing.id))
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
            archived = best_archived_surface_at_or_before(
                self.session,
                ticker=evaluation.ticker,
                as_of=evaluation.evaluated_at,
            )
            archive_snapshot, archive_heatmap = archived if archived else (None, None)
            payload = build_workspace_payload(
                evaluation,
                context,
                state,
                contract=contract,
                dealer_heatmap=archive_heatmap,
                dealer_archive_snapshot=archive_snapshot,
            )
            row = Phase2bV3ResearchWorkspace(
                source_v2_state_id=state.id,
                candidate_evaluation_id=evaluation.id,
                ticker_context_id=context.id,
                contract_symbol=evaluation.contract_symbol,
                ticker=evaluation.ticker,
                created_at=utc_now(),
                contract_identity=payload["contract_identity"],
                opportunity_positioning=payload["opportunity_positioning"],
                underlying_price=payload["underlying_price"],
                volatility_context=payload["trade_structure"]["volatility"],
                dealer_gex_structure=payload["trade_structure"]["dealer_gex"],
                execution_context=payload["trade_structure"]["execution"],
                provenance=payload["provenance"],
                specification_version=PHASE2B_V3_SPEC_VERSION,
                config_version=WORKSPACE_CONFIG_VERSION,
                config_hash=workspace_config_hash(),
                primary_floor_rule_version=PRIMARY_FLOOR_RULE_VERSION,
                primary_upper_node_rule_version=PRIMARY_UPPER_NODE_RULE_VERSION,
                below_floor_path_rule_version=BELOW_FLOOR_PATH_RULE_VERSION,
                adjacent_expiry_rule_version=ADJACENT_EXPIRY_RULE_VERSION,
            )
            self.session.add(row)
            self.session.flush()
            created += 1
            workspace_ids.append(str(row.id))
        if created:
            self.session.commit()
        return WorkspaceBuildSummary(
            created, reused, tuple(missing), tuple(workspace_ids)
        )


def latest_v3_workspace(
    session: Session,
    contract_symbol: str,
    *,
    candidate_evaluation_id: Any = None,
) -> dict[str, Any] | None:
    statement = select(Phase2bV3ResearchWorkspace).where(
        Phase2bV3ResearchWorkspace.contract_symbol == contract_symbol
    )
    if candidate_evaluation_id is not None:
        statement = statement.where(
            Phase2bV3ResearchWorkspace.candidate_evaluation_id
            == candidate_evaluation_id
        )
    row = session.scalar(statement.order_by(desc(Phase2bV3ResearchWorkspace.created_at)).limit(1))
    if row is None:
        return None
    return {
        "specification_version": row.specification_version,
        "contract_identity": row.contract_identity,
        "opportunity_positioning": row.opportunity_positioning,
        "underlying_price": row.underlying_price,
        "trade_structure": {
            "volatility": row.volatility_context,
            "dealer_gex": row.dealer_gex_structure,
            "execution": row.execution_context,
        },
        "provenance": row.provenance,
        "rule_versions": {
            "primary_floor": row.primary_floor_rule_version,
            "primary_upper_node": row.primary_upper_node_rule_version,
            "below_floor_path": row.below_floor_path_rule_version,
            "adjacent_expiry": row.adjacent_expiry_rule_version,
        },
        "config_version": row.config_version,
        "config_hash": row.config_hash,
        "created_at": row.created_at.isoformat(),
    }
