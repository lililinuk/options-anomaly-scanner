import inspect
import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from sqlalchemy import CheckConstraint

from app.confirmation.config import Phase2bContextConfig
from app.confirmation.provenance import (
    CandidateFirstKnowledge,
    EvaluationIdentity,
    aggregate_freshness_anchor_at,
    aggregate_source_first_received_at,
    source_time_entry,
)
from app.confirmation.service import Phase2bContextService
from app.db.models import Phase2bCandidateEvaluation, Phase2bTickerContextSnapshot
from app.ingestion.raw import RawIngestor, parse_vendor_observed_at

UTC = timezone.utc


class RawSession:
    def __init__(self, scalar_values: list[object | None]) -> None:
        self.scalar_values = iter(scalar_values)
        self.added: list[object] = []

    def scalar(self, _statement):  # type: ignore[no-untyped-def]
        return next(self.scalar_values)

    def add(self, row: object) -> None:
        if getattr(row, "id", None) is None:
            row.id = uuid.uuid4()  # type: ignore[attr-defined]
        self.added.append(row)

    def flush(self) -> None:
        return None


def test_source_first_receipt_is_idempotent_and_new_identity_gets_own_receipt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    t0 = datetime(2026, 8, 17, 12, 0, tzinfo=UTC)
    t1 = t0 + timedelta(hours=1)
    session = RawSession([None, None])
    ingestor = RawIngestor(session)  # type: ignore[arg-type]
    times = iter([t0, t1])
    monkeypatch.setattr("app.ingestion.raw.utc_now", lambda: next(times))

    first = ingestor.persist(endpoint="/fixture", request_id="source-1", payload={"v": 1})
    session.scalar_values = iter([first, None])
    repeated = ingestor.persist(endpoint="/fixture", request_id="source-1", payload={"v": 1})
    second = ingestor.persist(endpoint="/fixture", request_id="source-2", payload={"v": 2})

    assert repeated is first
    assert first.received_at == t0
    assert second.received_at == t1
    assert len(session.added) == 2


def test_source_identity_conflict_cannot_replace_preserved_receipt() -> None:
    t0 = datetime(2026, 8, 17, 12, 0, tzinfo=UTC)
    existing = SimpleNamespace(
        endpoint="/fixture",
        payload_sha256="not-the-new-hash",
        ticker=None,
        expiration=None,
        received_at=t0,
    )
    session = RawSession([existing])

    with pytest.raises(ValueError, match="identity conflicts"):
        RawIngestor(session).persist(  # type: ignore[arg-type]
            endpoint="/fixture", request_id="source-1", payload={"changed": True}
        )
    assert existing.received_at == t0
    assert session.added == []


def test_vendor_and_local_times_remain_distinct_without_fallback() -> None:
    received = datetime(2026, 8, 17, 12, 0, tzinfo=UTC)
    vendor = datetime(2026, 8, 17, 11, 45, tzinfo=UTC)
    raw = SimpleNamespace(
        id=uuid.uuid4(),
        source="nightwatch",
        request_id="source-1",
        payload_sha256="abc",
        received_at=received,
        observed_at=vendor,
    )
    entry = source_time_entry(raw, capability="fixture")
    missing_vendor = source_time_entry(
        SimpleNamespace(**{**raw.__dict__, "observed_at": None}),
        capability="fixture",
    )

    assert entry["vendor_observed_at"] == vendor.isoformat()
    assert entry["local_captured_at"] == received.isoformat()
    assert missing_vendor["vendor_observed_at"] is None
    assert missing_vendor["local_captured_at"] == received.isoformat()
    assert missing_vendor["freshness_basis"] == "SOURCE_FIRST_RECEIVED_AT"
    assert parse_vendor_observed_at({"data": {"as_of": vendor.isoformat()}}) == vendor
    assert parse_vendor_observed_at({"data": {"date": "2026-08-17"}}) is None


def test_missing_authoritative_lineage_stays_unresolved() -> None:
    assert aggregate_source_first_received_at({}) is None
    assert aggregate_freshness_anchor_at({}) is None
    assert CandidateFirstKnowledge().at is None


