# NIGHTWATCH vNext — Stage 9A Forward Outcome Foundation
## Codex Execution Package

**Date:** 2026-08-27  
**Authorization:** STAGE 9A IMPLEMENTATION AUTHORIZED  
**Boundary:** Do not implement Stage 9B or Stage 9C.

## 1. Authoritative starting point
Canonical repo: `F:\options-anomaly-scanner`  
Required branch before work: `main`  
Expected authorization commit: `c364183fff98d74e1d79f78a38a4fb07f94493f9`

Preflight:
```powershell
cd F:\options-anomaly-scanner
git fetch origin
git status --short
git branch --show-current
git rev-parse HEAD
git rev-parse origin/main
```

Requirements:
- branch `main`
- clean working tree
- `HEAD == origin/main`
- if `origin/main` advanced beyond the authorization commit, stop and report the new state before implementation; do not silently assume the old tree

## 2. Temporary worktree
Create a temporary Stage 9A worktree from verified latest `origin/main`.

Suggested:
- path: `F:\options-anomaly-scanner-stage9a`
- branch: `vnext/stage9a-forward-outcome-foundation`

The canonical repo remains `F:\options-anomaly-scanner`.

Do not remove the temporary worktree in this package; removal happens only after later acceptance/integration.

## 3. Canonical evidence
Read and honor:
- `F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_CANONICAL_EVIDENCE_MANIFEST.md`
- `F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_SCANNER_VNEXT_INTEGRATED_SPEC_PROMPT_20260817(1).md`
- `F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE9_DESIGN_GATE_FINAL_20260827.md`
- `F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE9_HISTORICAL_TRIGGER_RETENTION_DESIGN_DECISION_20260826.md`

If this execution package is supplied as an attachment and absent from canonical evidence, copy it byte-for-byte to:
`F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE9A_FORWARD_OUTCOME_FOUNDATION_EXECUTION_PACKAGE_20260827.md`

Verify SHA-256. If same-name canonical content differs, never overwrite; return HOLD / evidence conflict.

## 4. Stage 9A non-negotiables
- one Research Sample = one ProductCandidate occurrence
- ProductCandidate.id + candidate_first_knowledge_at + frozen FIRST_KNOWLEDGE_BASELINE are core identity
- no arbitrary cross-run merge
- canonical scheduled production ProductCandidates only are primary-aggregation eligible
- manual/controlled/diagnostic/remediation/developer rerun occurrences remain preserved but excluded from primary aggregation
- no second admission filter based on B1/B2/B3/B4, Trend, IV, GEX, DTE, trigger count, premium, Deep Dive, or future outcome
- Frozen First-Knowledge Baseline remains immutable
- historical qualifying triggers remain Research evidence after contract/expiry expiration
- `REFERENCE_PRICE_POLICY = PRIOR_COMPLETED_REGULAR_CLOSE`
- XNYS sessions, holidays, DST and early closes must be respected
- Direction remains `UNRESOLVED`
- Forward Outcome v1 uses T+1/T+3/T+5 Close Return plus Close-path Max Upside/Max Downside
- no Daily High/Low in v1 outcome formulas
- Reference and T+N prices must share one provably corporate-action-consistent basis
- reuse existing Scanner VERY SHORT / SHORT / MEDIUM DTE semantics
- preserve raw trigger count; do not hardcode trigger-count buckets
- `SECOND_FORWARD_OUTCOME_SCHEDULER = NO`
- zero paid Nightwatch calls
- no historical outcome materialization/backfill in Stage 9A
- no Research UI in Stage 9A
- live scanner/live ranking/current candidate paths must not consume Forward Outcome

## 5. Repository inspection before implementation
Document exact findings for:
1. ProductCandidate / ProductCandidateTrigger schema and occurrence identity
2. `candidate_first_knowledge_at`
3. frozen FIRST_KNOWLEDGE_BASELINE storage
4. scan-run trigger/origin metadata
5. historical OHLC schema and price semantics
6. canonical VERY SHORT / SHORT / MEDIUM DTE implementation/source
7. calendar/date helpers and dependencies
8. migration head
9. live scanner/API dependency graph relevant to the Research firewall

