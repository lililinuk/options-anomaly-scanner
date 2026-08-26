# Nightwatch Scanner vNext — Stage 4B Phase 2A vNext — Codex Execution Package

**Date:** 2026-08-18  
**Stage:** 4B — PHASE 2A vNext  
**Executor:** Codex implementation engineer  
**Authorization:** Stage 4B only  
**Branch:** `vnext/stage4b-phase2a-vnext`  
**Worktree:** `F:\options-anomaly-scanner-stage4b`  
**Required base SHA:** `4f0edba28dc6939e1d60ba176d0281189e5ee67d`

---

# 0. Purpose

Modify the active Phase 2A analytical path so it matches the founder-approved vNext architecture while preserving accepted history.

The active evidence families become:

```text
RADAR_EVENT           Core Discovery
EXPIRY_ACTIVITY       Core Discovery
  └── 0DTE            special calibration method inside Expiry Activity
CONTRACT_PERSISTENCE  Core Confirmation + Slow-Burn Discovery
```

Removed/sunset from active discovery:

```text
EXPIRY_PERSISTENCE
STRUCTURAL_COLD_START
Evidence Breadth / MULTI_EVIDENCE
```

Structure / Neighbor Strike / Cluster become **post-candidate Deep-Dive context**, not independent discovery evidence.

Candidate semantics are:

```text
ANOMALY = exact contract or expiry
PRODUCT CANDIDATE = ticker/product
```

However the first-class persisted `ProductCandidate` / `ProductCandidateTrigger` layer belongs to **Stage 5**, not Stage 4B.

---

# 1. Required Documents for a Fresh Codex Window

Read completely:

1. `NIGHTWATCH_SCANNER_VNEXT_INTEGRATED_SPEC_PROMPT_20260817(1).md`
2. `PHASE2A_VNEXT_DECISION_HANDOFF_20260817.md`
3. `NIGHTWATCH_VNEXT_STAGE1_READONLY_PROOF_GATE_REPORT_20260817.md`
4. `NIGHTWATCH_VNEXT_STAGE3_ACCEPTED_CHECKPOINT_COMPLETION_REPORT_20260818.md`
5. This file:
   `NIGHTWATCH_VNEXT_STAGE4B_PHASE2A_VNEXT_CODEX_EXECUTION_PACKAGE_20260818.md`

Inspect current repo broadly before edits.

The Integrated Spec is later and authoritative where stage boundaries differ from the older Phase 2A decision handoff.

---

# 2. Preflight — Isolated Common Base

Verify:

```text
REPO_ROOT=F:\options-anomaly-scanner-stage4b
BRANCH=vnext/stage4b-phase2a-vnext
HEAD=4f0edba28dc6939e1d60ba176d0281189e5ee67d
WORKTREE=CLEAN
```

Also verify:

- Stage 2 G1/G2 fixes present;
- Stage 3 time/knowledge/freshness foundation present;
- no Stage 4A implementation mixed into this worktree;
- current Alembic head is still the accepted Stage 3 base;
- current Phase 2A defects from Stage 1 remain reproducible where Stage 4B owns them.

STOP if not.

---

# 3. Mandatory Repository Orientation

Map before editing:

```text
Phase 2A scan orchestration
v1.1/v1.2/v1.3 scoring and route logic
Radar event parsing/gating
Expiry Activity and 0DTE paths
Contract Persistence history query/scoring
Structure / Neighbor Strike
Cluster
candidate/route selection
API serialization
legacy score fallback
glossary/state labels affected by backend semantics
tests
```

Report:

```text
STAGE4B_ORIENTATION
- current active evidence families:
- current candidate entity:
- Radar route:
- Expiry Activity route:
- 0DTE route:
- Persistence route:
- Structure/Cluster role:
- legacy route/score leakage:
```

Declare exact `AUTHORIZED_FILES_PROPOSED`.

Read broadly; write narrowly.

---

# 4. Hard Authorization Boundary

## Authorized

- Phase 2A backend analytical/orchestration changes.
- API/serialization changes strictly necessary to expose correct Phase 2A vNext semantics.
- Focused tests.
- Minimal glossary/semantic text changes only where needed to avoid actively false Phase 2A labels.
- In-memory/read-model grouping of qualifying anomalies by ticker for vNext candidate semantics.

## Forbidden

