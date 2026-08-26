# Nightwatch Scanner vNext — Stage 8 MAG7 Observation Period — Execution Package

**Date:** 2026-08-20  
**Stage:** 8 — MAG7 OBSERVATION PERIOD  
**Executor:** Read-only observation collector/reviewer. A fresh Codex observation thread is acceptable for local repository/SQL access; final interpretation returns to the Founder/reviewer.  
**Authorization:** Stage 8 observation only  
**Accepted predecessor:** Stage 7 `CLOSED / ACCEPTED`  
**Current accepted Stage 7 worktree:** `F:\options-anomaly-scanner-stage7`  
**Current Stage 7 branch:** `vnext/stage7-candidate-first-dashboard`  
**Stage 7 predecessor/base:** `d6cb38f5399dd3e30e8855f667ee16ef93a373e0`  
**Expected Stage 8 branch:** `vnext/stage8-mag7-observation`  
**Preferred Stage 8 worktree:** `F:\options-anomaly-scanner-stage8`

---

# 0. Objective

Stage 8 is **not another implementation stage**.

Its job is to observe the completed vNext Scanner on real MAG7 data and determine whether the candidate/time/context architecture behaves coherently enough to enter the Stage 9 **Candidate Forward Outcome Design Gate**.

Founder-approved Stage 8 observation dimensions:

```text
candidates/day
anomalies/candidate
route frequencies
persistence maturation
context completeness / availability
ticker concentration
chain reuse rate
Phase 2B API cost
freshness failure rate
```

Stage 8 must also spot-check the two foundations Stage 9 will depend on:

```text
ProductCandidate identity / occurrence integrity
candidate_first_knowledge_at + frozen FIRST_KNOWLEDGE_BASELINE integrity
```

Stage 8 does **not** calibrate thresholds and does **not** measure Forward Outcome.

---

# 1. Why Stage 8 Exists

The integrated architecture is now:

```text
MAG7
  ↓
Phase 2A vNext
  ↓
ProductCandidate + ProductCandidateTrigger
  ↓
FIRST_KNOWLEDGE_BASELINE
  ↓
Phase 2B Balanced Context
  ↓
Candidate-First Dashboard
```

Stage 9 will later design retrospective Forward Outcome sampling keyed by:

```text
ProductCandidate
+ candidate_first_knowledge_at
+ frozen first-knowledge baseline
```

Therefore Stage 8 must verify the **real observed samples** are structurally trustworthy before Stage 9 designs any T+1 / T+3 / T+5 measurement.

---

# 2. Stage 8 Is Observation, Not Calibration

Do not infer or change:

```text
Radar material gate
Activity weights/gates
Persistence 3/5/10 anchors
Persistence freshness numeric window
0DTE weights/gates
Structure/Cluster thresholds
Deep-Dive budget
candidate ranking
universe
```

Do not say a route is "good", "bad", "too frequent", or "too rare" from Stage 8 observation alone.

Stage 8 records what happened.

Any future threshold calibration requires outcome evidence and separate authorization.

---

# 3. Bootstrap — Freeze Accepted Stage 7

Stage 7 is accepted but uncommitted.

Inside:

```text
F:\options-anomaly-scanner-stage7
```

verify:

```text
branch = vnext/stage7-candidate-first-dashboard
```

and verify the working tree matches the accepted Stage 7 completion state.

The Stage 7 completion report established:

```text
STAGE7_RESULT=PASS_WITH_CARRIED_ITEMS
ALEMBIC_HEAD=20260818_0017
Full backend=379/379
Stage7 frontend=13/13
MIGRATION_CREATED=NO
STAGE8_READY=YES
```

Do not assume the exact Stage 7 path set from memory. Inspect the Stage 7 diff against its base and reconcile it to the accepted completion report.

If unrelated/unreviewed changes are mixed into the Stage 7 working tree and cannot be isolated, STOP.

Stage only accepted Stage 7 paths.

Do not use:

```text
git add .
git add -A
```

Authorized local commit:

```text
vnext: accept stage7 candidate-first dashboard
```

Record:

```text
STAGE7_ACCEPTED_COMMIT=<sha>
```

Then create:

```text
branch   = vnext/stage8-mag7-observation
worktree = F:\options-anomaly-scanner-stage8
```

from exactly that commit.

No push, PR, merge, or remote branch.

Stage 8 application code must remain unchanged.

---

# 4. Governing Documents

Read completely before observation:

1. `NIGHTWATCH_SCANNER_VNEXT_INTEGRATED_SPEC_PROMPT_20260817(1).md`
2. `NIGHTWATCH_VNEXT_STAGE5_PRODUCT_CANDIDATE_PERSISTENCE_COMPLETION_REPORT_20260818.md`
3. `NIGHTWATCH_VNEXT_STAGE6_PHASE2B_BALANCED_MODEL_COMPLETION_REPORT_20260818.md`
4. Founder-provided Stage 6 baseline-cutoff remediation PASS result
5. `NIGHTWATCH_VNEXT_STAGE7_CANDIDATE_FIRST_DASHBOARD_COMPLETION_REPORT_20260819.md`
6. this Stage 8 package.

Authority:

```text
Founder-approved Integrated Spec
> this Stage 8 package
> accepted Stage 7/6/5 state
> current repository implementation detail
> older audits/reviews
```

---

# 5. Carried Ledger — Must Remain Explicit

Stage 8 begins with all six unresolved carried items:

```text
CURRENT_TRIGGER_FRESHNESS_MODE=CALIBRATION_REQUIRED

RADAR_OI_SCHEDULE_ACTIVATION=PENDING_ROLLOVER_EVIDENCE

CROSS_RUN_CANDIDATE_LIFECYCLE=DEFERRED_NO_AUTO_MERGE

IV_RANK_CORE_ELIGIBILITY=WITHHOLD_PENDING_PROVENANCE

ISOLATED_POSTGRES_RUNTIME_VERIFIED=NO

N1_HISTORICAL_RUNTIME_DISTRIBUTION_VERIFIED=NO
```

Do not silently drop any of them because a later completion report omitted them.

Stage 8 may **observe evidence relevant to a carried item**, but it may not resolve one by invention.

---

# 6. Critical Runtime Prerequisite Gate

Stage 8 requires genuine vNext runtime observations.

Before querying observation data, determine whether an already-configured observation runtime database exists and is compatible with the accepted code.

Read-only checks only.

Do not print or log credentials.

Required:

```text
RUNTIME_DB_REACHABLE=YES/NO
RUNTIME_DB_SCHEMA_HEAD=
RUNTIME_PRODUCT_CANDIDATE_TABLE_PRESENT=YES/NO
RUNTIME_PRODUCT_CANDIDATE_TRIGGER_TABLE_PRESENT=YES/NO
RUNTIME_PRODUCT_CANDIDATE_CONTEXT_TABLE_PRESENT=YES/NO
RUNTIME_ANOMALY_CONTEXT_DETAIL_TABLE_PRESENT=YES/NO
```

Healthy runtime prerequisite:

```text
RUNTIME_DB_SCHEMA_HEAD=20260818_0017
```

or an explicitly proven descendant that contains the exact accepted 0017 schema without incompatible changes.

## Hard rule

This Stage 8 package does **not** authorize:

```text
alembic upgrade
remote migration
remote schema write
runtime deployment
historical backfill
```

If the configured runtime is below 0017 or required tables do not exist:

```text
STAGE8_RESULT=HOLD_RUNTIME_PREREQUISITE
STAGE8_RUNTIME_SCHEMA_READY=NO
RUNTIME_DEPLOYMENT_GATE_REQUIRED=YES
```

STOP.

Do not "observe" pre-vNext data and label it Stage 8 evidence.

---

# 7. Real-vNext Sample Eligibility