Do not invent semantics where repository-defined semantics exist.

## 6. Required Stage 9A implementation

### A. Minimal additive Research foundation schema
Fit names to the existing codebase, but represent at least:
- ProductCandidate occurrence FK / immutable research-sample identity
- auditable run-origin classification
- primary-research eligibility state
- candidate first-knowledge anchor
- reference-session identity
- T+1/T+3/T+5 target-session identities
- reference price basis/provenance
- maturity state or normalized maturity representation
- outcome methodology/version
- append-only/versioned compatibility for Stage 9B
- explicit missing/invalid states without zero-fill

Do not historical-backfill Forward Outcome values.

### B. Canonical production-origin classification
Primary Research uses only ProductCandidates from the canonical scheduled production vNext scan.

Production intent:
- morning Daily OI/Radar archive: not a canonical ProductCandidate run
- Dealer GEX archive: not a canonical ProductCandidate run
- evening Activity + readiness + exactly one scheduled vNext scan: canonical ProductCandidate run

If current metadata cannot reliably distinguish this, add the minimum explicit/auditable origin representation. Do not infer from clock time alone.

### C. XNYS session/reference mapping
Implement deterministic exchange-aware logic covering:
- premarket
- intraday
- post-close
- weekend/non-trading day
- XNYS holidays
- early closes
- DST
- exact-close boundary

Policy:
`PRIOR_COMPLETED_REGULAR_CLOSE`

Exact-close rule:
same-day close may be the reference only when the official session close has completed and the close is known as-of candidate first knowledge; otherwise use prior completed close.

Canonical test:
- candidate first known Aug 20 2026 06:07 ET
- reference Aug 19
- T+1 Aug 20
- T+3 Aug 24
- T+5 Aug 26

### D. Direction-neutral outcome functions
Pure/testable formulas:

`T+N Close Return = CN / R - 1`

`Max Upside through T+N = max(C1...CN) / R - 1`

`Max Downside through T+N = min(C1...CN) / R - 1`

Required N: 1, 3, 5.

Use Close-path values only. No Daily High/Low. No MFE/MAE labels. No bullish/bearish direction.

### E. Maturity state machine
At minimum:
- `NOT_YET_MATURE`
- `MATURE_AVAILABLE`
- `MATURE_MISSING_DATA`
- `INVALID_SAMPLE`

A target date on the calendar is not enough; its regular-session Close must have completed.

Missing is never zero.

### F. Corporate-action-consistent price-basis gate
Inspect actual OHLC semantics.

Reference and all future prices must use one consistent, provable corporate-action basis.

If adjusted/consistent semantics are provable, persist the basis/provenance.

If not provable, fail closed. Never mix raw/adjusted or fabricate returns. Report the capability gap and whether it blocks Stage 9B.

### G. Historical trigger retention
Stage 9 foundation must not require a contract to remain active.

Expired qualifying triggers remain attached/referentially available to the frozen Research Sample.

Later evidence must never rewrite the frozen qualifying-trigger set.

### H. Cohort foundation metadata only
Implement/preserve only what Stage 9A needs for later descriptive analysis:
- ticker
- route-presence booleans
- mutually exclusive route composition
- existing canonical DTE semantic: VERY SHORT / SHORT / MEDIUM
- raw qualifying trigger count

Do not hardcode trigger-count buckets.

Keep the data model extensible for later Trend, IV, GEX, premium, OI-change magnitude, Structure/Cluster dimensions without implementing them now.

### I. Defensive outcome-window identity
Provide/specify an analysis-layer identity equivalent to:

`ticker + reference_session + T1_session + T3_session + T5_session`

This never replaces ProductCandidate identity.

If abnormal duplicate canonical production occurrences map to the same window:
- preserve all
- later primary aggregate counts one
- earliest candidate_first_knowledge_at, then ProductCandidate.id is deterministic fallback

No aggregate statistics are required in Stage 9A.

### J. Live/Research firewall
Prove through code structure/tests that live scanner/live ranking/current candidate APIs do not consume Forward Outcome.