- No Nightwatch calls.
- No paid units.
- No remote DB writes/migrations.
- No workflow dispatch.
- No Stage 4A data-pipeline/scheduler work.
- **No Alembic migration in this parallel branch without founder coordination.**
- No `ProductCandidate` or `ProductCandidateTrigger` persistent model/table (Stage 5).
- No Phase 2B Balanced Model (Stage 6).
- No full Candidate-first dashboard redesign (Stage 7).
- No universe expansion.
- No Forward Outcome / Actionability / Trade Expression.
- No new score/threshold/ranking.
- No rewriting accepted historical evaluations.
- No deleting legacy history just because a route is removed from active discovery.

---

# 5. Parallel Migration Rule

Stage 4A owns migration creation in the Stage 4A/4B parallel tranche.

Stage 4B should be implementable as code/API semantics over existing/versioned structures.

If a correct Stage 4B implementation **requires** a new DB migration:

```text
STAGE4B_RESULT=HOLD
MIGRATION_COORDINATION_REQUIRED=YES
```

Explain exactly why and stop. Do not independently create a competing Alembic head from the shared Stage 3 base.

This protects later integration.

---

# 6. Non-Negotiable Semantic Red Lines

Remain true:

```text
missing != zero
Call != bullish
Put != bearish
OI increase != bought-to-open
Premium != one order / directional conviction
positive/negative GEX != market direction
UNRESOLVED != Neutral
PERSISTENT_BUILD/DECLINE != trade direction
Radar != complete option universe
no universal anomaly score
no ticker/conviction score
no BUY/SELL
no Actionability label
no rewriting accepted history
no-lookahead
```

No new interpretation may violate these.

---

# 7. Target Phase 2A vNext Funnel

Implement the active conceptual flow:

```text
Universe
   ↓
RADAR_EVENT ------------------┐
EXPIRY_ACTIVITY --------------┼→ qualifying anomaly pool
CONTRACT_PERSISTENCE ---------┘
   ↓
all qualifying contract/expiry anomalies retained
   ↓
GROUP BY TICKER / PRODUCT
   ↓
Product Candidate projection
   ↓
Structure / Neighbor Strike / Cluster Deep Dive
   ↓
Phase 2B later
```

Stage 4B may expose a **non-persisted candidate projection/read model** grouped by ticker if needed.

Do not create the Stage 5 persistent ProductCandidate entity.

A ticker becomes a current Product Candidate projection when at least one admissible active Phase 2A anomaly qualifies under current vNext semantics.

Do not discard additional anomalies after the ticker qualifies.

---

# 8. RADAR_EVENT

Keep as Core Discovery.

Preserve current material gate/anchors; do not retune:

```text
premium >= existing approved threshold
abs(delta OI) >= existing approved threshold
```

Radar remains a vendor-ranked changed-contract subset, not the full option universe.

Requirements:

- exact-contract anomaly identity retained;
- no directional inference;
- existing DTE/watch/deep-dive eligibility semantics retained unless the vNext spec explicitly reclassifies presentation;
- all qualifying Radar anomalies retained in the anomaly pool;
- Radar can independently make a ticker qualify for the non-persisted Product Candidate projection.

Do not change thresholds.

---

# 9. EXPIRY_ACTIVITY

Keep as Core Discovery at expiry entity level.

0DTE remains:

```text
EXPIRY_ACTIVITY
└── DTE=0 special historical calibration method
```

not a fourth evidence family.

Preserve current scoring anchors/gates.

Requirements:

- expiry anomaly can independently qualify a ticker;
- no fabricated contract-level detail for expiry-only anomalies;
- non-0DTE activity uses the existing current-session activity logic;
- 0DTE uses the existing historical model, subject to Stage 4A's future clean-canonical data foundation;
- no direction inference.

Stage 4B owns presentation/scoring-semantic corrections below, not Stage 4A pipeline storage.

---

# 10. CONTRACT_PERSISTENCE

Keep as:

```text
Core Confirmation
+
Slow-Burn Discovery
```

Entity: exact contract.

Keep existing 3/5/10 valid-observation scoring framework and anchors unless an approved document explicitly changes them.

## G9 — No-lookahead

Any history used for an analysis/candidate date must satisfy an authoritative upper bound so future OI observations cannot enter the window.

At minimum ensure the history query respects the relevant vendor OI date / evidence-as-of boundary.

