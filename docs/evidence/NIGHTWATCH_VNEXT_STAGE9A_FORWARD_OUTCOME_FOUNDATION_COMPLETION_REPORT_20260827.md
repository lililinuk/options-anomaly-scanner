# NIGHTWATCH vNext — Stage 9A Forward Outcome Foundation Completion Report

**Date:** 2026-08-27  
**Result:** `PASS_WITH_CARRIED_ITEMS`  
**Stage boundary:** Stage 9A only; Stage 9B and Stage 9C are not implemented or authorized by this report.

```text
DIRECT_START_BASELINE = ae8e4a28de411b61fdfd1933118f62159381eaed
SEPARATE_BASELINE_VALIDATION_GATE = WAIVED_BY_FOUNDER
WORKTREE = F:\options-anomaly-scanner-stage9a
BRANCH = vnext/stage9a-forward-outcome-foundation
REFERENCE_PRICE_POLICY = PRIOR_COMPLETED_REGULAR_CLOSE
OUTCOME_METHODOLOGY_VERSION = stage9a.close-path.v1
DIRECTION = UNRESOLVED
SECOND_FORWARD_OUTCOME_SCHEDULER = NO
PAID_NIGHTWATCH_CALLS = 0
PRODUCTION_OUTCOME_MATERIALIZATION_OR_BACKFILL = 0
STAGE9B_IMPLEMENTATION = 0
STAGE9C_IMPLEMENTATION = 0
```

## 1. Authorization and provenance

The Founder direct-start authorization superseded the prior baseline HOLD and authorized Stage 9A directly from:

`main @ ae8e4a28de411b61fdfd1933118f62159381eaed`

The worktree and branch were created from that exact commit. No merge, integration commit, push, or main-branch code change was performed.

The following supplied Stage 9 evidence files were absent from canonical evidence, copied byte-for-byte to both canonical evidence and the Stage 9A worktree, and verified by SHA-256:

| Evidence | SHA-256 |
|---|---|
| `NIGHTWATCH_VNEXT_STAGE9_DESIGN_GATE_FINAL_20260827.md` | `d7b21ad6b3df7a54aa3dcd00b0bc46dd1d9c48c6b1725420fd6a46664e032759` |
| `NIGHTWATCH_VNEXT_STAGE9_HISTORICAL_TRIGGER_RETENTION_DESIGN_DECISION_20260826.md` | `58296f54f567f9873f84d61e0d26db5ea96fc08c7a7040fc49370d6aad50bd48` |
| `NIGHTWATCH_VNEXT_STAGE9A_FORWARD_OUTCOME_FOUNDATION_EXECUTION_PACKAGE_20260827.md` | `c730ce90db2f55963b8babdb58a603ca7ba1e4760e5c429439ce07859473929f` |
| `NIGHTWATCH_VNEXT_STAGE9A_DIRECT_START_AUTHORIZATION_20260827.md` | `034d8b39c477e433bbb503fc816d6c629f8ef3ef1cfbde7932e31988fcac68e8` |

The Founder-approved Trading Dashboard vNext amendment was also read and enforced as an authoritative boundary between Current Trading Context, Frozen First-Knowledge evidence, and Stage 9 Research.

## 2. Repository inspection findings

### ProductCandidate occurrence identity

- `product_candidates` already provides one immutable occurrence keyed by its UUID and uniquely constrained by `scan_run_id + ticker + materialization_rule_version`.
- `candidate_first_knowledge_at`, scan identity, ticker, materialization version, and hash are ORM-immutable.
- `product_candidate_triggers` preserves qualifying and supporting evidence separately using `qualifies_candidate` and `present_at_first_knowledge`.
- A candidate can retain many trigger rows without becoming many Research Samples.

### Frozen First-Knowledge Baseline

- `product_candidate_contexts.evaluation_kind` distinguishes `FIRST_KNOWLEDGE_BASELINE` from `REFRESH`.
- The baseline is unique by candidate/spec/config identity and carries the same immutable `candidate_first_knowledge_at`.
- Stage 9A binds Research identity to the baseline context UUID and never updates the baseline or its trigger set.

