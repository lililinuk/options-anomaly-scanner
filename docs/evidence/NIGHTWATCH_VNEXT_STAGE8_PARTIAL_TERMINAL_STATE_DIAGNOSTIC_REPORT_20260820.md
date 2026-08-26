# Nightwatch vNext — Stage 8 PARTIAL Terminal-State Diagnostic Report

Date: 2026-08-20
Worktree: F:/options-anomaly-scanner-stage8
Branch: vnext/stage8-mag7-observation
Diagnostic package SHA-256: 52470D8355C3A627CD9E930615BB43801EFF97BD0A742585823C6C09E82D29EF
Second ScanRun: e9267160-503a-41c7-9bb1-8cc2b2e3d8c6

## Executive result

PARTIAL_DIAGNOSTIC_RESULT=ROOT_CAUSE_CONFIRMED

TERMINAL_STATUS_FUNCTION=app.scanner.service.completion_status
PARTIAL_STATUS_CONDITION=partial=True; budget_limited=False; data_pending=False

PARTIAL_CLASSIFICATION=BUG_PARTIAL_FROM_OPTIONAL_OR_POST_CANDIDATE_LAYER
PARTIAL_SEMANTICALLY_JUSTIFIED=NO

PARTIAL_CAUSING_TICKERS=AMZN
PARTIAL_CAUSING_SOURCE_FAMILIES=COMPLETE_DAILY_CHAIN_ARCHIVE_FOR_STRUCTURE_DEEP_DIVE; affected active trigger family=EXPIRY_ACTIVITY

CANDIDATE_MATERIALIZATION_CALLED=NO
CANDIDATE_MATERIALIZATION_SKIP_REASON=app.scanner.v11.Mag7Scanner._finish_v11 invokes materialization only when status == COMPLETE; status was PARTIAL
PARTIAL_STATUS_BLOCKS_MATERIALIZATION=YES
IF_RUN_IS_PARTIAL_BUT_PHASE2A_HAS_VALID_QUALIFYING_CANDIDATES_SHOULD_MATERIALIZE=YES

ZERO_PAID_TERMINAL_STATUS_REPRODUCTION_ATTEMPTED=YES
ZERO_PAID_TERMINAL_STATUS_REPRODUCTION_RESULT=REPRODUCED
REPRODUCED_STATUS=PARTIAL

REMEDIATION_REQUIRED=YES
EXPECTED_FILES_TO_CHANGE=backend/app/scanner/v13.py; backend/tests/test_stage4b_phase2a_vnext.py
MIGRATION_REQUIRED=NO
HISTORICAL_DATA_REPAIR_REQUIRED=NO

STAGE8_OBSERVATION_PACKAGE_STATUS_MODEL_DEFECT=NO
SECOND_RUN_MUTATED=NO
PARTIAL_RUN_STATE_TRUTHFUL=YES

The immediate production cause is exact and deterministic: two selected AMZN expiry observations had no matching COMPLETE daily-chain archive for their ticker, expiration, and vendor OI date. The inherited structure/deep-dive method set the scanner-wide partial flag for each gap. With no budget limit and no data-pending condition, completion_status returned PARTIAL. The COMPLETE-only finish gate then skipped ProductCandidate materialization even though the accepted candidate projection contained all seven MAG7 tickers and 82 qualifying active-family triggers.

The missing deep-dive archive data is a truthful feature-level degradation. What is not semantically justified is promoting this optional, post-candidate context gap into a run-level PARTIAL state that suppresses otherwise valid ProductCandidate occurrences. The accepted candidate-first architecture places candidate existence before Deep-Dive budget and structure context.

## Package and governing evidence

The attached package was saved byte-for-byte to:

F:/options-anomaly-scanner/docs/evidence/NIGHTWATCH_VNEXT_STAGE8_PARTIAL_TERMINAL_STATE_DIAGNOSTIC_EXECUTION_PACKAGE_20260820.md

PACKAGE_SHA256=52470D8355C3A627CD9E930615BB43801EFF97BD0A742585823C6C09E82D29EF
PACKAGE_BACKUP_BYTE_IDENTICAL=YES

All seven canonical governing/report files named by the package were present and read completely. The primary and canonical diagnostic report targets were absent before report creation, so no report conflict existed.

## Production terminal-status call chain

TERMINAL_STATUS_CALL_CHAIN:

