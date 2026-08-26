# Nightwatch Scanner vNext — Stage 5 Product Candidate Persistence — Codex Execution Package

**Date:** 2026-08-18  
**Stage:** 5 — PRODUCT CANDIDATE PERSISTENCE LAYER  
**Executor:** Codex implementation engineer  
**Authorization:** Stage 5 only  
**Integrated baseline:** `84b27b46311c35006def006621fe534b96c690d1` (`vnext/stage4-integrated`)  
**Expected branch:** `vnext/stage5-product-candidate-persistence`  
**Preferred worktree:** `F:\options-anomaly-scanner-stage5`

---

# 0. Objective

Persist the already-accepted Stage 4 Product Candidate projection as first-class research entities:

```text
ProductCandidate
ProductCandidateTrigger
candidate_first_knowledge_at
```

Stage 5 does **not** redesign Phase 2A, does **not** implement the Stage 6 Balanced Model, and does **not** implement Forward Outcome.

Normative identity remains:

```text
ANOMALY = exact contract or expiry
PRODUCT CANDIDATE = ticker / product
```

---

# 1. Accepted predecessor state

Stage 4 direct integration is accepted:

```text
STAGE4_INTEGRATION_RESULT=PASS_WITH_CARRIED_ITEMS
STAGE4A_INTEGRATED=YES
STAGE4B_INTEGRATED=YES
INTEGRATED_HEAD=84b27b46311c35006def006621fe534b96c690d1
ALEMBIC_HEAD=20260818_0015
ALEMBIC_SINGLE_HEAD=YES
```

Preserve all accepted Stage 4 invariants, especially:

```text
PERSISTENCE_NO_LOOKAHEAD_PRESERVED=YES
FUTURE_OBSERVATION_CAN_CHANGE_EARLIER_RESULT=NO
PERSISTENCE_FRESHNESS_FAIL_CLOSED_PRESERVED=YES
CANDIDATE_GROUPING_BEFORE_BUDGET_PRESERVED=YES
TOP4_LIMIT_CAN_DROP_VALID_PRODUCT_CANDIDATE=NO
PERSISTENCE_PROJECTION_DUPLICATION_FOUND=NO
REMOVED_ROUTE_LEAKAGE_STILL_ZERO=YES
STRUCTURE_POST_CANDIDATE_ONLY_PRESERVED=YES
```

Accepted population proof:

```text
QUALIFYING_TICKERS=7
PRODUCT_CANDIDATE_COUNT=7
DEEP_DIVE_SELECTED_TICKER_COUNT=4
OMITTED_VALID_PRODUCT_CANDIDATES=0
```

---

# 2. Governing documents

Read completely before implementation:

1. `NIGHTWATCH_SCANNER_VNEXT_INTEGRATED_SPEC_PROMPT_20260817(1).md`
2. `NIGHTWATCH_VNEXT_STAGE3_TIME_KNOWLEDGE_INTEGRITY_CODEX_EXECUTION_PACKAGE_20260817.md`
3. `NIGHTWATCH_VNEXT_STAGE4A_DAILY_PIPELINE_CODEX_EXECUTION_PACKAGE_20260818.md`
4. `NIGHTWATCH_VNEXT_STAGE4B_PHASE2A_VNEXT_CODEX_EXECUTION_PACKAGE_20260818.md`
5. this Stage 5 package
6. the Founder-provided Stage 4 direct-integration completion report

Authority:

```text
Founder-approved Integrated Spec
> Stage 5 package
> accepted integrated Stage 4 state
> accepted Stage 3 time/knowledge foundation
> repository implementation detail
```

---

# 3. Required entity semantics

The integrated spec requires:

```text
ProductCandidate
    ticker
    candidate_first_knowledge_at      immutable
    materialization rule version
    status / lifecycle fields

ProductCandidateTrigger
    → contract anomalies: Radar, Contract Persistence
    → expiry anomalies: Expiry Activity
    → each with anomaly identity, evidence time layer, source ids
```