Do not add current-candidate future-derived fields to live outputs.

## 7. Explicitly out of scope
Do not:
- implement Stage 9B outcome materialization/backfill
- run future-price backfill
- make paid Nightwatch API calls
- create another scheduler
- implement Research Dashboard pages
- change Phase 2A thresholds
- change Phase 2B semantics
- change live ranking
- infer bullish/bearish direction
- use future-derived live features
- create Actionability labels
- hardcode trigger-count buckets
- invent new DTE bucket thresholds
- perform destructive migration or historical repair

## 8. Required tests
At minimum prove:
1. one ProductCandidate with 27 qualifying triggers = one Research Sample
2. canonical scheduled production occurrence = primary eligible
3. manual/controlled/diagnostic/remediation occurrence = preserved but primary-ineligible
4. frozen baseline is not mutated
5. expired historical trigger remains valid Research evidence
6. premarket reference mapping
7. intraday reference mapping
8. post-close mapping
9. weekend/holiday mapping
10. early-close mapping
11. canonical Aug 20 → Aug 19 / Aug 20 / Aug 24 / Aug 26 mapping
12. Aug 26 T+5 before official close = NOT_YET_MATURE
13. missing T+N close != 0
14. T+N Close Return formula
15. Close-path Max Upside formula
16. Close-path Max Downside formula
17. no Daily High/Low dependency
18. direction remains UNRESOLVED
19. corporate-action basis must match across Reference/T+N
20. price-basis uncertainty fails closed
21. existing VERY SHORT / SHORT / MEDIUM source reused
22. raw trigger count preserved; no bucket hardcoding
23. live paths do not consume Forward Outcome
24. zero paid Nightwatch calls
25. additive migration integrity

Run focused tests and the complete relevant backend suite/lint/static checks.

## 9. Safety
Stage 9A may add additive schema/migration code.

Do not:
- apply destructive migrations
- historical-backfill outcomes
- write fabricated production maturity data
- call paid vendor endpoints

Use established isolated test mechanisms.

## 10. Completion report
Create:

`NIGHTWATCH_VNEXT_STAGE9A_FORWARD_OUTCOME_FOUNDATION_COMPLETION_REPORT_20260827.md`

Include:
- exact starting commit
- worktree/branch
- files changed
- migrations
- research schema/model decisions
- run-origin source/classification
- XNYS calendar implementation
- DTE canonical source reused
- OHLC/corporate-action finding
- reference/session tests
- outcome/maturity tests
- historical-trigger-retention proof
- Live/Research firewall proof
- paid Nightwatch calls = 0
- production outcome materialization/backfill = 0
- Stage 9B/9C implementation = 0
- test/lint results
- bounded gaps
- PASS / PASS_WITH_CARRIED_ITEMS / HOLD
- whether Stage 9B is technically ready, without authorizing Stage 9B

### Fixed report rule
The completion report must exist in BOTH:
1. `F:\options-anomaly-scanner-stage9a\docs\evidence\NIGHTWATCH_VNEXT_STAGE9A_FORWARD_OUTCOME_FOUNDATION_COMPLETION_REPORT_20260827.md`
2. `F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE9A_FORWARD_OUTCOME_FOUNDATION_COMPLETION_REPORT_20260827.md`

They must be byte-identical. Verify SHA-256.

If canonical same-name report already exists and is identical, verify/keep. If it differs, never overwrite; return conflict/HOLD.

## 11. Stop conditions
Return HOLD rather than guessing if:
- canonical main is dirty/diverged unexpectedly
- Stage 9 evidence conflicts
- ProductCandidate first-knowledge identity cannot be preserved
- canonical scheduled-production origin cannot be reliably classified
- exchange-aware XNYS mapping cannot be implemented
- price basis cannot be represented truthfully
- Stage 9A would make live paths consume Forward Outcome
- paid Nightwatch calls would be required
- destructive migration/history rewrite would be required

A corporate-action basis gap can be represented by a truthful fail-closed capability state; report whether that is PASS_WITH_CARRIED_ITEMS or HOLD for Stage 9B readiness.