1. app.cli.run_mag7_scan creates app.scanner.v13.Mag7Scanner.
2. v13.Mag7Scanner inherits app.scanner.v11.Mag7Scanner.execute.
3. execute runs v13._activity_surface.
4. execute runs v13._select_dual.
5. execute runs v13._structure_scan, which delegates structure loading to v11._structure_scan.
6. v11._structure_scan sets self.partial=True when a selected expiry lacks a matching COMPLETE archive or lacks vendor_oi_date.
7. v13._structure_scan completes its persistence annotations.
8. v12._summarize_v11 persists S6_POSITIONING_SUMMARY_V12.
9. v11.execute calls app.scanner.service.completion_status.
10. v11._finish_v11 persists the terminal status and calls candidate materialization only for COMPLETE.

The pure terminal function is:

- budget_limited=True returns PARTIAL_BUDGET_LIMIT.
- else data_pending=True returns DATA_PENDING.
- else partial=True returns PARTIAL.
- else returns COMPLETE.

FAILED does not come from completion_status. An exception in v11.execute enters its exception handler, which rolls back the current transaction, persists status FAILED, records safe_error as the exception class, and re-raises.

COMPLETE_STATUS_CONDITION=partial=False; budget_limited=False; data_pending=False
FAILED_STATUS_CONDITION=an exception reaches the v11.execute exception handler
PARTIAL_STATUS_CONDITION=partial=True; budget_limited=False; data_pending=False

## Exact terminal-status inputs for this run

The scanner-wide booleans are not separately persisted. They were deterministically reconstructed from the code and the run-linked rows.

| Terminal-status input | Persisted/reconstructed value | Expected condition | Caused PARTIAL? |
|---|---|---|---|
| partial | True | Any active path setting self.partial=True | YES |
| budget_limited | False | 14 consumed units below 75; 14 attempts below 100; no budget break | NO |
| data_pending and not expiry_rows | False | 104 expiry rows existed; all 14 activity calls were HTTP 200 | NO |
| ticker activity availability | Seven COMPLETE ticker rows, two request IDs each | No UNAVAILABLE or UNPARSEABLE ticker | NO |
| API errors/retries | 0 errors; 0 retries; 14 HTTP 200 | No activity NightwatchError | NO |
| required persisted stages | Seven COMPLETE stages through S6 | All stage writes completed | NO |
| selected expiry vendor OI dates | Present for all ten selected expiries | No missing vendor_oi_date branch | NO |
| selected expiry complete archive matches | 8/10 | Missing match sets self.partial=True | YES |
| positioning summaries | 0 rows; S6 stage COMPLETE | Not read by completion_status and does not set partial | NO |
| candidate projection | 7 candidates, 82 qualifying triggers | Not read by completion_status | NO |
| run safe_error | None | No exception/FAILED path | NO |
| quota/network counters | 14 paid units, 14 attempts, 0 cache hits, 14 fresh requests | Within configured bounds | NO |

All 14 run-linked api_usage_audit rows had HTTP 200, consumed_quota=True, attempt_count=1, retry_count=0, and error_code=NULL.

## Exact partial-causing persisted inputs

The selected expiry archive check in v11._structure_scan requires a row matching:

- ticker
- expiration
- vendor_oi_date
- chain_status=COMPLETE

Eight selected expiries satisfied this check and produced 1,694 ContractScanObservation rows. Two did not:

| Ticker | Expiration | Vendor OI date | Trigger source | COMPLETE archive match | Contract rows | Set partial |
|---|---|---|---|---:|---:|---:|
| AMZN | 2026-08-21 | 2026-08-11 | EXPIRY_ACTIVITY | NO | 0 | YES |
| AMZN | 2026-08-28 | 2026-08-11 | EXPIRY_ACTIVITY | NO | 0 | YES |

AMZN 2026-10-16, selected by RADAR_EVENT, did have a complete matching archive and produced 120 contract rows.

PARTIAL_CAUSING_TICKERS=AMZN
PARTIAL_CAUSING_SOURCE_FAMILIES=COMPLETE_DAILY_CHAIN_ARCHIVE_FOR_STRUCTURE_DEEP_DIVE; affected active trigger family=EXPIRY_ACTIVITY

This was not an activity endpoint failure, Radar failure, Persistence failure, quota failure, exception, or S4 telemetry failure.

## Seven-ticker inspection

The model has no separate ticker safe-error column. Safe-error status was checked through run summary and run-linked usage audit; no ticker had a persisted usage error.

