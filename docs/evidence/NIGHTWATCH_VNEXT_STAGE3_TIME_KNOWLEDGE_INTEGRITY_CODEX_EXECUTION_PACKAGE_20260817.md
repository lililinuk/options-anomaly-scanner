# Nightwatch Scanner vNext — Stage 3 Time / Knowledge Integrity Foundation — Codex Execution Package
**Date:** 2026-08-17
**Stage:** 3 — TIME / KNOWLEDGE INTEGRITY FOUNDATION
**Executor:** Codex implementation engineer
**Authorization:** Stage 3 only
**Authoritative baseline:** `NIGHTWATCH_SCANNER_VNEXT_INTEGRATED_SPEC_PROMPT_20260817(1).md` — v0.1 FOUNDER APPROVED
**Required predecessor evidence:** Stage 1 accepted; Stage 2 accepted as `PASS_WITH_CARRIED_ITEMS`

---

# 0. Stage 3 Objective

Stage 3 establishes the time / knowledge integrity foundation required before Phase 2A vNext, ProductCandidate persistence, Phase 2B vNext, Forward Outcome, or Actionability can safely rely on historical/current observations.

This package authorizes implementation of the Stage 3 items already approved in the integrated spec:

1. immutable `source_first_received_at`;
2. immutable `candidate_first_knowledge_at` semantics/foundation;
3. explicit vendor-time vs local-capture-time separation;
4. fix reprocessing freshness so stale vendor evidence cannot become fresh merely because a new DB row was created;
5. explicit Phase 2B evaluation identity:
   - `FIRST_KNOWLEDGE_BASELINE`
   - `REFRESH`
6. additive migrations only;
7. no guessed reconstruction of historical timestamps.

This is a foundation package.

It does not authorize Phase 2A vNext candidate grouping, ProductCandidate/ProductCandidateTrigger persistence, Phase 2B Balanced Model, daily pipeline changes, Forward Outcome, or Actionability.

---

# 1. Documents for a Fresh Codex Conversation

Provide Codex these files before execution:

## Required

1. `NIGHTWATCH_SCANNER_VNEXT_INTEGRATED_SPEC_PROMPT_20260817(1).md`
   - Founder-approved normative architecture baseline.

2. `NIGHTWATCH_VNEXT_STAGE1_READONLY_PROOF_GATE_REPORT_20260817.md`
   - Current-HEAD time/provenance evidence and carried unresolved items.

3. Stage 2 Completion Report
   - Paste the complete Stage 2 report verbatim if it exists only in chat.

4. `NIGHTWATCH_VNEXT_STAGE3_TIME_KNOWLEDGE_INTEGRITY_CODEX_EXECUTION_PACKAGE_20260817.md`
   - This package.

## Optional supporting evidence

5. `NIGHTWATCH_SCANNER_INDEPENDENT_AUDIT_20260817(1).md`

Do not require the old 2026-08-15 handoff, Phase 2A vNext decision file, or both Phase 2B fresh-review reports unless Codex discovers a concrete ambiguity not resolved by the integrated spec.

---

# 2. Authority Hierarchy

Use:

1. Founder-approved Integrated Spec
2. This Stage 3 Execution Package
3. Accepted Stage 2 Completion Report
4. Stage 1 Evidence Report
5. Current repository code
6. Historical audit only as supporting evidence

The repository is authoritative for implementation detail, but it does not override approved product/time semantics.

If current code materially conflicts with approved Stage 3 assumptions, STOP and report the conflict rather than silently redesigning the specification.

---

# 3. Hard Authorization Boundary

## Authorized

- Read the repository broadly.
- Perform read-only repository orientation before editing.
- Inspect git/branch/HEAD/status.
- Modify files strictly necessary for Stage 3.
- Add additive schema/model fields/tables/indexes if required by approved Stage 3 semantics.
- Create corresponding migration(s).
- Add/update local tests.
- Run migrations/tests only against local/ephemeral/test databases.
- Use mocks/fakes/fixtures.
- Update Stage 3-specific technical documentation/evidence.
- Refactor narrowly where required to enforce approved invariants.