Only observations generated under the accepted Stage 5/6 semantics may count as Stage 8 samples.

A ProductCandidate occurrence is eligible only if its persisted provenance proves:

```text
current active ProductCandidate materialization rule/version
immutable candidate_first_knowledge_at
persisted trigger set
```

A Phase 2B baseline is eligible only if:

```text
evaluation_kind=FIRST_KNOWLEDGE_BASELINE
its candidate relationship is authoritative
its evidence follows the corrected cutoff:
evidence_cutoff = candidate_first_knowledge_at
```

Do not mix old v1.2/v2.0/v3.1 evaluations into active Stage 8 samples.

Legacy rows may be inspected as audit context only.

---

# 8. Observation Source Priority

Use this priority:

```text
1. Existing real vNext persisted runtime observations
2. Existing scheduled/daily data already produced by authorized workflows
3. Existing real Stage 6 baseline/refresh observations
```

Do not manufacture observations from deterministic unit fixtures and call them Stage 8.

Fixtures may be used only to verify query logic.

---

# 9. Paid Calls / Live Scan Authorization Gate

This package does **not automatically authorize a new paid MAG7 scan or Phase 2B refresh**.

Default:

```text
STAGE8_LIVE_MAG7_AUTHORIZED=NO
STAGE8_LIVE_CONTEXT_REFRESH_AUTHORIZED=NO
```

If sufficient genuine vNext observations already exist, analyze them with zero new vendor calls.

If no usable sample exists and a new live scan would be required:

```text
STAGE8_RESULT=HOLD_LIVE_OBSERVATION_AUTHORIZATION
CONTROLLED_MAG7_OBSERVATION_REQUIRED=YES
```

STOP and request explicit Founder authorization.

Do not treat this package as implicit permission to spend paid units.

If the Founder later provides an explicit authorization token/package for a controlled live observation, use only the exact allowed run count/cost cap in that later authorization.

---

# 10. Observation Window Semantics

Do **not** invent a statistical "minimum sample size" or claim calibration sufficiency from an arbitrary number of days.

Observe all eligible real vNext samples currently available.

Report:

```text
OBSERVATION_FIRST_MARKET_DATE=
OBSERVATION_LAST_MARKET_DATE=
OBSERVED_COMPLETED_MARKET_DATES=
OBSERVED_SUCCESSFUL_SCAN_RUNS=
OBSERVED_FAILED_SCAN_RUNS=
OBSERVED_PRODUCT_CANDIDATE_OCCURRENCES=
OBSERVED_DISTINCT_CANDIDATE_DAYS=
```

If evidence is too sparse to evaluate one or more required Stage 8 dimensions, use:

```text
STAGE8_RESULT=CONTINUE_OBSERVATION
```

and state exactly which observation dimensions remain unobserved/immature.

Do not invent "5 days", "10 days", or another pass threshold.

---

# 11. Canonical Aggregation Rules

Multiple interactive scans can occur on the same NY market date.

Do not treat reruns as independent market days.

Report both:

```text
run-level candidate occurrences
and
market-date distinct ticker candidates
```

Definitions:

```text
candidate occurrence
= one persisted ProductCandidate linked to one authoritative ScanRun occurrence

candidate-day
= distinct (NY market date, ticker) represented by at least one eligible ProductCandidate occurrence
```

For `candidates/day`, report:

```text
distinct candidate-days by market date
```

Also disclose:

```text
successful scan runs per market date
```

so rerun density is visible.

Do not auto-merge cross-run ProductCandidate occurrences; lifecycle remains deferred.

---

# 12. O1 — Candidates / Day

For every observed NY market date report:

```text
market date
successful runs
distinct ProductCandidate tickers
ProductCandidate occurrences
zero-candidate successful runs
failed runs
```

Summary:

```text
candidate-days total
candidate occurrences total
min / median / max distinct candidates per observed day
```

These are descriptive only.

No ranking.

No judgment of "too many" or "too few".