One ProductCandidate references many triggers. The layer is additive. Existing exact-contract Phase 2B evaluations and historical evidence are not deleted or rewritten.

---

# 4. Candidate occurrence identity — conservative rule

The approved spec does not define a cross-run close/reopen/re-entry lifecycle. Do **not** invent one.

For this Stage 5 tranche, persist a **candidate materialization occurrence** keyed by an authoritative successful Phase 2A scan/materialization identity plus ticker plus materialization-rule version, or the closest semantically equivalent authoritative identity already present in the repository.

Required behavior:

```text
same successful materialization occurrence + same ticker + same rule version
→ same ProductCandidate on replay

different successful materialization occurrence
→ may create a distinct ProductCandidate occurrence
```

Do not auto-merge across runs. Do not invent inactivity timeout, episode gap, CLOSED/REOPENED logic, or lifecycle freshness.

Return:

```text
CROSS_RUN_CANDIDATE_LIFECYCLE=DEFERRED_NO_AUTO_MERGE
```

If no stable authoritative successful-scan/materialization identity exists, STOP:

```text
STAGE5_RESULT=HOLD
MATERIALIZATION_IDENTITY_DECISION_REQUIRED=YES
```

---

# 5. Physical candidate first knowledge

Stage 3 defines:

```text
candidate_first_knowledge_at
=
first time the system had all admissible evidence required,
under then-current materialization rules,
to materialize the user-facing Product/Ticker Candidate
```

For new prospective Stage 5 candidate occurrences, persist the actual first successful candidate-materialization knowledge cutoff captured by the application/materializer.

Rules:

- capture once in UTC;
- immutable thereafter;
- replay reuses stored value;
- later triggers never move it forward;
- later context refresh never rewrites it;
- later-discovered historical evidence never moves it backward;
- never derive it from event date, vendor date, DB `created_at`, migration time, or scan date alone.

Reuse the Stage 3 first-knowledge foundation where applicable. Do not create a competing semantic.

If a prospective authoritative value cannot be established without guessing, HOLD.

---

# 6. Candidate time vs trigger/source time

Keep distinct:

```text
candidate_first_knowledge_at

event_date
source_first_received_at
vendor_observed_at
local_captured_at
trigger_first_knowledge_at
```

Each ProductCandidateTrigger must preserve its own source/time provenance.

For triggers present at initial candidate materialization:

```text
present_at_first_knowledge=true
```

Any future explicitly appended trigger to the same candidate occurrence must use:

```text
present_at_first_knowledge=false
```

and may not redate the candidate.

---

# 7. Active trigger families only

Allowed:

```text
RADAR_EVENT          → CONTRACT
EXPIRY_ACTIVITY      → EXPIRY
CONTRACT_PERSISTENCE → CONTRACT
```

0DTE remains a special calibration mode inside `EXPIRY_ACTIVITY`, not a fourth trigger family.

Forbidden as ProductCandidateTrigger families:

```text
EXPIRY_PERSISTENCE
STRUCTURAL_COLD_START
Evidence Breadth
MULTI_EVIDENCE
Structure
Neighbor Strike
Cluster
legacy discovery score
```

Structure / Neighbor Strike / Cluster remain post-candidate Deep-Dive context only.

---

# 8. Preserve the full active anomaly pool

Persist the full Stage 4 active anomaly set under each candidate occurrence, not only the first qualifying anomaly.

Each trigger link must explicitly preserve:

```text
qualifies_candidate=true/false
```

and, for Persistence when available, current-trigger eligibility/currentness metadata.

At least one `qualifies_candidate=true` trigger is required to create a new ProductCandidate.

Under:

```text
CURRENT_TRIGGER_FRESHNESS_MODE=CALIBRATION_REQUIRED
```

supporting-only Persistence must not materialize a candidate by itself.

---

# 9. Consume Stage 4 projection; do not recompute eligibility

Required flow:

```text
accepted Phase 2A evidence
→ accepted Stage 4 Product Candidate projection
→ Stage 5 materializer
→ ProductCandidate + ProductCandidateTrigger
```