## Not authorized

- No paid Nightwatch API calls.
- No MAG7 scan.
- No Phase 2B live refresh.
- No archive collection.
- No GitHub workflow dispatch.
- No remote Supabase/dev/prod DB writes or migrations.
- No historical repair/backfill against any remote DB.
- No rewriting accepted historical evidence.
- No guessing historical first-receipt or first-knowledge timestamps.
- No Phase 2A vNext implementation.
- No `ProductCandidate` / `ProductCandidateTrigger` implementation; that remains Stage 5.
- No Phase 2B Balanced Model implementation; that remains Stage 6.
- No daily pipeline/scheduler changes; Stage 4A.
- No Persistence/0DTE/Structure/Cluster fixes; Stage 4A/4B.
- No Candidate-first Dashboard redesign; Stage 7.
- No N1 live heatmap removal; Stage 6 after proof.
- No IV Rank semantic resolution beyond preserving existing provenance correctly.
- No Forward Outcome implementation.
- No Actionability implementation.
- No Trade Expression implementation.
- No commit/push/PR/merge unless separately authorized by the founder.

Expected external effects:

```text
NIGHTWATCH_REQUESTS=0
PAID_UNITS=0
REMOTE_DB_WRITES=0
WORKFLOWS_DISPATCHED=0
```

---

# 4. Critical Semantic Invariants

## 4.1 Source first receipt

`source_first_received_at` means the earliest authoritative local receipt time of the same source-evidence identity.

Properties:
- immutable once known;
- reprocessing does not move it forward;
- later DB row creation time is not first receipt;
- if historical evidence cannot establish it authoritatively, it remains `NULL / UNRESOLVED`;
- do not populate it from `captured_at`, `created_at`, or `evaluated_at` merely because those values exist.

Where existing `RawVendorPayload.received_at` already provides authoritative first-receipt evidence, reuse/reference it rather than manufacturing a competing timestamp.

## 4.2 Candidate first knowledge

`candidate_first_knowledge_at` means the first time the system had all admissible evidence required, under the then-current materialization rules, to materialize the user-facing Product/Ticker Candidate.

Properties:
- immutable;
- rule/version provenance must be preserved;
- later triggers do not move first-known time forward;
- later re-evaluation does not rewrite it;
- historical value may be `NULL / UNRESOLVED`;
- do not infer it from event date alone.

Important Stage boundary:

Stage 3 creates the foundation/contract for candidate-first-knowledge semantics, but Stage 5 creates the actual first-class `ProductCandidate` / `ProductCandidateTrigger` entity layer.

Do not prematurely implement Stage 5.

If no appropriate current record exists on which to persist `candidate_first_knowledge_at` without creating ProductCandidate early, implement the approved storage/interface foundation necessary for later Stage 5 and document the deferred materialization point. Do not invent a temporary product entity that will be replaced later.

## 4.3 Vendor/local separation

Keep distinct:

```text
vendor_observed_at
local_captured_at
```

Rules:
- vendor time is vendor-provided analytical/as-of time;
- local capture is when our system received/captured the payload;
- vendor time may be NULL;
- vendor time MUST NOT silently fall back to local time under one field;
- UI/workspace semantics must not label local capture as vendor observation.

## 4.4 Evaluation identity

Phase 2B context evaluation semantics must distinguish:

```text
FIRST_KNOWLEDGE_BASELINE
REFRESH
```

Rules:
- baseline is the frozen research snapshot associated with first knowledge;
- refreshes are later evaluations;
- a refresh never overwrites/replaces the baseline;
- both remain separately identifiable;
- this Stage implements identity/foundation, not the Stage 6 Balanced Model.

## 4.5 Freshness

Freshness must be based on authoritative source/vendor information and/or source identity — not solely on the DB row's latest `created_at`.

A reprocessed row generated today from a preserved stale payload must remain stale with respect to the source evidence.