| Ticker | Ticker data status | Activity | Radar triggers | Persistence triggers | Structure/deep-dive | Positioning rows | Qualifying projection |
|---|---|---|---:|---:|---|---:|---|
| AAPL | COMPLETE | COMPLETE, 2/2 HTTP 200 | 11 | 0 | COMPLETE, 2/2 selected expiries archived; 332 contracts | 0 | YES, 13 triggers |
| AMZN | COMPLETE | COMPLETE, 2/2 HTTP 200 | 8 | 0 | PARTIAL, 1/3 selected expiries archived; 120 contracts | 0 | YES, 10 triggers |
| GOOGL | COMPLETE | COMPLETE, 2/2 HTTP 200 | 7 | 0 | NOT_SELECTED, 0 selected expiries | 0 | YES, 9 triggers |
| META | COMPLETE | COMPLETE, 2/2 HTTP 200 | 2 | 0 | COMPLETE, 2/2 selected expiries archived; 740 contracts | 0 | YES, 4 triggers |
| MSFT | COMPLETE | COMPLETE, 2/2 HTTP 200 | 3 | 0 | NOT_SELECTED, 0 selected expiries | 0 | YES, 5 triggers |
| NVDA | COMPLETE | COMPLETE, 2/2 HTTP 200 | 25 | 0 | COMPLETE, 3/3 selected expiries archived; 502 contracts | 0 | YES, 27 triggers |
| TSLA | COMPLETE | COMPLETE, 2/2 HTTP 200 | 12 | 0 | NOT_SELECTED, 0 selected expiries | 0 | YES, 14 triggers |

No current Contract Persistence trigger qualified under CALIBRATION_REQUIRED. That absence did not set partial. The zero positioning-summary count also did not feed terminal status; S6 itself persisted COMPLETE.

## Candidate projection and materialization gate

The accepted Stage 4 projection was executed read-only at the second run's completed_at cutoff using its persisted expiry, contract, Radar, raw-source, and provenance rows.

PROJECTED_PRODUCT_CANDIDATES=7
PROJECTED_ACTIVE_ANOMALIES=82
PROJECTED_QUALIFYING_TRIGGERS=82
PROJECTED_SUPPORTING_TRIGGERS=0
PROJECTED_RADAR_ROWS=68
PROJECTED_EXPIRY_ACTIVITY_ROWS=14
PROJECTED_PERSISTENCE_ROWS=0

| Candidate | Trigger count | Qualifying | Families |
|---|---:|---:|---|
| AAPL | 13 | 13 | RADAR_EVENT, EXPIRY_ACTIVITY |
| AMZN | 10 | 10 | RADAR_EVENT, EXPIRY_ACTIVITY |
| GOOGL | 9 | 9 | RADAR_EVENT, EXPIRY_ACTIVITY |
| META | 4 | 4 | RADAR_EVENT, EXPIRY_ACTIVITY |
| MSFT | 5 | 5 | RADAR_EVENT, EXPIRY_ACTIVITY |
| NVDA | 27 | 27 | RADAR_EVENT, EXPIRY_ACTIVITY |
| TSLA | 14 | 14 | RADAR_EVENT, EXPIRY_ACTIVITY |

CANDIDATE_MATERIALIZATION_CALLED=NO
CANDIDATE_MATERIALIZATION_SKIP_REASON=_finish_v11 branch condition status == COMPLETE was false because status == PARTIAL
PARTIAL_STATUS_BLOCKS_MATERIALIZATION=YES

The candidate materializer independently returns no rows for any status other than COMPLETE, and existing Stage 5 tests explicitly preserve that contract. The materialization gate therefore behaved exactly as implemented. The upstream semantic defect is that optional/post-candidate Deep-Dive archive availability was allowed to determine the run-level success status consumed by that gate.

Accepted governing semantics establish:

- ProductCandidate existence precedes Deep-Dive budget and structure context.
- All qualifying active anomalies are grouped and persisted.
- A valid candidate cannot be discarded because its Deep-Dive context is unavailable or not selected.
- Missing context must remain a truthful availability state, not a negative candidate signal.

IF_RUN_IS_PARTIAL_BUT_PHASE2A_HAS_VALID_QUALIFYING_CANDIDATES_SHOULD_MATERIALIZE=YES

For the narrowest remediation, the active vNext path should prevent a post-candidate structure/archive gap from setting the run-level candidate-success blocker while preserving truthful feature-level unavailability. The existing COMPLETE-only materialization contract can then remain unchanged.

## PARTIAL classification

PARTIAL_CLASSIFICATION=BUG_PARTIAL_FROM_OPTIONAL_OR_POST_CANDIDATE_LAYER
PARTIAL_SEMANTICALLY_JUSTIFIED=NO

The two missing archives are real and should remain visible as Deep-Dive context unavailable. A feature-level degradation indicator is semantically legitimate. The scanner-wide PARTIAL terminal consequence is not legitimate here because it converts an optional/post-candidate context gap into loss of seven valid candidate occurrences.

