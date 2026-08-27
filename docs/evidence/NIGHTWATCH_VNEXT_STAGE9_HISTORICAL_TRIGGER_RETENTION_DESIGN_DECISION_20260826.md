# Nightwatch vNext — Stage 9 Design Decision Amendment
## Historical Trigger Retention / Trading-to-Research Lifecycle

**Date:** 2026-08-26  
**Status:** FOUNDER-LOCKED DESIGN DECISION  
**Stage:** Stage 9 — Offline Research / Forward Outcome  
**Implementation authorization:** NO

## Decision

A qualifying trigger does **not** disappear from Research when its underlying contract or expiry becomes inactive or expires.

Once a trigger has qualified under the contemporaneous Phase 2A rules and is included in a `ProductCandidate` occurrence's first-knowledge evidence, it becomes immutable historical evidence for that Stage 9 Research Sample.

## Canonical lifecycle

Example:

- On Aug 26, the scanner identifies an Aug 28 option contract.
- The contract meets the qualification rules for at least one active discovery route:
  - Radar / OI Change,
  - Expiry Activity, or
  - Contract Persistence.
- That qualifying trigger contributes to a `ProductCandidate` occurrence.
- At `candidate_first_knowledge_at`, the candidate's `FIRST_KNOWLEDGE_BASELINE` and qualifying historical trigger set are frozen.
- The contract may later expire or cease to be active on the Trading Dashboard.
- The historical trigger remains permanently attached to the Research Sample.
- T+1 / T+3 / T+5 outcomes mature later and are appended to the Research record without mutating the frozen first-knowledge evidence.

## Trading vs Research semantics

### Trading Dashboard

Shows current/as-of trading context only, including:

- current Price,
- current IV,
- current Dealer/GEX,
- active anomalies,
- currently relevant contracts/expiries.

When a contract expires or is no longer active, it may disappear from the active Trading view.

### Stage 9 Research Workspace

Shows the historical `ProductCandidate` occurrence as it existed at first knowledge, including:

- immutable `candidate_first_knowledge_at`,
- frozen `FIRST_KNOWLEDGE_BASELINE`,
- all qualifying first-knowledge triggers,
- expired/historical contracts and expiries,
- timing/provenance,
- later T+1 / T+3 / T+5 Forward Outcomes.

The Research Sample exists from candidate formation onward; it does **not** wait for the contract to expire before becoming a research sample. Its Forward Outcome maturity can initially be `NOT_YET_MATURE`.

## Research sample identity

The research unit remains:

> **one ProductCandidate occurrence**

A contract is **not** an independent research sample.

For example, one ProductCandidate containing 27 qualifying anomaly contracts is still one Research Sample; the 27 contracts are trigger composition/features of that sample.

## Admission rule

Only contracts/triggers that actually qualified under the contemporaneous Phase 2A qualification rules become frozen Research evidence.

Merely appearing somewhere on the Dashboard does not make a contract a Research trigger.

## Non-negotiable boundary

- Frozen first-knowledge evidence is immutable.
- Current Trading Context must never overwrite or refresh the frozen baseline.
- Contract expiry must never delete historical qualifying evidence.
- Later evidence must not be backfilled into the original qualifying trigger set.
- Live scanner / live ranking must not consume the current candidate's Forward Outcome.

## Canonical evidence target

When incorporated into the repository, this decision should be preserved under:

`F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE9_HISTORICAL_TRIGGER_RETENTION_DESIGN_DECISION_20260826.md`