No timestamp laundering.

## 4.6 Live / Research separation

Do not introduce any path by which live runtime could consume future Forward Outcome.

No Forward Outcome table/model/repository may be queried by live Stage 3 code.

Train/serve information-time parity remains a red line.

---

# 5. Mandatory Read-Only Repository Orientation

Before editing anything:

1. Read the approved spec and prior-stage evidence.
2. Inspect repository top-level structure.
3. Map:
   - raw vendor ingestion/persistence;
   - `RawVendorPayload`;
   - Radar/activity/OI storage;
   - Phase 2B ticker context/evaluation models;
   - Phase 2B cache/reprocess path;
   - current timestamp/as-of fields;
   - SQLAlchemy models;
   - Alembic migration conventions;
   - tests/fixtures;
   - any repository/service layer for Phase 2B context.
4. Trace every write path for fields that Stage 3 may alter.
5. Trace how current `created_at`, `captured_at`, `observed_at`, `generated_at`, `evaluated_at`, and vendor dates are used.
6. Identify whether Stage 2 changes are present and intact.
7. Identify the minimum additive schema needed.

Then report before implementation:

```text
REPOSITORY_ORIENTATION
- raw payload lineage:
- current local receipt source:
- current vendor-time sources:
- current Phase 2B context persistence:
- current evaluation identity:
- current freshness/cache logic:
- migration convention:
- Stage 2 G1 status:
- Stage 2 G2 status:
```

Then provide:

```text
AUTHORIZED_FILES_PROPOSED:
- file: reason
...
```

Reading broadly does not authorize writing broadly.

READ BROADLY; WRITE NARROWLY.

---

# 6. Preflight / Worktree Protection

Record:

```text
REPO_ROOT=
BRANCH=
HEAD_BEFORE=
WORKTREE_STATE=
```

Stage 2 was performed on:

```text
branch = fix/oi-change-rollover-workflow-context
HEAD   = 8a2573f406d1011bc06970a34cf26e506bf29e97
```

Stage 2 itself did not commit, so its approved changes may still exist only in the dirty working tree.

Treat all Stage 2 modifications as protected predecessor work.

Do not:
- reset;
- checkout;
- clean;
- stash;
- revert;
- normalize line endings;
- overwrite Stage 2 behavior.

If Stage 2 changes are missing, partially present, or materially different from the accepted completion report, STOP before Stage 3 implementation.

If current HEAD moved but predecessor diffs are intact, document it and continue only if Stage 3-relevant code is compatible.

---

# 7. Workstream A — Canonical Time Vocabulary / Schema

## 7.1 Inventory before schema changes

Create a completion-report table mapping:

```text
CURRENT FIELD
TABLE / MODEL
ACTUAL WRITE SEMANTIC
TARGET SEMANTIC
KEEP / RENAME-IN-API / ADD-FIELD / DEPRECATE
```

At minimum include:
- `RawVendorPayload.received_at`
- `RawVendorPayload.observed_at`
- Radar `captured_at`
- Radar `ny_market_date`
- `ScanRun.started_at`
- `ScanRun.market_date`
- `ContractScanObservation.observed_at`
- `ExpiryObservation.observed_at`
- `Phase2bTickerContextSnapshot.created_at`
- source-specific as-of/date fields inside Phase 2B payload normalization
- `Phase2bCandidateEvaluation.evaluated_at`

## 7.2 Additive-only migration

Implement only fields/metadata needed to make approved time semantics explicit and enforceable.

Requirements:
- additive migration only;
- no destructive rename/drop;
- old fields remain readable;
- legacy records do not receive invented values;
- new nullable fields are acceptable where historical authority is absent;
- use constraints/enums/indexes only where they encode approved invariants safely.

Do not assign final future Phase 2A/2B production spec numbers unless separately authorized.

If an enum is used for evaluation identity, it must represent at least:

```text
FIRST_KNOWLEDGE_BASELINE
REFRESH
```

