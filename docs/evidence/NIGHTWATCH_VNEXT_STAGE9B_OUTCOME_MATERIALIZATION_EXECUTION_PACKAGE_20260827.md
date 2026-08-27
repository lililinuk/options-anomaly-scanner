# NIGHTWATCH vNext — Stage 9B Outcome Materialization & Maturity
## Codex Execution Package

**Date:** 2026-08-27  
**Authorization:** Stage 9B authorized after Stage 9A accepted integration.

## 1. Close Stage 9A integration first
Stage 9A has been reviewed and accepted as `PASS_WITH_CARRIED_ITEMS`.

Before Stage 9B:
1. In `F:\options-anomaly-scanner-stage9a`, verify the Stage 9A implementation tree/evidence.
2. Verify worktree/canonical Stage 9A completion-report copies are byte-identical and record SHA-256.
3. Commit Stage 9A implementation/evidence on `vnext/stage9a-forward-outcome-foundation` if not already committed.
4. Integrate the accepted Stage 9A commit into canonical `F:\options-anomaly-scanner`.
5. Push accepted canonical `main` to `origin/main`.
6. Verify clean `main` and `HEAD == origin/main`.
7. Record that exact commit as `STAGE9B_BASELINE_COMMIT`.

If unrelated newer canonical changes create an integration conflict, never force-push or overwrite; return `HOLD_CONFLICT`.

## 2. Required evidence
Ensure these exist under `F:\options-anomaly-scanner\docs\evidence`:
- `NIGHTWATCH_VNEXT_STAGE9_DESIGN_GATE_FINAL_20260827.md`
- `NIGHTWATCH_VNEXT_STAGE9_HISTORICAL_TRIGGER_RETENTION_DESIGN_DECISION_20260826.md`
- `NIGHTWATCH_VNEXT_STAGE9A_FORWARD_OUTCOME_FOUNDATION_COMPLETION_REPORT_20260827.md`
- `NIGHTWATCH_VNEXT_STAGE9A_ACCEPTANCE_AND_STAGE9B_AUTHORIZATION_20260827.md`
- `NIGHTWATCH_VNEXT_STAGE9B_OUTCOME_MATERIALIZATION_EXECUTION_PACKAGE_20260827.md`

Use byte-identical copy/hash rules; never overwrite conflicting same-name evidence.

## 3. Stage 9B worktree
From the clean Stage 9B baseline:
- worktree: `F:\options-anomaly-scanner-stage9b`
- branch: `vnext/stage9b-outcome-materialization`

## 4. Founder-locked price policy
`STAGE9B_PRICE_BASIS_POLICY = RAW_REGULAR_CLOSE_RESEARCH_V1`

This supersedes the prior global hold for lack of an adjusted-price basis.

Use the existing preserved regular-session Close parsing/provenance path.

Every measurement must say raw/unadjusted. Never label it adjusted, total-return, or corporate-action-consistent.

## 5. Corporate-action handling
Do not make a complete corporate-action feed a prerequisite for Stage 9B v1.

Rules:
- known price-scale-changing action between Reference and a target horizon contaminates that affected horizon for primary descriptive aggregation;
- preserve audit evidence, but do not present contaminated raw return as economically continuous;
- if an action occurs after T+1 but before T+3, T+1 can remain usable while T+3/T+5 are contaminated;
- ordinary cash dividends remain part of raw price-return semantics;
- later adjusted/corrected results must be append-only/versioned and must not overwrite raw-v1 measurements;
- if no known event is recorded, raw-v1 may be calculated as an accepted limitation.

## 6. Materialization scope
Materialize Stage 9 Research samples/outcomes from Stage 9A foundation.

Population:
- preserve all ProductCandidate occurrences;
- canonical `scheduled_daily` = primary eligible;
- manual/dashboard/diagnostic/remediation/developer rerun = preserved but primary-ineligible.

For each sample:
- bind immutable ProductCandidate identity;
- bind frozen FIRST_KNOWLEDGE_BASELINE;
- bind first-knowledge qualifying historical triggers;
- derive ticker, route composition, raw qualifying trigger count, existing DTE semantics;
- map Reference/T+1/T+3/T+5 XNYS sessions.

Maturity by horizon:
- `NOT_YET_MATURE`
- `MATURE_AVAILABLE`
- `MATURE_MISSING_DATA`
- `INVALID_SAMPLE`
- explicit corporate-action contamination reason/state if separate

