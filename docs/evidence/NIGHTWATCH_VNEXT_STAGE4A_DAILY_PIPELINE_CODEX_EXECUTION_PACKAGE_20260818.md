# Nightwatch Scanner vNext — Stage 4A Daily Data Pipeline — Codex Execution Package

**Date:** 2026-08-18  
**Stage:** 4A — DAILY DATA PIPELINE  
**Executor:** Codex implementation engineer  
**Authorization:** Stage 4A only  
**Branch:** `vnext/stage4a-daily-pipeline`  
**Worktree:** `F:\options-anomaly-scanner-stage4a`  
**Required base SHA:** `4f0edba28dc6939e1d60ba176d0281189e5ee67d`

---

# 0. Purpose

Implement the vNext daily Phase 2A data foundation without changing Phase 2A discovery logic.

Stage 4A owns the operational/data-integrity work assigned by the founder-approved integrated spec:

- **G19** — add a durable scheduled Phase 2A daily accumulation path;
- **G12** — prevent intraday 0DTE first-writer data from contaminating the canonical session-complete historical baseline;
- **G25** — retain contract-level `open_interest_as_of` instead of discarding it;
- **E1** — stop using one `DailyCollectionCoverage.observation_date` field for two different meanings;
- preserve append-only/no-lookahead/time-integrity foundations already accepted through Stage 3.

Stage 4A is a data/operations package. It does **not** implement Phase 2A vNext candidate/discovery semantics; that is Stage 4B.

---

# 1. Required Documents for a Fresh Codex Window

Provide and read completely:

1. `NIGHTWATCH_SCANNER_VNEXT_INTEGRATED_SPEC_PROMPT_20260817(1).md`
   - founder-approved architecture baseline.

2. `PHASE2A_VNEXT_DECISION_HANDOFF_20260817.md`
   - normative Phase 2A vNext decision and daily-pipeline requirements.

3. `NIGHTWATCH_VNEXT_STAGE1_READONLY_PROOF_GATE_REPORT_20260817.md`
   - current-head proof of G12/G19/G25/E1 and historical limitations.

4. `NIGHTWATCH_VNEXT_STAGE3_ACCEPTED_CHECKPOINT_COMPLETION_REPORT_20260818.md`
   - proves the common accepted checkpoint and worktree isolation.

5. This file:
   `NIGHTWATCH_VNEXT_STAGE4A_DAILY_PIPELINE_CODEX_EXECUTION_PACKAGE_20260818.md`

Also inspect the current repository, including the existing OI-change rollover-timing experiment artifacts/workflow. Do not rely on memory or invent timing evidence.

---

# 2. Authority Order

1. Founder-approved Integrated Spec.
2. Phase 2A vNext Decision Handoff where consistent with the later integrated spec.
3. This Stage 4A package.
4. Accepted Stage 3/checkpoint state.
5. Stage 1 evidence.
6. Current repository for implementation detail.

The later Integrated Spec supersedes older documents on stage boundaries.

---

# 3. Preflight — Must Match the Accepted Common Base

Before editing:

```text
REPO_ROOT=F:\options-anomaly-scanner-stage4a
EXPECTED_BRANCH=vnext/stage4a-daily-pipeline
EXPECTED_HEAD=4f0edba28dc6939e1d60ba176d0281189e5ee67d
EXPECTED_WORKTREE=CLEAN
```

Verify all four.

Also verify:

- Stage 2 G1/G2 fixes are present.
- Stage 3 time/knowledge/freshness foundation is present.
- Alembic current repository head begins from the accepted Stage 3 migration state.
- no Stage 4B implementation is mixed into this worktree.
- the Dealer/GEX scheduler remains unchanged.

If the branch/head/worktree is not the expected isolated baseline, **STOP**.

---

# 4. Mandatory Read-Only Repository Orientation

Before implementation, map:

```text
archive-mag7-daily CLI
daily pipeline orchestration
daily run / coverage models
expiry activity capture
0DTE snapshot write paths
interactive scan 0DTE write path
contract chain / OI archive
open_interest_as_of parser path
Radar / oi-change collection path
GitHub workflow conventions
trading-calendar helpers
advisory-lock / retry-suppression semantics
OI-change rollover-timing experiment
```

Report briefly:

```text
STAGE4A_ORIENTATION
- daily CLI:
- activity source:
- Radar/OI source:
- 0DTE current identity:
- contract OI identity:
- coverage semantics:
- workflow pattern:
- rollover experiment status/evidence available:
```

Then declare exact:

```text
AUTHORIZED_FILES_PROPOSED:
- file: reason
```

Read broadly; write narrowly.

---

# 5. Hard Authorization Boundary

## Authorized

- Modify Stage 4A data-pipeline/backend code.
- Add focused additive schema migration(s) required for Stage 4A.
- Add/update tests.
- Add a durable GitHub Actions workflow for the Phase 2A daily archive.
- Add safe scheduler/trading-session guards.
- Use local/ephemeral test DBs.
- Run local tests/lint/static workflow validation.
- Inspect existing rollover research evidence read-only.

## Forbidden

- No real Nightwatch requests during implementation/verification.
- No paid units.
- No remote Supabase/dev/prod DB writes or migrations.
- No workflow dispatch.
- No GitHub push/PR/merge.
- No Stage 4B Phase 2A discovery/candidate changes.
- No ProductCandidate/ProductCandidateTrigger persistence (Stage 5).
- No Phase 2B Balanced Model (Stage 6).
- No Candidate-first dashboard redesign (Stage 7).
- No Forward Outcome / Actionability / Trade Expression.
- No Dealer/GEX scheduler change.
- No new universal score/threshold.
- No deletion or rewriting of accepted history.
- No fabricated contract closure when a contract disappears.
- No treating missing as zero.

---

# 6. Parallel-Branch Migration Ownership Rule

Stage 4A is the **migration owner for the Stage 4A/4B parallel tranche**.

Reason: both Stage 4 branches start from the same accepted Stage 3 Alembic head. Competing independent migrations would create avoidable multi-head/numbering conflicts.

Therefore:

- Stage 4A may create the next additive migration(s) when required.
- Stage 4B is instructed not to create an Alembic migration unless it stops for founder coordination.
- Use the repository's real migration chain; do not blindly assume a revision number.
- Do not run migration remotely.

Migration rules:

```text
additive/versioned
legacy rows preserved
no guessed timestamps
no historical mass rewrite to manufacture meaning
nullable/legacy-unknown where authority is absent
```

If canonical 0DTE semantics cannot be implemented without destructive history rewriting, use an additive/versioned representation instead.

---

# 7. Workstream A — DailyCollectionCoverage Semantic Split (E1)

Current defect:

one `DailyCollectionCoverage.observation_date` is used for different meanings across activity and Radar/OI collection.

Target:

each date/time field has exactly one meaning.

At minimum establish distinct semantics for:

```text
activity_market_date
vendor_oi_date
```

or semantically equivalent explicit fields.

Requirements:

- preserve legacy `observation_date` read compatibility if needed;
- new code must not overload one field with both meanings;
- historical rows with ambiguous old meaning remain legacy/unknown rather than guessed;
- serializers/logging/coverage queries must use the correct field;
- NY market-date semantics and vendor OI date remain distinct.

Tests must prove activity and OI/Radar runs cannot silently write different meanings into the same new field.

---

# 8. Workstream B — 0DTE Canonical Session-Complete History (G12)

Current proven defect:

- interactive scan can write the first row for `(ticker, observation_date)`;
- later daily collector skips because the row already exists;
- therefore an intraday snapshot can become the historical 0DTE baseline observation.

Stage 1 proved origin linkage is distinguishable:

```text
scan_run_id  → interactive origin
daily_run_id → daily collector origin
```

but daily origin alone does **not** prove session-complete EOD.

## Target semantic

Future 0DTE evidence must distinguish at least:

```text
PROVISIONAL_INTRADAY
CANONICAL_SESSION_COMPLETE
LEGACY_OR_AMBIGUOUS
```

Names may follow repository conventions, but semantics must be explicit.

Requirements:

1. interactive observations may be persisted for research;
2. interactive observations never block later canonical session-complete capture;
3. only canonical session-complete observations enter the canonical 20-observation 0DTE historical baseline;
4. legacy/ambiguous observations are excluded from clean calibration by default;
5. no old row is deleted;
6. no old row is guessed to be EOD solely because its clock time looks late;
7. daily collector marks canonical only after an authoritative trading-session-complete guard passes;
8. early-close sessions use the actual NYSE session close, not a hardcoded normal close;
9. holiday/weekend/non-trading sessions do not create canonical observations.