Legacy/unknown handling must not fabricate a baseline classification.

---

# 8. Workstream B — Source First Receipt

Implement a reliable method/API/domain semantic for:

```text
source_first_received_at
```

Requirements:
1. Prefer authoritative existing lineage such as `RawVendorPayload.received_at`.
2. Preserve earliest receipt, not latest processing.
3. Repeated ingestion/reprocessing cannot move first receipt forward.
4. Distinct source identities must not be collapsed without an explicit identity rule.
5. Legacy rows with broken/missing linkage remain NULL/UNRESOLVED.
6. Do not perform historical DB repair.

Required tests:

### S3-A1
Same source evidence processed twice:
`source_first_received_at` remains T0.

### S3-A2
Later reprocessing at T1 > T0:
first receipt remains T0.

### S3-A3
Missing authoritative source lineage:
NULL/UNRESOLVED, not inferred from `created_at`.

### S3-A4
New source evidence:
new evidence receives its own valid first receipt.

---

# 9. Workstream C — Vendor Time vs Local Capture

Fix the current G4 class of semantic mixing.

Target:

```text
vendor_observed_at = vendor value or NULL
local_captured_at  = local receipt/capture value
```

Requirements:
- no silent fallback;
- no generic field whose label implies vendor time if it can hold local time;
- preserve both where available;
- downstream domain/API types must carry enough metadata to distinguish them;
- legacy unknown remains unknown.

Required tests:

### S3-B1
Vendor timestamp present:
both vendor and local timestamps preserved distinctly.

### S3-B2
Vendor timestamp missing:
`vendor_observed_at is NULL`;
`local_captured_at` remains populated.

### S3-B3
No code path substitutes local capture into vendor-observed field.

### S3-B4
Serialization/API output preserves the distinction where Stage 3-touched APIs expose these values.

Do not redesign final Stage 7 display.

---

# 10. Workstream D — Reprocess Freshness / Cache Integrity (G5)

Current defect:
- Phase 2B ticker context cache uses DB `created_at`;
- reprocessing preserved raw evidence writes a new row with new `created_at`;
- stale vendor evidence can therefore look fresh.

Implement source-aware freshness semantics.

Requirements:
1. A reprocessed row must not become fresh merely because it was recreated.
2. Freshness calculation must use authoritative source/vendor as-of time and/or source identity.
3. If no authoritative freshness timestamp exists:
   - do not invent one;
   - feature may be truthful unknown/partial/unavailable.
4. Preserve context reuse efficiencies where semantically safe.
5. Do not change freshness thresholds except to use the correct timestamp.
6. Do not alter Phase 2B content architecture.

Required tests:

### S3-C1
Old preserved raw payload reprocessed now:
context remains stale relative to old source time.

### S3-C2
Fresh vendor/source evidence:
context can qualify as fresh under existing threshold.

### S3-C3
Missing vendor/source freshness:
does not become fresh solely through `created_at`.

### S3-C4
Repeated reprocessing cannot extend freshness indefinitely.

---

# 11. Workstream E — Baseline vs Refresh Evaluation Identity

Implement explicit evaluation identity foundation:

```text
FIRST_KNOWLEDGE_BASELINE
REFRESH
```

Requirements:
- future newly created baseline can be marked explicitly;
- subsequent evaluations are distinct REFRESH records;
- REFRESH never mutates/replaces baseline;
- legacy rows remain legacy/unknown unless authoritative mapping exists;
- no historical bulk rewrite;
- identity is persisted, not inferred only at render time;
- current v1.2/v2.0/v3.1 structures remain readable and are not destructively migrated.

If the current exact-contract Phase 2B workflow cannot authoritatively determine ProductCandidate first knowledge before Stage 5 exists, implement persistence/type/schema support and a safe creation contract, but do not falsely label current contract evaluations as ProductCandidate `FIRST_KNOWLEDGE_BASELINE`.

Required tests:

### S3-D1
Baseline identity cannot be overwritten by refresh.