Do not build a second candidate-selection algorithm in Stage 5.

No new thresholds, route priorities, Top-N logic, candidate scores, conviction scores, or freshness rules.

A narrow refactor to share the existing pure grouping/projection logic between read and successful-scan write paths is allowed only if tests prove semantics are unchanged.

---

# 10. Authoritative write point — never materialize on GET

Materialization must occur only from an authoritative successful scan/materialization write path.

Never create candidate rows from dashboard/API GET/read/serialization/page refresh.

Expected semantics:

```text
SUCCESS_WITH_CANDIDATES → persist candidates/triggers
SUCCESS_NO_CANDIDATE    → zero candidate rows
FAILED                  → zero candidate rows
RUNNING / NOT_RUN        → zero candidate rows
```

Preserve exact accepted Stage 2 run-state names if repository naming differs.

GET remains read-only.

---

# 11. No-lookahead materialization cutoff

A candidate materialized at T may use only evidence admissible by its first-knowledge/materialization cutoff.

Required invariant:

```text
materialize candidate C at T
later add evidence at T+1

replay/read C
→ candidate_first_knowledge_at unchanged
→ present_at_first_knowledge trigger set unchanged
→ T+1 evidence never becomes first-knowledge evidence for C
```

Replay of an existing candidate occurrence should reuse persisted candidate/trigger rows rather than rebuild that occurrence from later DB state.

---

# 12. Minimum ProductCandidate shape

After repository inspection, implement semantically equivalent explicit fields. At minimum preserve:

```text
id
ticker
candidate_first_knowledge_at
materialization_rule_version
materialization_rule_hash
authoritative source scan/materialization identity
lifecycle_state
created_at / local persistence audit time
```

Stage 5 lifecycle may be only:

```text
MATERIALIZED
```

Do not invent CLOSED/EXPIRED/RESOLVED/REOPENED/ACTIVE-timeout semantics.

`created_at` is audit time only and never substitutes for first knowledge.

---

# 13. Minimum ProductCandidateTrigger shape

At minimum preserve:

```text
id
product_candidate_id

evidence_family
anomaly_entity_type
anomaly_identity
source_evidence_identity

qualifies_candidate
present_at_first_knowledge

event_date
trigger_first_knowledge_at
source_first_received_at
vendor_observed_at
local_captured_at

source ids / source observation ids
specification/materialization/config provenance
created_at
```

For contract anomalies: preserve exact contract identity.

For expiry anomalies: preserve exact expiry identity and never fabricate contract fields.

Prefer explicit nullable source FKs when authoritative source tables exist, plus a normalized immutable source-evidence identity for replay/deduplication.

---

# 14. Trigger deduplication

The same logical anomaly may be reachable through more than one read path. Stage 5 must still persist it once.

Especially preserve the accepted Stage 4B invariant for:

```text
current-run Deep-Dive evidence
+
untruncated Persistence projection evidence
→ one logical trigger
```

Use a deterministic uniqueness rule based on candidate identity + evidence family + authoritative source-evidence identity (or equivalent proven key).

Required proof:

```text
LOGICAL_INPUT_ROWS=2
PERSISTED_LOGICAL_TRIGGER_ROWS=1
```

Do not dedupe distinct events merely because contract symbol/expiry matches.

---

# 15. Immutability / append-only

Immutable candidate identity fields:

```text
ticker
candidate_first_knowledge_at
source materialization identity
materialization_rule_version/hash
```

Immutable trigger identity fields:

```text
source_evidence_identity
anomaly_identity
source_first_received_at once known
trigger_first_knowledge_at
present_at_first_knowledge
```

Later new evidence creates a new trigger row; it does not transform an old row into a different anomaly.

Conflicting replay must fail closed rather than silently mutate first knowledge/provenance.

---

# 16. Idempotence

Required:

```text
same successful candidate occurrence replay
→ ProductCandidate created once

same candidate + same logical trigger replay
→ ProductCandidateTrigger created once
```