---

# 13. O2 — Anomalies / Candidate

For every eligible ProductCandidate occurrence report:

```text
ticker
candidate id
candidate_first_knowledge_at
trigger count
qualifying trigger count
supporting trigger count
contract trigger count
expiry trigger count
```

Aggregate:

```text
min
median
max
distribution/count table
```

Do not create an Evidence Breadth score.

Anomaly count is descriptive only.

---

# 14. O3 — Route Frequencies

Active families only:

```text
RADAR_EVENT
EXPIRY_ACTIVITY
CONTRACT_PERSISTENCE
```

Report at two levels:

## Trigger-level

```text
family
trigger count
qualifying count
supporting count
share of observed active triggers
```

## Candidate-level family presence

Examples:

```text
RADAR only
EXPIRY_ACTIVITY only
CONTRACT_PERSISTENCE only
RADAR + EXPIRY_ACTIVITY
RADAR + CONTRACT_PERSISTENCE
EXPIRY_ACTIVITY + CONTRACT_PERSISTENCE
all three
```

Do not call multi-family presence "confirmation" or "higher conviction".

Removed routes remain excluded.

---

# 15. O4 — Persistence Maturation

Observe Contract Persistence without changing its rules.

Preserve:

```text
CURRENT_TRIGGER_FRESHNESS_MODE=CALIBRATION_REQUIRED
```

Where current persisted analytics expose them, report:

```text
valid observation count
3 / 5 / 10 accepted observation anchors
window first date
window last date
span days
current-trigger eligible vs supporting-only
history immature / mature state
```

Do not invent a freshness window.

Do not infer missing observations as zero.

If no genuine persistence sample is present:

```text
PERSISTENCE_MATURATION_OBSERVED=NO
```

This is an observation gap, not a reason to fabricate data.

---

# 16. O5 — Context Availability Matrix

The integrated spec calls for context completeness observation, but Stage 6 deliberately removed a composite readiness score.

Therefore Stage 8 must **not recreate one**.

For every eligible baseline context, report independent availability for:

```text
B1 Price
B2 Volatility
B3 Dealer/GEX
B4 anomaly detail
B5 provenance/time
```

Use only accepted states such as:

```text
AVAILABLE
PARTIAL
UNAVAILABLE
NOT_YET_AVAILABLE
HISTORY_IMMATURE
STALE_DATA
```

Report per-layer counts/rates.

Also report:

```text
CANDIDATES_WITH_BASELINE=
CANDIDATES_WITHOUT_BASELINE=
BASELINE_EXISTENCE_RATE=
```

This is operational coverage, not a score.

Do not sum B1–B5 into "4/5 context score".

---

# 17. O6 — Ticker Concentration

For MAG7 only.

Report:

```text
ticker
candidate occurrences
candidate-days
share of candidate occurrences
share of candidate-days
```

No universe expansion.

No concentration threshold.

Do not call concentration "bias" without outcome evidence.

---

# 18. O7 — Chain Reuse

The accepted architecture requires one shared chain-context load per ticker-expiry and zero per-contract paid calls.

Observe only what current telemetry can prove.

Report:

```text
CHAIN_REUSE_TELEMETRY_AVAILABLE=YES/NO
```

If actual runtime load/request telemetry exists, calculate the documented reuse rate from authoritative records and show the exact formula.

If only shared source identity can be proven, report:

```text
CHAIN_SOURCE_IDENTITY_REUSE_OBSERVED=YES/NO
```

and counts such as:

```text
contract anomaly details
unique ticker-expiry chain source identities
details sharing an existing source identity
```

Do **not** convert this into an "actual loader call rate" unless runtime telemetry proves actual load counts.

If unmeasurable:

```text
CHAIN_REUSE_RATE=UNRESOLVED_CURRENT_TELEMETRY
```

Do not add instrumentation in Stage 8.

---

# 19. O8 — Phase 2B API Cost