### Scan origin

- `scan_runs.trigger` is the existing explicit, persisted origin source.
- The canonical scheduled workflow calls the scanner exactly once with `trigger="scheduled_daily"` after Activity readiness passes.
- Existing non-canonical entry points use explicit values such as `cli` and `dashboard`.
- No classification relies on wall-clock inference.

### Historical OHLC and price semantics

- Daily OHLC is preserved in `raw_vendor_payloads` and normalized through the existing regular-session parser.
- The parser retains one unambiguous `session=regular` bar per trading date and reports missing/ambiguous dates rather than zero-filling.
- The repository explicitly records `price_adjustment_semantics = UNCONFIRMED`.
- No authoritative proof currently establishes a corporate-action-consistent adjusted basis for Reference and T+N prices.

### Canonical DTE semantics

Stage 9A reuses `app.models.signals.bucket_for_dte` and `DEFAULT_DTE_BUCKET_RULES`:

- `VERY_SHORT`: 0–7 calendar DTE
- `SHORT`: 8–30 calendar DTE
- `MEDIUM`: 31–90 calendar DTE
- existing `LONG`: 91–180 remains preserved where present and is not used as an admission filter

No Stage 9 thresholds or trigger-count buckets were introduced.

### Calendar and migration head

- The repository already depends on `exchange-calendars` and uses the `XNYS` calendar.
- Persisted timestamps remain UTC; market/session interpretation uses `America/New_York` and official XNYS session closes.
- Pre-Stage-9A migration head: `20260818_0017`.
- New additive head: `20260827_0018`.

### Live dependency graph

- Live scan routes import scanner/candidate/context modules directly.
- Stage 9A code is isolated under `app.research`.
- No live scanner, live ranking, current-candidate API, frontend route, workflow, or scheduler imports or exposes Forward Outcome.

## 3. Implementation

### Additive schema

Migration `20260827_0018_stage9a_forward_outcome_foundation.py` creates two empty tables only:

1. `forward_outcome_research_samples`
   - unique one-to-one ProductCandidate occurrence identity;
   - Frozen First-Knowledge Baseline FK, with explicit invalid-sample representation when absent or inconsistent;
   - explicit run-origin source, classification version, and primary-eligibility flag;
   - ticker, immutable first-knowledge anchor, route presence/composition, raw qualifying trigger count, and canonical DTE bucket counts;
   - Reference/T+1/T+3/T+5 XNYS session identities;
   - defensive outcome-window key;
   - reference policy, price-basis capability/provenance, methodology version, and `UNRESOLVED` direction.

2. `forward_outcome_measurements`
   - append-only/versioned compatibility for later Stage 9B;
   - one horizon per revision for T+1/T+3/T+5;
   - explicit maturity state and nullable Reference/target/metric fields;
   - DB constraints prevent an available outcome without all metrics and a proven named basis;
   - direction is locked to `UNRESOLVED`.

The migration performs no historical query, `INSERT`, outcome `UPDATE`, or backfill. The measurement table remains empty by Stage 9A design.

### Production-origin classification

The versioned mapping is:

| Persisted trigger | Classification | Primary eligible |
|---|---|---:|
| `scheduled_daily` | `CANONICAL_SCHEDULED_PRODUCTION` | yes, when the sample is valid |
| `cli` | `MANUAL` | no |
| `dashboard` | `CONTROLLED_OBSERVATION` | no |
| `diagnostic` / test evidence | `DIAGNOSTIC` | no |
| `remediation` | `REMEDIATION` | no |
| `developer_rerun` | `DEVELOPER_RERUN` | no |
| unknown explicit value | `OTHER_NON_CANONICAL` | no |

Non-primary occurrences remain represented. Origin changes aggregation eligibility only; it is not a second candidate-admission filter.

### XNYS reference and target sessions