### S3-D2
One baseline and later refreshes can coexist.

### S3-D3
Legacy unknown evaluation is not auto-labeled baseline.

### S3-D4
No destructive update to old v1.2/v2.0/v3.1 rows.

---

# 12. Workstream F — Candidate First-Knowledge Foundation

The integrated spec requires immutable:

```text
candidate_first_knowledge_at
```

but Stage 5 creates:

```text
ProductCandidate
ProductCandidateTrigger
```

Therefore Stage 3 must establish the foundation without stealing Stage 5 scope.

Codex must determine the narrowest correct implementation.

Acceptable outcomes:

### Option 1 — shared time/provenance domain support
Introduce reusable immutable first-knowledge helper/schema contract for Stage 5.

### Option 2 — additive nullable foundation on an existing appropriate record
Only if there is an authoritative entity where this belongs without pretending exact-contract evaluation = ProductCandidate.

### Option 3 — physical persistence deferred to Stage 5
If persisting candidate first knowledge now would require a temporary/incorrect entity, implement validation/helper/interface semantics now and defer physical storage to Stage 5.

Do not create ProductCandidate early merely to satisfy the field name.

Completion report must state one:

```text
CANDIDATE_FIRST_KNOWLEDGE_FOUNDATION=IMPLEMENTED_NOW
```

or

```text
CANDIDATE_FIRST_KNOWLEDGE_FOUNDATION=INTERFACE_FOUNDATION_IMPLEMENTED_PHYSICAL_STORAGE_STAGE5
```

Required invariants/tests:
- first knowledge never moves forward after set;
- later anomaly arrival cannot overwrite it;
- unknown historical value remains NULL;
- materialization-rule version must be representable alongside it when Stage 5 uses the foundation.

---

# 13. Legacy / Historical Data Policy

Use:

```text
KNOWN AUTHORITATIVE
→ preserve / map safely

RECONSTRUCTABLE WITH AUTHORITATIVE PROVENANCE
→ may be exposed as RECONSTRUCTED only if genuinely proven

UNKNOWN / BROKEN LINEAGE
→ NULL / UNRESOLVED

SUSPECT
→ remain flagged, not repaired
```

Default for Stage 3:

> Do not backfill historical first-knowledge timestamps.

Never use:
- migration execution time;
- current `created_at`;
- event date;
- scan date

as surrogate first knowledge merely to fill a column.

No remote historical backfill is authorized.

---

# 14. Stage 1 Carried Items

Carry unless resolved locally without scope expansion:

- N1 runtime heatmap distribution → Stage 6 proof/removal path.
- IV Rank vendor semantics → `WITHHOLD_PENDING_PROVENANCE`.
- Historical first-knowledge DB sampling → later DB-capable proof.
- G2 overwritten historical Radar identity → UNRESOLVED where unrecoverable.
- 0DTE row counts/classification → Stage 4A/later proof.
- G9 contaminated Persistence evaluations → later exclusion from clean research sample.
- T1–T6 → do not invent definitions.

Stage 3 may improve timestamp/provenance plumbing for IV Rank but may not invent its vendor semantics.

---

# 15. Explicit Non-Goals

Do not implement or alter:

```text
Phase 2A vNext discovery families
Contract Persistence recency/no-lookahead
0DTE canonical EOD pipeline
Daily archive scheduler
Contract open_interest_as_of pipeline
Structure/Cluster scoring
Neighbor Ratio
Legacy score removal
ProductCandidate/ProductCandidateTrigger entities
Phase 2B Balanced Model blocks
GEX labels / heatmap removal
Candidate-first dashboard
Universe expansion
Forward Outcome metrics
Actionability
Trade Expression
Radar threshold / score anchors
GEX scheduler
oi-change rollover experiment
```

Stage 2 G1/G2 behavior must remain intact.

---

# 16. Migration Safety Requirements