Measure actual observed cost only where authoritative telemetry exists.

Separate:

```text
FIRST_KNOWLEDGE_BASELINE
REFRESH
```

Baseline design:

```text
no hidden paid calls
```

Refresh design contract:

```text
daily_ohlc
stock_state
iv_rank
term_structure

up to 4 ticker-level calls
0 per-anomaly calls
Dealer/GEX archive-only
```

For observed refreshes report where provable:

```text
refresh count
source request count by endpoint
paid units / quota delta
calls per refresh
per-anomaly calls
dealer heatmap calls
```

If no real refresh occurred:

```text
PHASE2B_REFRESH_COST_OBSERVED=NO
```

Do not execute a refresh merely to fill the metric without separate paid-call authorization.

---

# 20. O9 — Freshness Failure Rate

Observe per-layer freshness/availability failures without creating a composite penalty.

For each layer/source, report numerator/denominator and exact state counts:

```text
AVAILABLE
PARTIAL
UNAVAILABLE
NOT_YET_AVAILABLE
STALE_DATA
HISTORY_IMMATURE
```

Where applicable distinguish reason:

```text
missing source
stale source
post-cutoff source
history immature
IV Rank provenance withheld
archive missing
quote missing
```

Do not treat IV Rank `WITHHOLD_PENDING_PROVENANCE` as a trading-negative feature.

---

# 21. Additional Audit Metric — Baseline Creation Lag

Because Stage 6 required a critical cutoff remediation, Stage 8 must observe:

```text
baseline_creation_lag
=
FIRST_KNOWLEDGE_BASELINE.context_evaluated_at
-
ProductCandidate.candidate_first_knowledge_at
```

Report distribution descriptively.

This lag does **not** change baseline eligibility because the evidence cutoff remains `candidate_first_knowledge_at`.

Flag as a defect only if observed baseline source evidence violates that cutoff.

No acceptable/unacceptable lag threshold is invented in Stage 8.

---

# 22. Mandatory First-Knowledge Integrity Spot Check

For all eligible samples if tractable, otherwise for a clearly stated deterministic sample covering multiple trigger/context types, verify:

```text
candidate_first_knowledge_at immutable

baseline evaluation_kind = FIRST_KNOWLEDGE_BASELINE

baseline source receipt/capture/as-of
<= candidate_first_knowledge_at
where that source has an authoritative time

post-candidate/pre-evaluation evidence
not present in baseline

REFRESH does not mutate baseline

baseline trigger-id set
matches persisted candidate trigger set
```

For B1 OHLC, preserve the corrected semantics:

```text
payload/source evidence must be knowable by cutoff
bars after the cutoff's New York trading date are excluded
missing/malformed bar date fails closed
```

No Forward Outcome data is involved.

Return:

```text
OBSERVED_BASELINE_LOOKAHEAD_FOUND=YES/NO
OBSERVED_BASELINE_MUTATION_FOUND=YES/NO
OBSERVED_TRIGGER_SET_DRIFT_FOUND=YES/NO
```

Any `YES` is a Stage 8 blocking defect.

---

# 23. Candidate / Budget Integrity Spot Check

Verify on observed data:

```text
all persisted qualifying ProductCandidates are surfaced
Deep-Dive selection/budget does not suppress candidate existence
```

Report:

```text
OBSERVED_VALID_CANDIDATE_OMISSION_FOUND=YES/NO
OBSERVED_DEEP_DIVE_BUDGET_SUPPRESSION_FOUND=YES/NO
```

Any `YES` is blocking.

---

# 24. Run-State / Operational Observation

Report real observed counts for:

```text
SUCCESS_WITH_CANDIDATES
SUCCESS_NO_CANDIDATE
FAILED
RUNNING if stale/orphaned
```

Also observe where available:

```text
last daily collection success
Dealer/GEX archive latest vendor observation
quota age/remaining
Radar/OI collection state
```

Do not rewrite failed runs.

Do not repair missing data.

---