`map_forward_sessions` uses the authoritative XNYS calendar and official session close timestamps:

- premarket/intraday: Reference = prior completed session; T+1 = current session;
- after close: same-day Reference is allowed only when that Close is proven known as-of first knowledge; T+1 = next session;
- exact close: handled by the same completed-and-known rule;
- weekend/holiday: Reference = latest prior XNYS session; T+1 = next XNYS session;
- early closes and DST: taken from exchange-calendar data, never hard-coded at 16:00;
- T+3/T+5 advance through trading sessions, not calendar days.

The canonical test maps Aug 20, 2026 06:07 ET to Aug 19 Reference, Aug 20 T+1, Aug 24 T+3, and Aug 26 T+5.

### Maturity and outcome formulas

Maturity states are:

- `NOT_YET_MATURE`
- `MATURE_AVAILABLE`
- `MATURE_MISSING_DATA`
- `INVALID_SAMPLE`

A target date is not mature before its official XNYS close. Missing data remains `None`/NULL and is never converted to zero.

Pure Decimal formulas implement only:

- `T+N Close Return = CN / R - 1`
- `Max Upside through T+N = max(C1...CN) / R - 1`
- `Max Downside through T+N = min(C1...CN) / R - 1`

The input contract contains session, Close, and price-basis evidence only. Daily High/Low, MFE/MAE, direction inference, Actionability, scoring, and ranking are absent.

### Corporate-action price-basis gate

All Reference and future Close evidence must:

- carry `PROVEN_CONSISTENT` corporate-action status;
- share one non-empty basis identity; and
- retain provenance.

Unconfirmed or mismatched evidence raises a fail-closed error and cannot produce metrics. The persisted schema independently enforces the same available-outcome rule.

### Historical triggers and cohort metadata

- Cohort metadata counts only `qualifies_candidate=true` and `present_at_first_knowledge=true` rows.
- Contract/expiry active state and current date are not consulted; expired historical evidence remains included.
- Route presence and the seven mutually exclusive route compositions are preserved.
- Raw qualifying trigger count is stored without trigger-count buckets.
- DTE counts reuse the canonical Scanner bucket function.

### Defensive outcome-window identity

The analysis-layer key is:

`ticker | reference_session | T1_session | T3_session | T5_session`

It never replaces ProductCandidate identity. A defensive selector chooses the earliest `candidate_first_knowledge_at`, then ProductCandidate UUID, only among primary-eligible occurrences sharing one window. All occurrences remain preserved.

## 4. Files changed

### Backend implementation

- `backend/alembic/versions/20260827_0018_stage9a_forward_outcome_foundation.py`
- `backend/app/research/__init__.py`
- `backend/app/research/aggregation.py`
- `backend/app/research/forward_outcome.py`
- `backend/app/research/models.py`
- `backend/tests/test_stage9a_forward_outcome_foundation.py`

### Canonical/worktree evidence

- `docs/evidence/NIGHTWATCH_VNEXT_STAGE9_DESIGN_GATE_FINAL_20260827.md`
- `docs/evidence/NIGHTWATCH_VNEXT_STAGE9_HISTORICAL_TRIGGER_RETENTION_DESIGN_DECISION_20260826.md`
- `docs/evidence/NIGHTWATCH_VNEXT_STAGE9A_FORWARD_OUTCOME_FOUNDATION_EXECUTION_PACKAGE_20260827.md`
- `docs/evidence/NIGHTWATCH_VNEXT_STAGE9A_DIRECT_START_AUTHORIZATION_20260827.md`
- `docs/evidence/NIGHTWATCH_VNEXT_STAGE9A_FORWARD_OUTCOME_FOUNDATION_COMPLETION_REPORT_20260827.md`

No frontend source, API route, workflow, scheduler, Phase 2A threshold, Phase 2B semantic, or live-ranking file changed.

## 5. Verification results