Tests must demonstrate an observation after the analysis date cannot change the earlier result.

## G10 — Observation span visibility

The last-N valid-observation window may span calendar gaps.

Do not invent a gap threshold.

Expose/store in the evaluation/read model at least:

```text
window_first_observation_date
window_last_observation_date
valid_observation_count
```

or semantically equivalent explicit metadata.

Do not imply that "5 observations" means "5 calendar days."

## G8 — Current-candidate freshness

Historical persistence must not act forever as a current trigger.

Required semantics:

```text
explicit
configurable
versioned
no-lookahead
calibration-required
```

**Do not invent 5/7/10/20 days or any new supposedly correct numeric window.**

First inspect whether a founder-approved numeric freshness value exists in current governing docs/config.

If none exists, the safe default is:

```text
PERSISTENCE_CURRENT_TRIGGER_FRESHNESS=CALIBRATION_REQUIRED
```

Meaning:

- compute/preserve Persistence analytics descriptively;
- do not silently treat arbitrarily old persistence as current;
- persistence-alone may not pull a ticker into the **current** candidate projection until an explicit configured recency rule exists;
- Radar/Expiry Activity remain unaffected;
- expose this as calibration-required/insufficient-currentness, not as neutral/zero.

If existing code requires a numeric value to run, do not make one up. Implement an explicit disabled/unconfigured current-trigger state.

Later empirical data may calibrate the window.

---

# 11. Remove EXPIRY_PERSISTENCE From Active Discovery

Decision:

```text
EXPIRY_PERSISTENCE → REMOVE FROM ACTIVE vNEXT DISCOVERY
```

Requirements:

- it cannot create a current anomaly/candidate;
- it cannot contribute to evidence breadth/route qualification;
- old data/code may remain read-only if removing it destructively is unnecessary;
- API should not present it as an active vNext discovery family;
- do not delete historical expiry observations useful for research/data quality.

---

# 12. Sunset STRUCTURAL_COLD_START

Decision:

```text
STRUCTURAL_COLD_START → SUNSET FROM ACTIVE DISCOVERY
```

Requirements:

- Structure cannot create a candidate before a core anomaly exists;
- remove it from active route/candidate qualification;
- preserve historical evidence/code read-only where practical;
- no destructive history rewrite.

---

# 13. Remove Evidence Breadth / MULTI_EVIDENCE

Decision:

```text
Evidence Breadth → REMOVE
MULTI_EVIDENCE → REMOVE
```

Do not replace it with a new composite/ticker/conviction score.

Preferred semantics are explicit Why-Found evidence:

```text
Radar Event          PRESENT/ABSENT
Expiry Activity      PRESENT/ABSENT
Contract Persistence PRESENT/ABSENT / CALIBRATION_REQUIRED
```

No "3 evidence families = stronger conviction."

---

# 14. Structure / Neighbor Strike / Cluster → Deep Dive

Structure and Cluster are not active discovery families.

Correct order:

```text
candidate/anomaly qualifies first
→ Structure
→ Neighbor Strike as Structure component
→ Cluster context
```

## G14/G15/G26 corrections

- `INVALID_CLUSTER` must never render/serialize as positive Structure evidence.
- sub-threshold Structure must not be treated as positive evidence.
- invalid/weak presence cannot inflate a removed breadth count.
- zero-fill must not convert missing facts into analytical zero where NULL/UNAVAILABLE is correct.
- quote availability/as-of must be labeled truthfully.
- Neighbor Strike is a Structure component, not an independent evidence family.

Preserve existing Structure/Cluster score anchors/gates.

No threshold retuning.

---

# 15. G11 — 0DTE Score-Basis Attribution

Fix API/read-model semantics so 0DTE rows are not incorrectly attributed to the non-0DTE balanced/share-neighbor basis.

The displayed/serialized score basis must reflect the actual method used.

Do not change score anchors.

---

# 16. G13 — Neighbor Ratio Display vs Scoring Comparator

Current displayed Neighbor Ratio and glossary semantics can differ from the comparator actually used in scoring.

Target:

- serialized/display-supporting field identifies the actual comparable-neighbor ratio used by the score;
- comparator peer count/quality/median/DTEs remain distinguishable;
- missing historical comparator remains NULL, never synthesized;
- glossary/API wording matches actual calculation.