# 25. 0DTE Observation

Where genuine 0DTE data exists, report observed counts for:

```text
PROVISIONAL_INTRADAY
CANONICAL_SESSION_COMPLETE
LEGACY_OR_AMBIGUOUS
```

and:

```text
history observation count
maturity state
fallback status
```

Do not let provisional/legacy rows enter canonical baseline analysis.

Do not alter the 0DTE 20-observation design.

---

# 26. Carried Gate Observation — Radar/OI Rollover

The existing rollover-timing experiment is independent.

Stage 8 may read its already-produced evidence.

Do not activate Radar/OI production scheduling in this package.

Report:

```text
ROLLOVER_EVIDENCE_AVAILABLE=YES/NO
RADAR_OI_SCHEDULE_ACTIVATION=PENDING_ROLLOVER_EVIDENCE
```

unless a separate Founder-approved timing decision already exists in the repository.

Do not infer a schedule from Stage 8 scanner observations.

---

# 27. No Forward Outcome

Do not calculate or persist:

```text
T+1 return
T+3 return
T+5 return
MFE
MAE
max upside
max downside
future price path
event response
actionability
```

Even if future prices are already available for observed candidates.

Stage 9 is the design gate for those metrics.

Stage 8 may inspect only same-time candidate/context integrity and operational behavior.

---

# 28. No Code / Schema Changes

Stage 8 authorized writes are limited to Stage 8 evidence artifacts under:

```text
docs/evidence/stage8/
```

or one equivalent existing evidence directory.

Allowed evidence artifacts:

```text
read-only SQL/query text
sanitized CSV/JSON summaries with no secrets
observation tables
Stage 8 report
```

No application source edits.

No test edits.

No migrations.

No workflows.

No scheduler edits.

No config edits.

If observation reveals a production defect:

```text
record it
classify severity
STOP remediation
```

A fix requires a separate scoped remediation package.

---

# 29. Secret / Data Safety

Do not print:

```text
DB password
connection string with credentials
Nightwatch API key
Authorization header
raw secrets
```

Do not include full raw vendor payloads in the report when a safe normalized summary is sufficient.

Request IDs / raw payload IDs may be recorded if already considered safe project audit identifiers.

---

# 30. Mandatory Repository Orientation

Before observation report:

```text
REPOSITORY_ORIENTATION
- Stage7 accepted diff:
- Stage7 dashboard candidate route:
- ProductCandidate model/repository:
- ProductCandidateTrigger model/repository:
- ProductCandidateContext model/repository:
- AnomalyContextDetail model/repository:
- ScanRun market-date/status source:
- daily collection health source:
- Dealer/GEX archive source:
- quota metadata source:
- persistence analytics source:
- 0DTE status source:
- Stage6 request/provenance telemetry:
- rollover experiment evidence location:
- Alembic head:
```

Then:

```text
STAGE8_EVIDENCE_QUERY_PLAN
- query/view:
- metric supported:
- read-only proof:
```

No writes before the runtime prerequisite gate is satisfied.

---

# 31. Observation Result States

Use one:

```text
STAGE8_RESULT=PASS_WITH_CARRIED_ITEMS
STAGE8_RESULT=CONTINUE_OBSERVATION
STAGE8_RESULT=HOLD_RUNTIME_PREREQUISITE
STAGE8_RESULT=HOLD_LIVE_OBSERVATION_AUTHORIZATION
STAGE8_RESULT=FAIL_BLOCKING_INTEGRITY_DEFECT
```

Interpretation:

## PASS_WITH_CARRIED_ITEMS

Use only when:

```text
real vNext sample exists
candidate/time/baseline integrity is clean
required observation dimensions are meaningfully observable
no blocking semantic/operational defect is found
```

Unobserved rare route combinations may remain explicitly carried.

## CONTINUE_OBSERVATION

Use when:

```text
runtime is healthy
real samples exist
no blocking defect is found
but one or more required Stage 8 dimensions are still too sparse/unobserved to characterize
```