| Check | Result |
|---|---|
| Focused Stage 9A tests | `29 passed` |
| Complete backend suite | `442 passed` |
| Repository-wide Ruff | passed |
| Alembic head | `20260827_0018 (head)` |
| Offline PostgreSQL migration compilation | passed; generated additive DDL successfully |
| Frontend ESLint | passed |
| Frontend glossary semantic check | passed; 34 governed concepts |
| Frontend Stage 7 regression suite | passed; 13 tests |
| Frontend production build | passed |
| `git diff --check` | passed; only a Git line-ending advisory for the pre-existing Research package initializer |

The first production-build attempt used a temporary dependency junction and Turbopack rejected that environmental layout because the junction pointed outside the project root. The junction was removed after target verification, dependencies were installed from the local npm cache with `npm ci --offline`, and the final production build passed. No registry request was made.

Automated tests used local fixtures, synthetic proven price-basis evidence, and mocks. They did not contact Nightwatch or any remote database.

## 6. Required proof summary

1. One ProductCandidate with 27 qualifying triggers produces one Research foundation sample: **PASS**.
2. Canonical scheduled production occurrence is primary eligible: **PASS**.
3. Manual/controlled/diagnostic/remediation/developer occurrences are preserved but primary-ineligible: **PASS**.
4. Frozen baseline identity is read-only and unchanged: **PASS**.
5. Expired qualifying evidence remains included: **PASS**.
6. Premarket/intraday/post-close/exact-close/weekend/holiday/early-close/DST mapping: **PASS**.
7. Canonical Aug 20 session mapping: **PASS**.
8. Aug 26 T+5 before official close remains `NOT_YET_MATURE`: **PASS**.
9. Missing Close is not zero: **PASS**.
10. T+N Close Return and Close-path maximum upside/downside: **PASS**.
11. No Daily High/Low dependency and direction remains `UNRESOLVED`: **PASS**.
12. Matching proven price basis required; uncertainty fails closed: **PASS**.
13. Existing DTE implementation reused; raw trigger count preserved without buckets: **PASS**.
14. Live paths do not import or expose Forward Outcome: **PASS**.
15. Paid Nightwatch calls: **0**.
16. Additive migration integrity and zero historical outcome backfill: **PASS**.

## 7. External contacts and write boundary

External URL contacted during the Stage 9A task:

- `https://github.com/lililinuk/options-anomaly-scanner.git` — read-only `git fetch origin main --prune` during the authorization preflight.

No Nightwatch URL/API endpoint, npm registry endpoint, remote database, deployment service, or GitHub workflow endpoint was contacted. The npm registry value was read from local configuration only; dependency installation used strict offline mode.

## 8. Bounded carried items

### Corporate-action basis proof

`PRICE_BASIS_CAPABILITY = UNCONFIRMED`

The current Nightwatch daily-OHLC evidence does not prove split/corporate-action adjustment semantics. Stage 9A truthfully represents that state and fails closed. This does not block acceptance of the Stage 9A foundation, but it blocks production outcome computation/materialization.

### Same-day post-close knowledge proof

The mapper supports same-day post-close Reference only through an explicit proof that the Close was known as-of first knowledge. The default is fail-closed. A later materializer must bind this decision to preserved bar/as-of provenance; it must not infer knowledge from the clock alone.

## 9. Final decision

```text
STAGE9A_RESULT = PASS_WITH_CARRIED_ITEMS
STAGE9A_SCOPE_COMPLETE = YES
STAGE9B_TECHNICALLY_READY = NO
STAGE9B_BLOCKER = AUTHORITATIVE_CORPORATE_ACTION_CONSISTENT_OHLC_BASIS_NOT_PROVEN
STAGE9B_AUTHORIZED = NO
STAGE9C_IMPLEMENTED = NO
```

Stage 9A is complete within its authorized boundary. The additive schema, pure methodology, origin eligibility, session/maturity logic, cohort metadata, historical-trigger retention, and live/research firewall are implemented and verified. Stage 9B must remain on hold until the price basis is proven and separately authorized.