def test_reprocess_preserves_old_source_freshness_and_drops_mixed_heatmap_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    old_receipt = datetime(2026, 8, 10, 12, 0, tzinfo=UTC)
    now = datetime(2026, 8, 17, 12, 0, tzinfo=UTC)
    raw = SimpleNamespace(
        id=uuid.uuid4(),
        source="nightwatch",
        endpoint="/v1/stocks/ohlc/NVDA",
        request_id="old-source",
        payload_sha256="abc",
        payload={"data": {"as_of": "2026-08-10T11:00:00Z", "bars": []}},
        received_at=old_receipt,
        # Legacy Phase 2B stored local time here; reprocess must not trust it as vendor time.
        observed_at=old_receipt,
    )

    class Session:
        def __init__(self) -> None:
            self.added: list[object] = []

        def get(self, _model, raw_id):  # type: ignore[no-untyped-def]
            return raw if raw_id == raw.id else None

        def add(self, row: object) -> None:
            row.id = uuid.uuid4()  # type: ignore[attr-defined]
            self.added.append(row)

        def flush(self) -> None:
            return None

    source = SimpleNamespace(
        ticker="NVDA",
        raw_payload_ids=[str(raw.id)],
        dealer_heatmap={
            "availability": "UNAVAILABLE",
            "capture_timestamp": now.isoformat(),
            "generated_at": None,
            "cells": [],
            "row_stacks": [],
        },
        endpoint_statuses={
            "dealer_heatmap": {"availability": "UNAVAILABLE", "captured_at": now.isoformat()}
        },
        stock_state={},
        iv_rank={},
        term_structure={},
        source_timestamps={"heatmap": now.isoformat()},
        source_request_ids=["old-source"],
        source_time_provenance=None,
        source_first_received_at=None,
        freshness_anchor_at=None,
    )
    config = Phase2bContextConfig(
        version="test.v1",
        stock_state_freshness_minutes=10,
        ohlc_freshness_minutes=10,
        iv_rank_freshness_minutes=10,
        term_structure_freshness_minutes=10,
        heatmap_freshness_minutes=10,
        at_spot_tolerance_pct=0.0025,  # type: ignore[arg-type]
    )
    monkeypatch.setattr("app.confirmation.service.utc_now", lambda: now)
    service = Phase2bContextService(Session(), SimpleNamespace(), config)  # type: ignore[arg-type]

    reprocessed = service._reprocess_ticker_context(source)

    assert reprocessed is not None
    assert reprocessed.created_at == now
    assert reprocessed.source_first_received_at == old_receipt
    assert reprocessed.freshness_anchor_at == old_receipt
    assert reprocessed.source_time_provenance["daily_ohlc"]["vendor_observed_at"] is None
    assert reprocessed.source_timestamps["heatmap"] is None


def test_cache_query_uses_source_freshness_not_created_at() -> None:
    source = inspect.getsource(Phase2bContextService._fresh_context)
    assert "freshness_anchor_at >= cutoff" in source
    assert "created_at >= cutoff" not in source


def test_evaluation_identity_is_nullable_for_legacy_and_immutable_when_known() -> None:
    legacy = Phase2bCandidateEvaluation(evaluation_identity=None)
    baseline = Phase2bCandidateEvaluation(
        evaluation_identity=EvaluationIdentity.FIRST_KNOWLEDGE_BASELINE.value
    )
    refresh = Phase2bCandidateEvaluation(evaluation_identity=EvaluationIdentity.REFRESH.value)

    assert legacy.evaluation_identity is None
    assert baseline.evaluation_identity == "FIRST_KNOWLEDGE_BASELINE"
    assert refresh.evaluation_identity == "REFRESH"
    with pytest.raises(ValueError, match="immutable"):
        baseline.evaluation_identity = EvaluationIdentity.REFRESH.value


def test_model_metadata_contains_only_approved_evaluation_identities() -> None:
    constraints = [
        constraint
        for constraint in Phase2bCandidateEvaluation.__table__.constraints
        if isinstance(constraint, CheckConstraint)
    ]
    rendered = " ".join(str(constraint.sqltext) for constraint in constraints)
    assert "FIRST_KNOWLEDGE_BASELINE" in rendered
    assert "REFRESH" in rendered
    assert Phase2bTickerContextSnapshot.__table__.c.source_first_received_at.nullable is True
    assert Phase2bCandidateEvaluation.__table__.c.evaluation_identity.nullable is True


def test_candidate_first_knowledge_contract_is_set_once_with_rule_provenance() -> None:
    first = datetime(2026, 8, 17, 13, 0, tzinfo=UTC)
    later = first + timedelta(hours=2)
    unresolved = CandidateFirstKnowledge()
    established = unresolved.establish(
        at=first,
        materialization_rule_version="candidate-materialization-test-v1",
    )

    after_later_trigger = established.establish(
        at=later,
        materialization_rule_version="candidate-materialization-test-v2",
    )

    assert established.at == first
    assert established.materialization_rule_version == "candidate-materialization-test-v1"
    assert after_later_trigger is established


def test_raw_ingestion_api_names_vendor_time_explicitly() -> None:
    signature = inspect.signature(RawIngestor.persist)
    assert "vendor_observed_at" in signature.parameters
    assert "observed_at" not in signature.parameters
