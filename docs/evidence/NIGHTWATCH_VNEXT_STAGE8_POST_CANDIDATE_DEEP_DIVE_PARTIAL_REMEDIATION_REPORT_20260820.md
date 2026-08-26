# Nightwatch vNext — Stage 8 Post-Candidate Deep-Dive PARTIAL Remediation Report

Date: 2026-08-20
Worktree: `F:\options-anomaly-scanner-stage8`
Branch: `vnext/stage8-mag7-observation`
Base HEAD: `3a63eaa1b9069d34199704fe31ac6466e8929d7d`
Execution package SHA-256: `27837492E472A2376398A2509A33AECBF8E982128ACD10A7A34A3569936F3E44`

## Executive result

```text
STAGE8_POST_CANDIDATE_PARTIAL_REMEDIATION_RESULT=PASS
ROOT_CAUSE_ADDRESSED=YES

RUN_LEVEL_PARTIAL_FROM_POST_CANDIDATE_DEEP_DIVE_ONLY=BLOCKED
LEGITIMATE_PREEXISTING_PARTIAL_PRESERVED=YES

DEEP_DIVE_MISSING_STATE_PRESERVED=YES
MISSING_STRUCTURE_FABRICATED=NO

CANDIDATE_MATERIALIZATION_ELIGIBILITY_PRESERVED=YES
CANDIDATE_BEFORE_BUDGET_INVARIANT_PRESERVED=YES

S4_IDENTIFIER_REMEDIATION_PRESERVED=YES
```

The active vNext scanner now preserves the run-level `partial` value that existed immediately
before optional post-candidate Structure Deep Dive. The inherited v11 structure implementation
still detects a missing complete daily-chain archive and skips structure generation, but that
Deep-Dive-only condition no longer changes an otherwise successful vNext run to `PARTIAL` and no
longer blocks the accepted Stage 5 `COMPLETE`-only ProductCandidate materialization path.

Legacy v11/v12 semantics were not changed. A legitimate partial condition that already exists
before vNext Structure Deep Dive remains `PARTIAL`.

## Package and governing evidence

The attached execution package was absent from canonical evidence and was copied byte-for-byte to:

```text
F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE8_POST_CANDIDATE_DEEP_DIVE_PARTIAL_REMEDIATION_EXECUTION_PACKAGE_20260820.md
```

```text
PACKAGE_SHA256=27837492E472A2376398A2509A33AECBF8E982128ACD10A7A34A3569936F3E44
PACKAGE_BACKUP_BYTE_IDENTICAL=YES
PACKAGE_CONFLICT_FOUND=NO
```

The execution package and every required governing/report file named by it were present in the
canonical evidence root and read completely before implementation:

- `NIGHTWATCH_SCANNER_VNEXT_INTEGRATED_SPEC_PROMPT_20260817(1).md`
- `NIGHTWATCH_VNEXT_STAGE4B_PHASE2A_VNEXT_CODEX_EXECUTION_PACKAGE_20260818.md`
- `NIGHTWATCH_VNEXT_STAGE5_PRODUCT_CANDIDATE_PERSISTENCE_COMPLETION_REPORT_20260818.md`
- `NIGHTWATCH_VNEXT_STAGE8_S4_STAGE_IDENTIFIER_REMEDIATION_REPORT_20260820.md`
- `NIGHTWATCH_VNEXT_SECOND_CONTROLLED_LIVE_MAG7_OBSERVATION_REPORT_20260820.md`
- `NIGHTWATCH_VNEXT_STAGE8_PARTIAL_TERMINAL_STATE_DIAGNOSTIC_REPORT_20260820.md`

## Repository preflight and authorized scope

```text
WORKTREE=F:\options-anomaly-scanner-stage8
BRANCH=vnext/stage8-mag7-observation
HEAD=3a63eaa1b9069d34199704fe31ac6466e8929d7d
ACCEPTED_S4_REMEDIATION_PRESENT=YES
UNEXPECTED_TRACKED_DIFF_FOUND=NO
```