Do not invent a numeric sufficiency threshold.

## HOLD_RUNTIME_PREREQUISITE

Use when accepted vNext runtime/schema is not actually deployed/available.

## HOLD_LIVE_OBSERVATION_AUTHORIZATION

Use when no genuine sample exists and producing one requires a paid scan/context refresh not separately authorized.

## FAIL_BLOCKING_INTEGRITY_DEFECT

Use for observed:

```text
lookahead
baseline mutation
candidate omission
trigger-set drift
legacy rows entering vNext sample
wrong entity semantics
silent failure/empty-success contamination
```

Do not fix in this package.

---

# 32. Stage 9 Readiness Rule

Stage 9 is a **design gate**, not outcome calculation.

Stage 8 may return:

```text
STAGE9_READY=YES
```

only when:

```text
1. at least one genuine vNext ProductCandidate + frozen baseline sample exists;
2. observed candidate/time/baseline integrity has no blocking defect;
3. observation metrics required by Stage 8 are either:
   - actually observed, or
   - explicitly marked NOT_OBSERVED / UNRESOLVED_CURRENT_TELEMETRY with a reason;
4. no unresolved item requires changing the ProductCandidate sample key or first-knowledge semantics before Forward Outcome can be designed.
```

Do not require every active route family to appear before Stage 9 design.

Do not claim statistical calibration sufficiency.

If persistence maturation or API-cost behavior remains unobserved but architecture/sample integrity is stable, carry it explicitly and explain whether it blocks Stage 9 design.

---

# 33. Required Stage 8 Report

Create:

```text
docs/evidence/stage8/NIGHTWATCH_VNEXT_STAGE8_MAG7_OBSERVATION_REPORT_20260820.md
```

Optional sanitized machine-readable summaries may sit beside it.

Report:

## A. Result

```text
STAGE8_RESULT=
```

## B. Bootstrap

```text
STAGE7_ACCEPTED_COMMIT=
STAGE8_BRANCH=
STAGE8_WORKTREE=
STAGE8_BASE_HEAD=
APPLICATION_CODE_CHANGES=0
```

## C. Runtime prerequisite

```text
RUNTIME_DB_REACHABLE=
RUNTIME_DB_SCHEMA_HEAD=
STAGE8_RUNTIME_SCHEMA_READY=
```

## D. Observation window

```text
OBSERVATION_FIRST_MARKET_DATE=
OBSERVATION_LAST_MARKET_DATE=
OBSERVED_COMPLETED_MARKET_DATES=
OBSERVED_SUCCESSFUL_SCAN_RUNS=
OBSERVED_FAILED_SCAN_RUNS=
OBSERVED_PRODUCT_CANDIDATE_OCCURRENCES=
OBSERVED_DISTINCT_CANDIDATE_DAYS=
```

## E. O1 Candidates/day

Daily table + descriptive summary.

## F. O2 Anomalies/candidate

Occurrence table + descriptive distribution.

## G. O3 Route frequencies

Trigger-level and candidate-level family combinations.

## H. O4 Persistence maturation

```text
PERSISTENCE_MATURATION_OBSERVED=YES/NO
```

plus available counts/windows/states.

## I. O5 Context availability

B1–B5 per-layer availability matrix.

No composite score.

## J. O6 Ticker concentration

MAG7 counts/shares only.

## K. O7 Chain reuse

```text
CHAIN_REUSE_TELEMETRY_AVAILABLE=
CHAIN_SOURCE_IDENTITY_REUSE_OBSERVED=
CHAIN_REUSE_RATE=
```

## L. O8 Phase 2B API cost

```text
PHASE2B_REFRESH_COST_OBSERVED=
OBSERVED_REFRESH_COUNT=
OBSERVED_VENDOR_REQUESTS=
OBSERVED_PAID_UNITS=
PER_ANOMALY_VENDOR_CALLS=
DEALER_HEATMAP_CALLS=
```