Immediate replay should create zero duplicate rows.

---

# 17. Historical policy

Stage 5 is prospective.

The migration must not backfill ProductCandidate rows from old Radar/Expiry/Persistence/Phase2B/dashboard data.

Do not manufacture historical first knowledge from:

```text
event_date
scan date
created_at
evaluated_at
migration time
captured_at
```

No historical repair is authorized.

---

# 18. Additive migration

Stage 5 owns one additive migration after:

```text
20260818_0015
```

Expected new head:

```text
20260818_0016
```

Migration may create candidate/trigger tables, FKs, unique constraints, indexes, CHECK constraints, and minimal lifecycle/immutability support.

Migration must not perform historical UPDATE/INSERT backfill or destructive old-table changes.

Required:

- one Alembic head;
- offline PostgreSQL upgrade SQL;
- offline PostgreSQL downgrade SQL;
- model/migration agreement;
- no remote migration.

If isolated PostgreSQL remains unavailable:

```text
ISOLATED_POSTGRES_RUNTIME_VERIFIED=NO
```

carry it forward.

---

# 19. Preserve existing carried gates

Keep:

```text
CURRENT_TRIGGER_FRESHNESS_MODE=CALIBRATION_REQUIRED
RADAR_OI_SCHEDULE_ACTIVATION=PENDING_ROLLOVER_EVIDENCE
```

Do not invent a numeric Persistence freshness value and do not activate Radar/OI cron.

---

# 20. Stage 6 boundary

Do not implement:

```text
ProductCandidateContext
AnomalyContextDetail
Balanced Model B1-B5
fresh Phase 2B vendor calls
FIRST_KNOWLEDGE_BASELINE context contents
REFRESH context computation
```

Stage 5 may expose candidate IDs/timestamps/provenance required by Stage 6, but it must not implement Stage 6 logic.

No Forward Outcome, T+N prices, MFE/MAE, Actionability, or future-derived labels.

---

# 21. Minimal backend read support

Backend-only additive read/repository support is authorized so Stage 6 can load:

```text
ProductCandidate
+ ordered ProductCandidateTriggers
```

Include candidate ID, ticker, first knowledge, materialization version/hash, lifecycle state, full trigger list, trigger qualification flags, source/time provenance.

Optional additive scan API serialization of persisted candidate ID/first-knowledge metadata is allowed if frontend behavior does not change.

No dashboard redesign.

---

# 22. Mandatory read-only orientation

Before editing, inspect and report:

```text
REPOSITORY_ORIENTATION
- integrated Stage 4 head:
- authoritative successful scan identity:
- successful scan write path:
- Stage 4 candidate projection entry point:
- candidate grouping function:
- Radar source identity:
- Expiry Activity source identity:
- Persistence source identity:
- Stage 3 first-knowledge foundation:
- migration predecessor:
- current API read path:
```

Then:

```text
AUTHORIZED_FILES_PROPOSED:
- file: reason
```

READ BROADLY; WRITE NARROWLY.

---

# 23. Preflight / branch

Start exactly from:

```text
84b27b46311c35006def006621fe534b96c690d1
```

Create:

```text
branch   = vnext/stage5-product-candidate-persistence
worktree = F:\options-anomaly-scanner-stage5
```

If already present, inspect it; do not force-move/delete.

Required:

```text
WORKTREE_CLEAN_AT_START=YES
INTEGRATED_STAGE4_BASE_PRESENT=YES
ALEMBIC_HEAD_BEFORE=20260818_0015
```

STOP on wrong base.

---

# 24. Authorized file scope

Authorized categories:

```text
backend/app/db/models.py
backend/alembic/versions/<Stage5 migration>
backend/app/scanner/... minimal candidate persistence/materializer/repository
backend/app/api/routes/scans.py if needed for write/read integration
backend/app/confirmation/... only if Stage 3 first-knowledge reuse requires it
backend/tests/... focused Stage 5 + regressions
```