If current table uniqueness makes #2 impossible, use an additive/versioned persistence design rather than rewriting an existing intraday row into an EOD row.

Required tests:

- provisional intraday + later canonical can coexist;
- provisional does not count toward 20-observation baseline;
- canonical does count;
- legacy/ambiguous does not count by default;
- early-close guard;
- non-trading-day skip;
- repeated canonical execution is idempotent;
- missing vendor data remains missing, not zero.

---

# 9. Workstream C — Contract-Level `open_interest_as_of` (G25)

Current defect:

parser receives contract-level `open_interest_as_of`, but archive persistence discards it and contract rows inherit an expiry-level/vendor date.

Target:

preserve the exact contract-level source as-of when provided.

Requirements:

```text
contract open_interest_as_of
≠ expiry-level observation date
≠ local captured_at
```

- persist contract-level value separately;
- keep vendor/local separation from Stage 3;
- legacy records may remain NULL;
- do not manufacture a value when vendor field is absent;
- do not reinterpret existing expiry-level date as contract-level as-of;
- no lookahead query may use a later contract OI observation for an earlier analysis date.

Tests:

- explicit contract as-of survives parser → archive → read path;
- absent contract as-of remains NULL;
- local receipt/capture remains separate;
- multiple contracts may legitimately carry different as-of values;
- no fallback from expiry date into contract as-of field unless the vendor schema explicitly states equivalence and existing authoritative docs prove it.

---

# 10. Workstream D — Durable Daily Phase 2A Workflow (G19)

Create a GitHub Actions workflow for the Phase 2A daily archive using the established operational safety pattern:

```text
contents: read
server-side secrets only
concurrency protection
trading-day/session guard
scheduled + workflow_dispatch support
safe retry/idempotence
no browser/API-key exposure
```

Do not modify `dealer-gex-archive.yml`.

The daily architecture must respect separate publication semantics:

```text
A. same-day / session-complete activity
B. Radar / OI-confirmation data
```

They are not one universal timestamp.

## Critical timing rule

**Do not invent the final Radar/OI cron.**

The repo contains an OI-change rollover-timing experiment whose purpose is to measure publication timing. Inspect its actual evidence.

If the experiment has not yet produced a conclusive founder-accepted publication window:

```text
RADAR_OI_SCHEDULE_ACTIVATION=PENDING_ROLLOVER_EVIDENCE
```

Implement the safe collection mode/workflow plumbing, but do not activate a speculative production Radar/OI cron.

This is an acceptable carried item for Stage 4A implementation completion.

For same-day activity, schedule/guard logic must guarantee the snapshot is **after the actual regular session close** and must be clearly identified as canonical session-complete. Prefer session-calendar-based gating over assuming the Dealer/GEX 15:30 slot.

Do not claim vendor publication readiness unless repository evidence supports it.

## Integration ordering rule

Stage 4A and Stage 4B may be developed in parallel, but **Stage 4B must not be integrated ahead of the Stage 4A data foundation**. If Radar/OI schedule activation remains pending the still-running experiment, report it explicitly so founder integration can be held until the timing gate is resolved.

---

# 11. Preserve Existing Daily-Pipeline Principles

Must remain true:

```text
append-only where practical
UTC persistence
New York market-calendar semantics
vendor timestamp separate from local capture
missing != zero
complete-chain gate for contract OI archive
no fabricated closure
idempotent/retry-safe collection
spec/config/version/hash provenance where already used
```

Do not remove expiry-level historical storage merely because Expiry Persistence is removed from active discovery; retention and active-scoring architecture are different questions.

---

# 12. Stage 3 Regression Requirements

Stage 4A must not break:

```text
source_first_received_at immutability
vendor_observed_at / local_captured_at separation
source-aware freshness
Radar captured_at / ny_market_date stop-bleed
G1 truthful failure semantics
G3 source pinning
evaluation identity foundation
```

Run relevant Stage 2/3 regression tests.

Carried Stage 3 item remains:

```text
MIGRATION_RUNTIME_POSTGRES_VERIFIED=NO
```

If an isolated PostgreSQL instance is available locally, you may execute Stage 3 + Stage 4A migrations there. If not, do not use remote Supabase as a substitute.

---

# 13. Explicit Non-Goals