Unknown stays unknown.

## M. O9 Freshness failures

Per-layer state counts/rates and reasons.

## N. Baseline lag / integrity

```text
BASELINE_CREATION_LAG_OBSERVED=YES/NO
OBSERVED_BASELINE_LOOKAHEAD_FOUND=YES/NO
OBSERVED_BASELINE_MUTATION_FOUND=YES/NO
OBSERVED_TRIGGER_SET_DRIFT_FOUND=YES/NO
```

## O. Candidate/budget integrity

```text
OBSERVED_VALID_CANDIDATE_OMISSION_FOUND=
OBSERVED_DEEP_DIVE_BUDGET_SUPPRESSION_FOUND=
```

## P. Operational/run state

Run-state counts, daily archive health, Dealer/GEX age, quota facts where available.

## Q. 0DTE

Observed status/maturity distributions if present.

## R. Carried ledger

Return all six:

```text
CURRENT_TRIGGER_FRESHNESS_MODE=CALIBRATION_REQUIRED
RADAR_OI_SCHEDULE_ACTIVATION=PENDING_ROLLOVER_EVIDENCE
CROSS_RUN_CANDIDATE_LIFECYCLE=DEFERRED_NO_AUTO_MERGE
IV_RANK_CORE_ELIGIBILITY=WITHHOLD_PENDING_PROVENANCE
ISOLATED_POSTGRES_RUNTIME_VERIFIED=NO/YES
N1_HISTORICAL_RUNTIME_DISTRIBUTION_VERIFIED=NO/YES
```

Only change YES/NO when actually proven under authorization.

## S. New observations / defects

Each:

```text
finding
evidence
severity
blocking Stage9? YES/NO
requires remediation? YES/NO
```

No fix.

## T. Authorization ledger

```text
APPLICATION_CODE_CHANGES=0
TEST_CODE_CHANGES=0
MIGRATION_CREATED=0
REMOTE_MIGRATIONS_RUN=0
REMOTE_DB_WRITES=0
WORKFLOWS_DISPATCHED=0

NIGHTWATCH_REQUESTS=
PAID_UNITS=

STAGE7_ACCEPTED_COMMITS_CREATED=1
STAGE8_IMPLEMENTATION_COMMITS_CREATED=0

PUSHES=0
PRS_CREATED=0
MERGES=0

EXTERNAL_URLS_OR_API_ENDPOINTS_CONTACTED=[]
```

With this package as initially issued, expected:

```text
NIGHTWATCH_REQUESTS=0
PAID_UNITS=0
```

because paid observation is separately gated.

## U. Stage 9 readiness

```text
STAGE9_READY=YES/NO
NEXT_AUTHORIZED_STAGE=NONE
```

Do not start Stage 9.

---

# 34. Hard STOP Conditions

STOP if:

- Stage 7 accepted state cannot be isolated cleanly;
- runtime DB is not at accepted 0017-compatible schema;
- runtime access would require applying migrations;
- no real vNext data exists and paid live observation is not explicitly authorized;
- queries would mutate application data;
- a fix is required;
- observation would require universe expansion;
- Forward Outcome would need to be calculated;
- a carried semantic must be guessed;
- secrets would need to be exposed.

---

# 35. Authorization Summary

Authorized:

```text
one local accepted Stage7 commit
new Stage8 branch/worktree
repository read-only inspection
already-configured runtime DB SELECT-only observation
read-only analysis of existing vNext MAG7 observations
sanitized Stage8 evidence/report files
```

Not authorized:

```text
application code changes
test changes
migration/schema changes
runtime deployment
remote DB writes
new live paid MAG7 scan
Phase2B paid refresh
workflow dispatch
scheduler changes
universe expansion
Forward Outcome
Actionability
Trade Expression
threshold calibration
push/PR/merge
```

At completion:

```text
NEXT_AUTHORIZED_STAGE=NONE
```

STOP.