The accepted S4 remediation was intentionally present and uncommitted at the start. It was neither
discarded nor modified outside its accepted identifier. The only tracked paths changed before and
after this remediation are the two authorized paths:

```text
AUTHORIZED_REMEDIATION_FILES:
- backend/app/scanner/v13.py: vNext-only post-candidate run-level partial isolation
- backend/tests/test_stage4b_phase2a_vnext.py: deterministic regression coverage
```

No application, test, migration, workflow, scheduler, configuration, or historical-data path
outside that authorization was changed.

## Narrow production fix

The change is confined to `app.scanner.v13.Mag7Scanner._structure_scan()`:

1. Capture `self.partial` immediately before calling the inherited structure implementation.
2. Execute the inherited implementation unchanged. It continues to query for a matching complete
   archive, skip an expiry when the archive or authoritative vendor OI date is absent, and generate
   no fabricated ContractScanObservation or StrikeCluster rows.
3. Restore the pre-Deep-Dive partial value before continuing the vNext persistence-freshness
   annotations.

This is correct for the active vNext boundary because Structure, Neighbor Strike, and Cluster are
optional post-candidate Deep-Dive context. The active v13 `_radar()` override reads already
persisted Radar evidence and does not introduce another partial condition inside this inherited
structure call. Core activity-source partials are established before Structure and therefore are
preserved by the saved value. Exceptions still follow the unchanged `FAILED` path.

```text
LEGACY_V11_CHANGED=NO
LEGACY_V12_CHANGED=NO
COMPLETE_ONLY_MATERIALIZATION_GATE_CHANGED=NO
TERMINAL_STATUS_FUNCTION_CHANGED=NO
THRESHOLDS_OR_SCORING_CHANGED=NO
DEEP_DIVE_BUDGET_CHANGED=NO
```

## Missing-state integrity

The focused production-path fixture supplied an AMZN selected expiry with vendor OI date
`2026-08-11` and no matching complete daily-chain archive. The inherited query returned no archive,
and the flow produced:

```text
CONTRACT_SCAN_OBSERVATIONS_CREATED=0
STRIKE_CLUSTERS_CREATED=0
MISSING_ARCHIVE_REPLACED_OR_SYNTHESIZED=NO
DEEP_DIVE_MISSING_STATE_PRESERVED=YES
MISSING_STRUCTURE_FABRICATED=NO
```

Thus the source remains absent/unavailable under the existing structure evidence semantics. Only
its inappropriate promotion to a run-level candidate-success blocker is removed.

## Regression evidence

### Case A — confirmed defect and normal materialization path

The regression directly executed the inherited production structure path through v13 with the
missing AMZN archive. With no pre-existing blocker, the remediated scanner retained
`partial=False`, and the unchanged production `completion_status()` returned `COMPLETE`.

A deterministic diagnostic-shaped projection with the observed distribution then ran through the
normal `materialize_successful_scan_candidates()` implementation:

```text
PROJECTED_PRODUCT_CANDIDATES=7
PROJECTED_QUALIFYING_TRIGGERS=82
MATERIALIZED_PRODUCT_CANDIDATES=7
MATERIALIZED_PRODUCT_CANDIDATE_TRIGGERS=82
CANDIDATE_MATERIALIZATION_ELIGIBILITY_PRESERVED=YES
```

Candidates were produced by the normal Stage 5 materializer in memory; the test did not manually
insert runtime candidates and made no database or vendor call.

### Case B — legitimate pre-existing PARTIAL

The same missing-archive path was executed with `self.partial=True` before Structure. After Deep
Dive, `self.partial` remained true and the unchanged terminal function returned `PARTIAL`.

```text
LEGITIMATE_PREEXISTING_PARTIAL_PRESERVED=YES
```

### Case C — candidate-before-budget invariant

The existing production-projection regression remains unchanged and passes. It proves seven
qualifying ProductCandidates exist while only four tickers receive Deep-Dive budget.

```text
QUALIFYING_PRODUCT_CANDIDATES=7
DEEP_DIVE_SELECTED_TICKERS=4
CANDIDATE_BEFORE_BUDGET_INVARIANT_PRESERVED=YES
```