1. Additive migrations only.
2. No DROP COLUMN/TABLE.
3. No destructive rename.
4. No mass historical UPDATE to manufacture time values.
5. Historical-facing new time fields should be nullable unless authority exists.
6. Migration downgrade may remove only Stage 3-added schema in local/test contexts; it must not imply historical data rewriting.
7. Add indexes only for actual Stage 3 access patterns.
8. Do not run migration against remote Supabase/dev/prod.
9. Run upgrade/downgrade only on isolated local/test DB if available.
10. If no safe local DB exists, validate migration statically/unit-level and report runtime migration check as skipped.

---

# 17. Authorized File Discipline

Before edits, declare exact files and reasons.

Expected categories may include:

```text
backend/app/db/models.py
backend/alembic/versions/<stage3_additive_migration>.py
backend/app/confirmation/service.py
backend/app/confirmation/domain.py
backend/app/confirmation/... relevant repository/state modules
backend/app/scanner/... only if required for time/provenance interface
backend/app/api/routes/... only if needed to preserve timestamp identity
backend/tests/...
docs/evidence/<Stage3 report> if repository evidence is standard
```

These are examples, not blanket authorization.

Avoid formatting-only churn.

---

# 18. Verification Requirements

At minimum verify:

## Schema/migration
- migration syntax/imports;
- model metadata;
- local/test upgrade if available;
- no historical value fabrication.

## Time semantics
- source first receipt immutable;
- vendor/local separation;
- NULL behavior when vendor time absent;
- no local fallback.

## Freshness
- stale preserved source remains stale after reprocess;
- fresh source remains fresh;
- created_at alone cannot refresh evidence.

## Evaluation identity
- baseline vs refresh distinct;
- refresh cannot overwrite baseline;
- legacy rows not auto-promoted.

## Candidate-first-knowledge foundation
- immutability contract;
- unknown remains NULL;
- no premature ProductCandidate implementation.

## Regression
- Stage 2 G1 tests still pass;
- Stage 2 G2 tests still pass;
- focused Phase 2B tests;
- complete backend suite if safe;
- Ruff/type checks for touched files;
- frontend tests only if frontend files are touched.

Absolutely no real vendor calls or remote DB writes.

---

# 19. Required Invariant Tests / Static Guards

Where practical, add tests asserting:

```text
1. vendor_observed_at != implicit(local_captured_at fallback)
2. source_first_received_at cannot be advanced by reprocess
3. stale raw evidence + new DB row != fresh evidence
4. refresh != baseline overwrite
5. historical unknown != guessed timestamp
6. no Stage 3 live code queries Forward Outcome
```

Do not create unnecessary infrastructure solely for test #6.

---

# 20. Diff Hygiene

Before final report:

1. show `git status --short`;
2. isolate Stage 3 diff from:
   - pre-existing user dirt;
   - accepted uncommitted Stage 2 changes;
3. show Stage 3-only `git diff --stat` if possible;
4. confirm no accidental:
   - Stage 2 revert;
   - line-ending normalization;
   - scheduler edits;
   - frontend redesign;
   - scoring changes;
   - paid-call additions;
   - secrets;
   - remote DB config changes.

Because Stage 2 may be uncommitted, explicitly identify which working-tree changes predated Stage 3.

---

# 21. Required Completion Report

## A. EXECUTIVE RESULT

```text
STAGE3_RESULT =
PASS
PASS_WITH_CARRIED_ITEMS
HOLD
```

## B. PREFLIGHT / REPOSITORY ORIENTATION

Report:
- repo root
- branch
- HEAD before/after
- pre-existing dirty state
- Stage 2 predecessor changes detected
- Stage 3 authorized files
- architecture map relevant to Stage 3

## C. TIME FIELD INVENTORY

```text
CURRENT FIELD | ACTUAL SEMANTIC | TARGET SEMANTIC | ACTION
```

## D. MIGRATION / SCHEMA CHANGES

- exact migration;
- new columns/tables/enums/indexes;
- nullable/default behavior;
- why additive;
- historical treatment;
- local migration verification.