Do not alter the underlying scoring anchors.

---

# 17. G21 — Legacy Discovery Score Leakage

vNext active APIs/read models must not silently fall back to legacy v1.2 discovery-score concepts in a way that appears current.

Requirements:

- isolate/mark legacy output explicitly;
- do not use legacy discovery score to define current Product Candidate projection;
- remove silent analytical fallback from vNext path where possible without deleting historical API compatibility;
- no replacement universal score.

If legacy compatibility endpoints remain, label them legacy.

---

# 18. G7 — Market Date / Trading Day / DTE Identity

Fix Stage 4B analytical semantics so:

- market date uses explicit NY market-calendar semantics, not browser/local machine date;
- trading-day validity is explicit where current-candidate analysis needs it;
- every DTE/date says what anchor it is measured from;
- vendor-dated evidence is not silently reinterpreted using a later local scan date.

Do not guess missing vendor dates.

No-lookahead remains mandatory.

---

# 19. Candidate Projection — Stage 4B vs Stage 5 Boundary

Stage 4B must make Phase 2A behave conceptually as:

```text
Candidate = Product/Ticker
Anomaly = Contract/Expiry Trigger
```

But Stage 5 owns first-class persistence.

Allowed in Stage 4B:

- in-memory grouping;
- service/domain read model;
- API projection;
- deterministic ticker grouping;
- full anomaly list under each ticker;
- reason/evidence time-layer labels derived from existing evidence.

Forbidden:

- `ProductCandidate` SQLAlchemy model/table;
- `ProductCandidateTrigger` table;
- persisted `candidate_first_knowledge_at` on a new candidate entity;
- Stage 5 migrations.

Do not create a temporary persistent entity that Stage 5 will replace.

---

# 20. No Top-N / No 4×3 Product Rule

For MAG7:

- all qualifying ticker candidates should be representable;
- no forced 12 slots;
- no user-facing top-4 ticker cap as candidate definition;
- no Top-N cross-ticker ranking;
- no Ticker Score.

Existing budget/deep-dive caps may remain as internal engineering mechanisms if required, but any truncation must be explicit/logged and cannot redefine candidate identity.

---

# 21. API / Frontend Scope

Stage 4B may update backend API/read-model semantics required to expose Phase 2A vNext correctly.

Do **not** perform the Stage 7 Candidate-first dashboard redesign.

Minimal frontend/glossary changes are permitted only when necessary to prevent actively false labels created by the backend changes.

If full UX work is needed, carry it to Stage 7.

---

# 22. Stage 2/3 Regression Protection

Must preserve:

```text
truthful run-state failure semantics
Radar captured_at / ny_market_date stop-bleed
source_first_received_at immutability
vendor/local time separation
source-aware freshness
G3 pinned Radar source
baseline/refresh evaluation identity
no future Outcome consumption
```

Run Stage 2/3 regression tests.

---

# 23. Explicit Non-Goals

Do not implement:

```text
daily scheduler / 0DTE canonical storage (Stage 4A)
contract open_interest_as_of persistence (Stage 4A)
DailyCollectionCoverage date split (Stage 4A)
ProductCandidate persistence (Stage 5)
Phase 2B Balanced Model (Stage 6)
Candidate-first Dashboard (Stage 7)
Forward Outcome
Actionability
Trade Expression
Universe expansion
new ranking
new scoring anchors
GEX redesign
IV Rank provenance resolution
```

---

# 24. Verification Requirements

At minimum add/run tests for:

- active-family set exactly Radar / Expiry Activity / Contract Persistence;
- Expiry Persistence cannot create a vNext current candidate;
- Structural Cold Start cannot create a vNext current candidate;
- Evidence Breadth/MULTI_EVIDENCE absent from vNext current qualification;
- expiry-only activity can qualify a ticker projection;
- Radar can qualify a ticker projection;
- Persistence current-trigger respects explicit configured freshness state;
- no configured freshness → `CALIBRATION_REQUIRED`, not stale indefinite triggering;
- Persistence history no-lookahead;
- observation window first/last span visibility;
- future OI row cannot alter past persistence result;
- 0DTE score-basis attribution;
- Neighbor Ratio serialized comparator matches score input;
- invalid cluster not positive evidence;
- missing cluster/quote values not zero-filled analytically;
- candidate grouping preserves all qualifying anomalies;
- no top-4/12-slot product-candidate requirement;
- legacy discovery score not used for vNext candidate qualification;
- Stage 2/3 regression suites;
- complete backend suite if safe;
- Ruff/type/static checks.