Do not change:

```text
Radar material gate thresholds
Expiry Activity scoring anchors
0DTE scoring anchors
Contract Persistence scoring anchors
Contract Persistence candidate freshness rule
Phase 2A route/candidate grouping
Expiry Persistence active-route code
Structural Cold Start active-route code
Evidence Breadth
Structure/Cluster presentation
legacy discovery score
Phase 2B
dashboard architecture
GEX scheduler
universe
Forward Outcome
Actionability
Trade Expression
```

Those Stage 4B items must stay out of this worktree.

---

# 14. Verification

Required, as applicable:

- focused pipeline tests;
- 0DTE origin/canonical-baseline tests;
- contract OI as-of tests;
- coverage semantic split tests;
- trading-day/early-close tests;
- idempotence/retry tests;
- workflow syntax/static validation;
- Alembic single-head check;
- offline PostgreSQL migration SQL generation;
- isolated PostgreSQL upgrade/downgrade smoke if locally available;
- complete backend suite if safe;
- Ruff/static checks;
- Stage 2/3 regressions.

No real vendor request and no remote DB write.

---

# 15. Required Completion Report

## A. RESULT

```text
STAGE4A_RESULT=
PASS
PASS_WITH_CARRIED_ITEMS
HOLD
```

## B. PREFLIGHT

```text
BRANCH=
HEAD_BASE=
WORKTREE=
CLEAN_AT_START=
```

Confirm base SHA is exactly `4f0edba28dc6939e1d60ba176d0281189e5ee67d`.

## C. FILES CHANGED

List each file and its reason.

## D. COVERAGE SEMANTICS (E1)

Explain new activity-date vs vendor-OI-date representation and legacy treatment.

## E. 0DTE (G12)

Report:

```text
PROVISIONAL_INTRADAY_BEHAVIOR=
CANONICAL_SESSION_COMPLETE_BEHAVIOR=
LEGACY_AMBIGUOUS_BEHAVIOR=
CANONICAL_BASELINE_FILTER=
```

## F. CONTRACT OI AS-OF (G25)

Show parser → persistence → read provenance.

## G. DAILY WORKFLOW (G19)

Report:

```text
WORKFLOW_FILE=
ACTIVITY_SCHEDULE_OR_GUARD=
RADAR_OI_COLLECTION_MODE=
RADAR_OI_SCHEDULE_ACTIVATION=
ROLLOVER_EVIDENCE_USED=
```

Never label an unvalidated schedule "final".

## H. MIGRATION

```text
MIGRATION_CREATED=YES/NO
ALEMBIC_HEAD=
ISOLATED_POSTGRES_RUNTIME_VERIFIED=YES/NO
REMOTE_MIGRATION_RUN=NO
```

## I. TESTS

Commands/suites/results.

## J. CARRIED ITEMS

Include unresolved Radar/OI timing if applicable.

## K. DIFF

```text
FILES_CHANGED=
LINES_ADDED=
LINES_REMOVED=
WORKFLOW_FILES=
MIGRATION_FILES=
```

## L. AUTHORIZATION COMPLIANCE

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

## M. SPEC IMPACT

```text
REOPEN_PHASE2A_VNEXT=YES/NO
SPEC_AMENDMENT_REQUIRED=YES/NO
STAGE_ORDER_CHANGE_REQUIRED=YES/NO
```

## N. NEXT ACTION

```text
NEXT_AUTHORIZED_STAGE=NONE
```

Do not start Stage 5 or integrate Stage 4B.

---

# 16. Stop Conditions

STOP if:

- base branch/head is wrong;
- Stage 4B changes are present;
- canonical 0DTE would require rewriting accepted history rather than additive/versioned storage;
- the only way to schedule Radar/OI is to invent vendor timing;
- a required test would call Nightwatch;
- remote DB access is required;
- migration would conflict with accepted Stage 3 semantics;
- implementation would modify Dealer/GEX scheduling;
- implementation requires changing Phase 2A analytical thresholds/route logic.

Do not solve a timing-evidence gap by guessing.

---

# 17. Final Principle

Stage 4A exists to make future research data trustworthy and repeatable:

```text
one session
→ one truthful canonical session-complete activity observation
→ one truthful vendor-OI observation when published
→ exact provenance
→ no first-writer contamination
→ no fabricated timing
→ no missing-as-zero
```