## E. SOURCE FIRST RECEIPT

- implementation;
- source identity;
- immutability;
- unresolved legacy behavior;
- tests.

## F. VENDOR / LOCAL TIME SEPARATION

- prior mixed paths;
- new behavior;
- NULL semantics;
- API/domain effects;
- tests.

## G. REPROCESS FRESHNESS

- prior created_at laundering path;
- new freshness anchor;
- missing-source behavior;
- tests.

## H. BASELINE / REFRESH IDENTITY

- persisted representation;
- baseline immutability;
- refresh coexistence;
- legacy rows;
- tests.

## I. CANDIDATE FIRST-KNOWLEDGE FOUNDATION

Return exactly one:

```text
CANDIDATE_FIRST_KNOWLEDGE_FOUNDATION=IMPLEMENTED_NOW
```

or

```text
CANDIDATE_FIRST_KNOWLEDGE_FOUNDATION=INTERFACE_FOUNDATION_IMPLEMENTED_PHYSICAL_STORAGE_STAGE5
```

Then explain why.

## J. HISTORICAL DATA TREATMENT

Use categories:

```text
AUTHORITATIVE
RECONSTRUCTED
NULL_UNRESOLVED
SUSPECT
```

No remote repair.

## K. TEST EVIDENCE

List commands/suites/results.

Explicitly include Stage 2 G1/G2 regression status.

## L. CARRIED ITEMS

List unresolved items and destination stage.

## M. OUT-OF-SCOPE FINDINGS

Anything noticed but intentionally not changed.

## N. DIFF SUMMARY

```text
stage3 files changed:
lines added:
lines removed:
migration files:
workflow files:
frontend files:
```

## O. AUTHORIZATION COMPLIANCE

Return exactly:

```text
NIGHTWATCH_REQUESTS=<integer>
PAID_UNITS=<integer>
REMOTE_DB_WRITES=<integer>
REMOTE_MIGRATIONS_RUN=<integer>
WORKFLOWS_DISPATCHED=<integer>
COMMITS_CREATED=<integer>
PUSHES=<integer>
PRS_CREATED=<integer>
```

Expected all zero unless separately authorized.

## P. SPEC IMPACT

```text
REOPEN_PHASE2A_VNEXT=YES/NO
REOPEN_PHASE2B_MODEL_B=YES/NO
SPEC_AMENDMENT_REQUIRED=YES/NO
STAGE_ORDER_CHANGE_REQUIRED=YES/NO
```

## Q. NEXT ACTION

Return:

```text
NEXT_AUTHORIZED_STAGE = NONE
```

State:

> Stage 4A / 4B may be recommended after founder review, but neither is authorized by this Stage 3 package.

Do not continue into Stage 4A or Stage 4B.

---

# 22. HOLD / STOP Conditions

STOP and report `HOLD` if:

1. correct Stage 3 semantics require destructive migration;
2. the only way to populate first knowledge is to guess historical times;
3. implementing `candidate_first_knowledge_at` correctly requires prematurely implementing ProductCandidate;
4. current relevant repository code materially differs from the accepted Stage 2 state;
5. Stage 3 would require remote DB writes;
6. tests would require paid Nightwatch traffic;
7. proper freshness semantics cannot be represented without reopening approved architecture;
8. migration/versioning rules conflict with the integrated spec;
9. Stage 3 changes would require deleting/replacing old Phase 2B layers rather than additive coexistence.

Do not solve a HOLD condition by expanding scope.

---

# 23. Final Principle

Stage 3 must establish that these remain distinct facts:

```text
WHAT HAPPENED
WHEN THE VENDOR OBSERVED IT
WHEN OUR SYSTEM FIRST RECEIVED IT
WHEN THE SYSTEM FIRST KNEW ENOUGH
WHEN CONTEXT WAS EVALUATED
```

A later reprocess may create a new evaluation.

It may never rewrite history.
It may never manufacture knowledge time.
It may never make stale evidence fresh.
It may never introduce future information into live runtime.