This is primarily scanner terminal-status logic inherited from the pre-candidate architecture. It is not an S4 repair regression, vendor-call failure, accounting/finalization error, or only a Stage 8 reporting-model issue.

STAGE8_OBSERVATION_PACKAGE_STATUS_MODEL_DEFECT=NO

The second-observation package correctly refused to relabel a persisted PARTIAL run as SUCCESS_NO_CANDIDATE. The incorrect state originated in production before the package interpreted it.

## Zero-paid deterministic reproduction

The read-only reconstruction proved:

- activity-source partial branch: not taken;
- unparseable activity branch: not taken;
- budget-limited branch: not taken;
- data-pending branch: not taken;
- missing selected archive branch: taken twice for AMZN;
- missing vendor OI date branch: not taken.

The pure local function produced:

completion_status(partial=False, budget_limited=False, data_pending=False)=COMPLETE
completion_status(partial=True, budget_limited=False, data_pending=False)=PARTIAL

ZERO_PAID_TERMINAL_STATUS_REPRODUCTION_ATTEMPTED=YES
ZERO_PAID_TERMINAL_STATUS_REPRODUCTION_RESULT=REPRODUCED
REPRODUCED_STATUS=PARTIAL

No vendor client was constructed and no database write was performed.

## Remediation design boundary

REMEDIATION_REQUIRED=YES
EXPECTED_FILES_TO_CHANGE=backend/app/scanner/v13.py; backend/tests/test_stage4b_phase2a_vnext.py
MIGRATION_REQUIRED=NO
HISTORICAL_DATA_REPAIR_REQUIRED=NO

Narrow design scope:

1. In the active vNext scanner path, keep selected-expiry daily-chain absence as a truthful Structure/Deep-Dive availability fact.
2. Do not let that post-candidate availability gap set the run-level partial boolean that blocks ProductCandidate materialization.
3. Add a regression proving a run with valid active-family candidates and unavailable selected Deep-Dive archive still reaches candidate materialization, while the missing Deep-Dive context remains unavailable.
4. Preserve true activity-source failures, unparseable core discovery, budget limits, data-pending states, exceptions, thresholds, scoring, candidate rules, retry behavior, universe, and the COMPLETE-only materialization guard.

The narrow active-vNext remediation avoids changing legacy v11/v12 semantics globally and avoids broadening materialization to every existing PARTIAL cause.

No fix was implemented.

## Runtime truth preservation

Final explicit read-only verification:

SECOND_SCAN_RUN_ID=e9267160-503a-41c7-9bb1-8cc2b2e3d8c6
SECOND_SCAN_STATUS=PARTIAL
SECOND_SCAN_SAFE_ERROR=NONE
COMPLETED_STAGE_ROWS=7
CANDIDATE_MATERIALIZED_AT=NULL
CANDIDATE_MATERIALIZATION_RULE_VERSION=NULL
CANDIDATE_MATERIALIZATION_RULE_HASH=NULL
PRODUCT_CANDIDATE_ROWS=0
PRODUCT_CANDIDATE_TRIGGER_ROWS=0
PRODUCT_CANDIDATE_CONTEXT_ROWS=0
ANOMALY_CONTEXT_DETAIL_ROWS=0

SECOND_RUN_MUTATED=NO
PARTIAL_RUN_STATE_TRUTHFUL=YES

The historical run truthfully records what the current code did. No row was repaired, relabeled, backfilled, or deleted.

## Repository and external-contact ledger

The only tracked worktree differences remained the previously accepted, uncommitted S4 remediation files:

- backend/app/scanner/v13.py
- backend/tests/test_stage4b_phase2a_vnext.py

This diagnostic made no application, test, migration, workflow, scheduler, or configuration edit.

The only external endpoint contacted in this task was:

- postgresql://aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres — explicit read-only SELECT/reconstruction transactions; credentials omitted.

No HTTP(S), Nightwatch, Dealer/GEX, GitHub, workflow, registry, or other external endpoint was contacted.

NIGHTWATCH_REQUESTS=0
PAID_UNITS=0
REMOTE_DB_WRITES=0
APPLICATION_CODE_CHANGES=0
TEST_CODE_CHANGES=0
MIGRATION_CHANGES=0
WORKFLOWS_DISPATCHED=0
COMMITS_CREATED=0
PUSHES=0
PRS_CREATED=0
MERGES=0

## Final boundary

THIRD_MAG7_SCAN_AUTHORIZED=NO
STAGE8_OBSERVATION_RESUME_READY=NO
STAGE9_READY=NO
NEXT_AUTHORIZED_STAGE=NONE

STOP. No remediation, third scan, broader Stage 8 observation, or Stage 9 work was started.