A horizon matures independently of later horizons.

## 7. Price sourcing
Priority:
1. preserved historical regular-session OHLC;
2. no refetch when required sessions already exist;
3. identify minimal distinct ticker/date gaps for mature/due missing data;
4. share any later-permitted fetch once across all due samples for a ticker;
5. no second scheduler.

For this initial Stage 9B implementation/materialization run:
`PAID_NIGHTWATCH_CALLS = 0`

Materialize all possible outcomes from preserved data first and report residual missing OHLC before any later paid-call authorization.

## 8. Outcome formulas
For Reference `R` and future closes `C1...CN`:
- `T+N Close Return = CN / R - 1`
- `Max Upside through T+N = max(C1...CN) / R - 1`
- `Max Downside through T+N = min(C1...CN) / R - 1`

Close-path only. No Daily High/Low. No MFE/MAE. Direction remains `UNRESOLVED`.

## 9. Trigger-count distribution
Inspect only canonical scheduled-production historical ProductCandidates.

Report at minimum:
- N
- min
- P25
- median
- P75
- P90 if useful
- max
- by ticker
- by route composition when sample size permits

Do not hardcode Stage 9C trigger-count buckets. Recommend natural versioned boundaries in the completion report for Founder review.

## 10. DTE
Reuse canonical Scanner semantics:
- VERY_SHORT
- SHORT
- MEDIUM

Preserve LONG where existing data contains it; never use DTE as an admission filter. Do not invent Stage 9 thresholds.

## 11. Materialization integrity
Must be deterministic and idempotent/safely versioned.

Do not:
- mutate Frozen First-Knowledge baseline;
- mutate frozen trigger set;
- rewrite ProductCandidate identity;
- backfill future knowledge into first-knowledge context;
- silently duplicate the same methodology revision;
- silently overwrite raw-v1 when later correction exists.

## 12. Required report counts
Report:
- total Research Samples
- canonical primary-eligible samples
- non-primary samples by origin
- valid frozen baselines
- invalid samples/reasons
- T+1/T+3/T+5 maturity counts
- MATURE_AVAILABLE / NOT_YET_MATURE / MATURE_MISSING_DATA
- known/suspect corporate-action contamination count if available
- outcomes materialized from preserved OHLC
- residual missing OHLC by ticker/date
- paid calls
- trigger-count distribution
- per-ticker composition
- route composition counts

## 13. Tests
Add focused tests for:
- raw/unadjusted basis labeling
- no adjusted/total-return misrepresentation
- maturity by horizon
- materialization idempotence/versioning
- preserved-OHLC reuse
- missing != zero
- partial horizon maturity
- historical-trigger retention
- canonical/noncanonical origin population
- trigger-count distribution
- no trigger-bucket hardcoding
- Live/Research firewall regression
- known corporate-action contamination
- later corrected revision does not overwrite raw-v1
- no second scheduler
- normal preserved-data materialization triggers no paid call path

Run full relevant backend suite, Ruff, Alembic checks, and applicable shared-contract/frontend regressions.

## 14. Out of scope
Do not:
- build Stage 9C Research UI
- create Actionability labels
- feed Forward Outcome to live paths
- change Phase 2A thresholds/routes
- change Phase 2B semantics
- infer bullish/bearish direction
- add a second scheduler
- claim raw Close return is total return

## 15. Completion report
Create:
`NIGHTWATCH_VNEXT_STAGE9B_OUTCOME_MATERIALIZATION_COMPLETION_REPORT_20260827.md`

Include:
- exact Stage 9B baseline/integration commit
- branch/worktree
- migrations/files changed
- materialization and maturity counts
- price-basis provenance
- corporate-action handling
- trigger-count distribution and proposed natural buckets
- residual OHLC gaps
- paid calls
- tests
- Live/Research firewall proof
- Stage 9C technical readiness
- PASS / PASS_WITH_CARRIED_ITEMS / HOLD

Save byte-identical copies to:
1. `F:\options-anomaly-scanner-stage9b\docs\evidence\NIGHTWATCH_VNEXT_STAGE9B_OUTCOME_MATERIALIZATION_COMPLETION_REPORT_20260827.md`
2. `F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE9B_OUTCOME_MATERIALIZATION_COMPLETION_REPORT_20260827.md`

Verify and report SHA-256 of both copies.

Do not authorize Stage 9C yourself.