No real vendor traffic.

---

# 25. Required Completion Report

## A. RESULT

```text
STAGE4B_RESULT=
PASS
PASS_WITH_CARRIED_ITEMS
HOLD
```

## B. PREFLIGHT

```text
BRANCH=
BASE_HEAD=
WORKTREE=
CLEAN_AT_START=
```

Base must be `4f0edba28dc6939e1d60ba176d0281189e5ee67d`.

## C. ACTIVE ARCHITECTURE

Return:

```text
ACTIVE_DISCOVERY=[
 RADAR_EVENT,
 EXPIRY_ACTIVITY,
 CONTRACT_PERSISTENCE
]

REMOVED_ACTIVE_DISCOVERY=[
 EXPIRY_PERSISTENCE,
 STRUCTURAL_COLD_START,
 Evidence_Breadth
]

CANDIDATE_ENTITY=TICKER_PRODUCT_PROJECTION
ANOMALY_ENTITY=CONTRACT_OR_EXPIRY
PERSISTED_PRODUCT_CANDIDATE_CREATED=NO
```

## D. PERSISTENCE

Report:

```text
NO_LOOKAHEAD_BOUND=
WINDOW_SPAN_METADATA=
CURRENT_TRIGGER_FRESHNESS_MODE=
FRESHNESS_CONFIG_VERSIONING=
```

If no numeric window is configured:

```text
CURRENT_TRIGGER_FRESHNESS_MODE=CALIBRATION_REQUIRED
```

## E. EXPIRY ACTIVITY / 0DTE

Describe score-basis correction and expiry-only candidate behavior.

## F. STRUCTURE / CLUSTER

Describe deep-dive gating, invalid handling, NULL discipline, quote-as-of semantics.

## G. LEGACY CLEANUP

Describe Expiry Persistence/Cold Start/Breadth/legacy score treatment without destructive deletion.

## H. CANDIDATE PROJECTION

Show how all qualifying anomalies group by ticker and how no valid anomaly is silently dropped.

## I. MIGRATION

Return:

```text
MIGRATION_CREATED=NO
MIGRATION_COORDINATION_REQUIRED=YES/NO
```

Expected `MIGRATION_CREATED=NO`.

## J. TESTS

List commands/results.

## K. CARRIED ITEMS

Anything deferred to Stage 4A/5/7/etc.

## L. DIFF

```text
FILES_CHANGED=
LINES_ADDED=
LINES_REMOVED=
MIGRATION_FILES=0
WORKFLOW_FILES=0
```

## M. AUTHORIZATION COMPLIANCE

Return exactly:

```text
NIGHTWATCH_REQUESTS=0
PAID_UNITS=0
REMOTE_DB_WRITES=0
REMOTE_MIGRATIONS_RUN=0
WORKFLOWS_DISPATCHED=0
COMMITS_CREATED=0
PUSHES=0
PRS_CREATED=0
MERGES=0
```

## N. SPEC IMPACT

```text
REOPEN_PHASE2A_VNEXT=YES/NO
SPEC_AMENDMENT_REQUIRED=YES/NO
STAGE_ORDER_CHANGE_REQUIRED=YES/NO
```

## O. NEXT ACTION

```text
NEXT_AUTHORIZED_STAGE=NONE
```

Do not start Stage 5 or Stage 6.

---

# 26. Stop Conditions

STOP if:

- branch/head/worktree does not match common checkpoint;
- Stage 4A changes are present;
- a new database migration is required for correctness;
- a numeric Persistence freshness window would have to be invented;
- correctness requires changing approved scoring thresholds;
- accepted history must be rewritten;
- a test requires Nightwatch;
- implementation would prematurely create persistent ProductCandidate entities;
- Phase 2B/Forward Outcome/Actionability work becomes necessary.

Do not expand the package.

---

# 27. Final Principle

Phase 2A vNext should answer only:

```text
What unusual contract/expiry evidence exists?
Which products/tickers does that make research-worthy now?
What positioning structure explains those already-qualified anomalies?
```

It does not answer:

```text
Which direction?
Should I trade?
How should I trade?
What will happen next?
```