A small isolated module such as `backend/app/scanner/candidates.py` is allowed.

Not authorized:

```text
.github/workflows/*
Dealer/GEX changes
Stage 4A scheduler changes
frontend redesign
Phase 2B Balanced Model
Forward Outcome
Actionability
Trade Expression
universe expansion
score/threshold changes
Persistence freshness calibration
```

---

# 25. Required functional tests

Prove at minimum:

### S5-A — population/write state

```text
SUCCESS_WITH_CANDIDATES → persisted
SUCCESS_NO_CANDIDATE    → zero rows
FAILED                  → zero rows
```

Seven-ticker proof:

```text
QUALIFYING_TICKERS=7
PERSISTED_PRODUCT_CANDIDATE_COUNT=7
DEEP_DIVE_SELECTED_TICKER_COUNT=4
OMITTED_VALID_PRODUCT_CANDIDATES=0
```

### S5-B — full anomaly pool

```text
persisted trigger count == Stage 4 anomaly_count
persisted qualifying trigger count == Stage 4 qualifying_anomaly_count
```

Supporting CALIBRATION_REQUIRED Persistence does not create a candidate alone.

### S5-C — first knowledge

Initial `candidate_first_knowledge_at=T`; replay/later trigger keeps T.

`created_at`/event date/vendor date do not substitute.

Future T+1 evidence does not change first-knowledge trigger set.

### S5-D — provenance

Contract and expiry triggers preserve source IDs and time fields without substitution.

Expiry trigger fabricates no contract.

Removed/Deep-Dive families never persist as triggers.

### S5-E — idempotence/read-only

Same candidate occurrence replay → one candidate.

Duplicate logical trigger input → one trigger.

Repeated GET → zero writes and unchanged row counts.

### S5-F — predecessor invariants

Existing Stage 4 seven-ticker, no-lookahead, duplicate-evidence, removed-route, Deep-Dive and Stage 2/3 regression tests remain green.

### S5-G — stage boundaries

Repository search confirms no Stage 6 Balanced Model or Forward Outcome implementation was added.

---

# 26. Regression suite

Run:

1. focused Stage 5 tests;
2. Stage 4A focused tests;
3. Stage 4B focused tests;
4. Stage 2/3 regressions;
5. full backend suite;
6. Ruff;
7. glossary/null-safety if API-visible fields changed;
8. frontend lint/build only if frontend/shared typing changed;
9. `python -m alembic heads`;
10. offline PostgreSQL upgrade/downgrade SQL;
11. `git diff --check`.

No Nightwatch or external application/API calls.

---

# 27. Completion report

Create/return:

```text
NIGHTWATCH_VNEXT_STAGE5_PRODUCT_CANDIDATE_PERSISTENCE_COMPLETION_REPORT_20260818.md
```

Required headline:

```text
STAGE5_RESULT=PASS/PASS_WITH_CARRIED_ITEMS/HOLD/FAIL
```

Return at least:

```text
PRODUCT_CANDIDATE_PERSISTED=YES/NO
PRODUCT_CANDIDATE_TRIGGER_PERSISTED=YES/NO
CANDIDATE_FIRST_KNOWLEDGE_PHYSICAL=YES/NO
CANDIDATE_MATERIALIZATION_IDENTITY=
CROSS_RUN_CANDIDATE_LIFECYCLE=DEFERRED_NO_AUTO_MERGE

CANDIDATE_FIRST_KNOWLEDGE_IMMUTABLE=YES/NO
CREATED_AT_USED_AS_FIRST_KNOWLEDGE=YES/NO
EVENT_DATE_USED_AS_FIRST_KNOWLEDGE=YES/NO
LATER_TRIGGER_CAN_REDATE_CANDIDATE=YES/NO

TRIGGER_SOURCE_IDENTITY_PRESERVED=YES/NO
SOURCE_FIRST_RECEIVED_PRESERVED=YES/NO
VENDOR_LOCAL_TIME_SEPARATION_PRESERVED=YES/NO
EXPIRY_TRIGGER_FABRICATES_CONTRACT=YES/NO

QUALIFYING_TICKERS=
PERSISTED_PRODUCT_CANDIDATE_COUNT=
DEEP_DIVE_SELECTED_TICKER_COUNT=
OMITTED_VALID_PRODUCT_CANDIDATES=

FULL_ANOMALY_POOL_PERSISTED=YES/NO
QUALIFYING_ANOMALY_COUNT_PRESERVED=YES/NO
SUPPORTING_PERSISTENCE_DISTINGUISHED=YES/NO

CANDIDATE_REPLAY_DUPLICATION_FOUND=YES/NO
TRIGGER_REPLAY_DUPLICATION_FOUND=YES/NO
GET_CAUSES_CANDIDATE_WRITES=YES/NO

PHASE2A_SCORING_CHANGED=YES/NO
STAGE6_BALANCED_MODEL_STARTED=YES/NO
FORWARD_OUTCOME_STARTED=YES/NO
DASHBOARD_REDESIGN_STARTED=YES/NO

MIGRATION_CREATED=YES
ALEMBIC_HEAD=
ALEMBIC_SINGLE_HEAD=YES/NO
HISTORICAL_BACKFILL_PERFORMED=YES/NO
ISOLATED_POSTGRES_RUNTIME_VERIFIED=YES/NO
REMOTE_MIGRATION_RUN=NO
```

Expected healthy semantic flags:

```text
CANDIDATE_FIRST_KNOWLEDGE_IMMUTABLE=YES
CREATED_AT_USED_AS_FIRST_KNOWLEDGE=NO
EVENT_DATE_USED_AS_FIRST_KNOWLEDGE=NO
LATER_TRIGGER_CAN_REDATE_CANDIDATE=NO
EXPIRY_TRIGGER_FABRICATES_CONTRACT=NO
CANDIDATE_REPLAY_DUPLICATION_FOUND=NO
TRIGGER_REPLAY_DUPLICATION_FOUND=NO
GET_CAUSES_CANDIDATE_WRITES=NO
PHASE2A_SCORING_CHANGED=NO
STAGE6_BALANCED_MODEL_STARTED=NO
FORWARD_OUTCOME_STARTED=NO
DASHBOARD_REDESIGN_STARTED=NO
HISTORICAL_BACKFILL_PERFORMED=NO
```

Also report exact files/diff/tests and carried items.

Authorization ledger:

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

Finally:

```text
STAGE6_READY=YES/NO
NEXT_AUTHORIZED_STAGE=NONE
```

Do not begin Stage 6.

---

# 28. Hard STOP conditions

STOP/HOLD if:

- base is not `84b27b46311c35006def006621fe534b96c690d1`;
- accepted Stage 4 invariants are missing;
- no stable authoritative successful-scan/materialization identity exists;
- candidate persistence requires inventing cross-run lifecycle/re-entry semantics;
- candidate first knowledge cannot be established prospectively without guessing;
- implementation requires Phase 2A threshold/score changes;
- implementation requires numeric Persistence freshness guess;
- implementation requires Stage 6 work;
- implementation requires Forward Outcome;
- migration creates a second Alembic head;
- migration rewrites historical evidence;
- Nightwatch or remote DB access is required.

Return HOLD with exact reason. Do not repair by broadening scope.

---

# 29. Authorization summary

Authorized:

```text
ProductCandidate persistence
ProductCandidateTrigger persistence
physical immutable candidate_first_knowledge_at
additive Stage 5 migration
successful-scan materialization integration
minimal backend read/repository support
focused tests + regressions
```

Not authorized:

```text
Phase 2A redesign
Stage 6 Balanced Model
dashboard redesign
Forward Outcome
Actionability
Trade Expression
universe expansion
Radar/OI cron activation
Persistence numeric calibration
Nightwatch calls
remote DB/migrations
push/PR/merge
```

At completion:

```text
NEXT_AUTHORIZED_STAGE=NONE
```

STOP.