### Case D — S4 identifier contract

The existing executable S4 regression remains intact and passes:

```text
S4_STAGE_IDENTIFIER=S4_VNEXT_DEEP_BUDGET_SELECTION
S4_STAGE_IDENTIFIER_LENGTH=30
SCAN_STAGES_STAGE_MAX_LENGTH=32
S4_IDENTIFIER_REMEDIATION_PRESERVED=YES
```

## Verification matrix

| Gate | Result |
|---|---|
| Focused remediation + carried-in invariant/S4 tests | PASS — 4 passed |
| Stage 4B focused tests | PASS — 18 passed |
| Stage 5 regressions | PASS — 14 passed |
| Stage 6 regressions | PASS — 27 passed |
| Stage 7 relevant backend regressions | PASS — 3 passed |
| Full backend suite | PASS — 382 passed |
| Ruff | PASS — all checks passed with `--no-cache` |
| Alembic heads | PASS — `20260818_0017 (head)` |
| `git diff --check` | PASS |

The host's standard pytest process reproducibly remained alive after every fixture teardown,
including for an untouched one-assertion existing test. To obtain authoritative command exit
codes, verification disabled unrelated auto-loaded plugins, explicitly enabled
`pytest_asyncio.plugin` where async tests required it, and used an in-memory pytest plugin that
exited with pytest's already-computed `sessionfinish` status before the hanging Windows teardown
hook. Test collection, fixtures, bodies, assertions, and reported exit status were unchanged. Every
matrix command returned pytest exit status 0.

No frontend file or frontend behavior changed, so frontend lint/build was not a relevant gate for
this backend-only remediation.

```text
MIGRATION_CREATED=NO
ALEMBIC_HEAD=20260818_0017
MIGRATION_FILES_CHANGED=0
WORKFLOW_FILES_CHANGED=0
SCHEDULER_FILES_CHANGED=0
```

## Historical and external-state integrity

Neither historical controlled run was queried or written during this code/test remediation. No
runtime database connection was opened. Because the task performed zero remote DB writes, both
persisted historical states remain untouched:

```text
FIRST_FAILED_RUN_ID=090359ad-9d76-49b9-8902-f28ac54a1d1b
FIRST_FAILED_RUN_MUTATED=NO

SECOND_SCAN_RUN_ID=e9267160-503a-41c7-9bb1-8cc2b2e3d8c6
SECOND_PARTIAL_RUN_MUTATED=NO
```

Exact external URLs/API endpoints contacted during this task:

```text
EXTERNAL_URLS_OR_API_ENDPOINTS_CONTACTED=[]
```

No Nightwatch, PostgreSQL, Dealer/GEX, GitHub, registry, or other network endpoint was contacted.

## Change and authorization ledger

The current tracked diff relative to base includes the accepted carried-in S4 remediation plus
this fix. This task added the vNext partial guard and its regressions without changing any other
tracked path.

```text
APPLICATION_CODE_CHANGES=1
TEST_CODE_CHANGES=1
MIGRATION_CREATED=NO
ALEMBIC_HEAD=20260818_0017

FIRST_FAILED_RUN_MUTATED=NO
SECOND_PARTIAL_RUN_MUTATED=NO

NIGHTWATCH_REQUESTS=0
PAID_UNITS=0
REMOTE_DB_WRITES=0

WORKFLOW_CHANGES=0
SCHEDULER_CHANGES=0
COMMITS_CREATED=0
PUSHES=0
PRS_CREATED=0
MERGES=0
```

## Final boundary

```text
THIRD_MAG7_SCAN_AUTHORIZED=NO
STAGE8_OBSERVATION_RESUME_READY=YES
STAGE9_READY=NO
NEXT_AUTHORIZED_STAGE=NONE
```

`STAGE8_OBSERVATION_RESUME_READY=YES` states only that this narrow code remediation and its
regressions passed. It does not authorize or start a third MAG7 scan, any paid request, broader
Stage 8 observation, deployment, or Stage 9 work.

STOP.
