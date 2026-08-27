# NIGHTWATCH vNext — Stage 9B Outcome Materialization Completion Report

**Date:** 2026-08-27  
**Result:** `PASS_WITH_CARRIED_ITEMS`  
**Stage boundary:** Stage 9B only. Stage 9C Research UI is neither implemented nor authorized by this report.

```text
STAGE9A_RESULT = PASS_WITH_CARRIED_ITEMS
STAGE9A_RETEST_REQUIRED = NO
STAGE9A_COMPLETION_REPORT_SHA256 = 307FF1EB8333567704649A2955E210E07B4FAE934390BF23F025BF228F395216
STAGE9A_INTEGRATION_COMMIT = 671e252a03ee7a71f46e8b8f9ae7cb4fcd6094f5
STAGE9B_BASELINE_COMMIT = 671e252a03ee7a71f46e8b8f9ae7cb4fcd6094f5
STAGE9B_IMPLEMENTATION_COMMIT = edba29778bcdc14fdd0230587b74c54b2fcf1ce0
WORKTREE = F:\options-anomaly-scanner-stage9b
BRANCH = vnext/stage9b-outcome-materialization
STAGE9B_PRICE_BASIS_POLICY = RAW_REGULAR_CLOSE_RESEARCH_V1
OUTCOME_METHODOLOGY_VERSION = stage9b.raw-regular-close-research-v1
REFERENCE_PRICE_POLICY = PRIOR_COMPLETED_REGULAR_CLOSE
DIRECTION = UNRESOLVED
SECOND_FORWARD_OUTCOME_SCHEDULER = NO
PAID_NIGHTWATCH_CALLS = 0
STAGE9C_IMPLEMENTED = NO
STAGE9C_AUTHORIZED = NO
```

## 1. Stage 9A administrative closeout and canonical integration

The accepted Stage 9A completion report was read from both required locations:

- `F:\options-anomaly-scanner-stage9a\docs\evidence\NIGHTWATCH_VNEXT_STAGE9A_FORWARD_OUTCOME_FOUNDATION_COMPLETION_REPORT_20260827.md`
- `F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_VNEXT_STAGE9A_FORWARD_OUTCOME_FOUNDATION_COMPLETION_REPORT_20260827.md`

The files were byte-identical. Both SHA-256 values were:

`307FF1EB8333567704649A2955E210E07B4FAE934390BF23F025BF228F395216`

No Stage 9A retest was performed, as directed. The accepted Stage 9A implementation and evidence were committed on `vnext/stage9a-forward-outcome-foundation`, fast-forwarded into canonical `main`, and pushed to `origin/main` without conflict. Canonical `main` was clean and verified as:

```text
HEAD        = 671e252a03ee7a71f46e8b8f9ae7cb4fcd6094f5
origin/main = 671e252a03ee7a71f46e8b8f9ae7cb4fcd6094f5
```

That exact commit is the Stage 9B baseline. No force-push, overwrite, or unrelated integration conflict occurred.

## 2. Implementation delivered

### Raw regular-Close policy

Stage 9B implements the Founder-locked policy `RAW_REGULAR_CLOSE_RESEARCH_V1`.

- Only preserved `session=regular` daily bars normalized through `app.confirmation.domain.canonical_regular_daily` are eligible.
- Each sample and measurement says `RAW_UNADJUSTED` and records raw-payload ID, payload SHA-256, endpoint, request provenance, receipt/observation timestamps, trading date, parser policy, and deterministic selection policy.
- The code and persisted provenance explicitly exclude claims of adjusted return, total return, or corporate-action-consistent return.
- Reference and future sessions share one explicit raw-v1 basis identity.
- Raw prices are never assumed to “adjust back” over time.

### Materialization and maturity

The materializer:

- preserves one Research Sample per immutable ProductCandidate occurrence;
- binds the frozen `FIRST_KNOWLEDGE_BASELINE` and qualifying historical trigger set;
- resolves detection DTE from existing Radar, Expiry Activity, and Contract Persistence source rows using existing Scanner semantics;
- maps Reference/T+1/T+3/T+5 with XNYS sessions;
- matures each horizon independently;
- calculates only Close Return, Close-path Max Upside, and Close-path Max Downside when the complete required path exists;
- preserves missing values as NULL, never zero;
- runs rollback-only unless `--commit` is explicitly supplied;
- has no Nightwatch client, API-key, HTTP, or vendor-refresh dependency.

### Append-only/versioned integrity

Every raw-v1 measurement carries a semantic SHA-256 fingerprint and a positive calculation revision. An identical rerun reuses the existing row. A changed raw input or maturity state appends a new revision linked through `supersedes_measurement_id`; it never updates the previous revision. A later corrected/adjusted methodology must use a distinct methodology version and cannot silently replace raw-v1.

### Corporate-action handling

Migration `20260827_0019` adds an append-only known corporate-action evidence table. Recorded known price-scale-changing actions are evaluated by effective session per horizon:

- an action after Reference and through T+1 contaminates T+1/T+3/T+5;
- an action after T+1 and through T+3 leaves T+1 usable and contaminates T+3/T+5;
- a contaminated horizon is `CORPORATE_ACTION_CONTAMINATED`, retains its raw input evidence, has NULL outcome metrics, and is ineligible for primary descriptive aggregation;
- ordinary cash dividends are not modeled as total return adjustments;
- a later correction is append-only/versioned.

The production registry currently contains zero known price-scale-changing events. No complete corporate-action coverage is claimed, and no unapproved price-jump heuristic or suspect-event threshold was invented.

## 3. Files and migration

Implementation commit `edba29778bcdc14fdd0230587b74c54b2fcf1ce0` changes:

- `backend/alembic/versions/20260827_0019_stage9b_outcome_materialization.py`
- `backend/app/cli.py`
- `backend/app/research/forward_outcome.py`
- `backend/app/research/materialization.py`
- `backend/app/research/models.py`
- `backend/tests/test_stage9b_outcome_materialization.py`

This completion report is the only additional evidence file.

Database migration state advanced transactionally:

```text
before = 20260818_0017
after  = 20260827_0019
```

Migrations `20260827_0018` and `20260827_0019` were applied. The schema changes are additive. No migration inserts, updates, or backfills historical outcomes.

## 4. Production materialization result

### Research population

| Measure | Count |
|---|---:|
| Total ProductCandidate Research Samples | 7 |
| Valid frozen baselines | 7 |
| Invalid samples | 0 |
| Canonical primary-eligible (`scheduled_daily`) | 0 |
| Manual (`cli`), preserved but primary-ineligible | 7 |
| Research sample rows inserted | 7 |
| Measurement rows inserted | 21 |
| Known price-scale-changing action records | 0 |
| Contaminated horizons | 0 |

All seven ProductCandidates occurred at `2026-08-20T10:07:16.687134Z` with explicit `scan_runs.trigger = cli`. No origin was inferred from time.

### Horizon maturity

| Horizon | NOT_YET_MATURE | MATURE_AVAILABLE | MATURE_MISSING_DATA | INVALID_SAMPLE | CORPORATE_ACTION_CONTAMINATED |
|---|---:|---:|---:|---:|---:|
| T+1 | 0 | 0 | 7 | 0 | 0 |
| T+3 | 0 | 0 | 7 | 0 | 0 |
| T+5 | 0 | 0 | 7 | 0 | 0 |

All 21 horizons were mature at evaluation time. None had the complete preserved raw regular-Close path required to compute a metric. Consequently:

```text
OUTCOMES_MATERIALIZED_FROM_PRESERVED_OHLC = 0
NON_NULL_CLOSE_RETURN_MAX_UPSIDE_MAX_DOWNSIDE = 0
MISSING_WAS_ZERO_FILLED = NO
```

### Idempotence proof

The first committed run inserted 7 samples and 21 measurement revisions. The immediate second committed run reported:

```text
samples_inserted = 0
samples_reused = 7
measurements_inserted = 0
measurements_reused = 21
max_calculation_revision = 1
```

No duplicate semantic revision was created.

## 5. Per-ticker and route composition

All occurrences have route composition `RADAR + EXPIRY`; none is primary eligible.

| Ticker | Samples | Primary | Qualifying triggers | DTE counts preserved | Unresolved DTE count |
|---|---:|---:|---:|---|---:|
| AAPL | 1 | 0 | 13 | VERY_SHORT 11; SHORT 1 | 1 |
| AMZN | 1 | 0 | 10 | VERY_SHORT 6; SHORT 1; MEDIUM 1 | 2 |
| GOOGL | 1 | 0 | 9 | VERY_SHORT 8; SHORT 1 | 0 |
| META | 1 | 0 | 4 | VERY_SHORT 3; SHORT 1 | 0 |
| MSFT | 1 | 0 | 5 | VERY_SHORT 1; SHORT 1 | 3 |
| NVDA | 1 | 0 | 27 | VERY_SHORT 7; SHORT 4; MEDIUM 2 | 14 |
| TSLA | 1 | 0 | 14 | VERY_SHORT 11; SHORT 1 | 2 |

An unresolved DTE does not exclude a trigger or sample. `LONG` remains supported by the canonical Scanner bucket function but does not occur in the resolved source rows above.

## 6. Canonical scheduled-production trigger-count distribution

The required population contains no canonical scheduled-production ProductCandidate:

| Statistic | Canonical value |
|---|---:|
| N | 0 |
| min | unavailable |
| P25 | unavailable |
| median | unavailable |
| P75 | unavailable |
| P90 | unavailable |
| max | unavailable |

There is therefore no by-ticker or by-route canonical distribution to report and no defensive duplicate window in the primary population.

For context only, the seven non-primary manual occurrences have raw trigger counts `4, 5, 9, 10, 13, 14, 27`; using documented linear interpolation: N 7, min 4, P25 7, median 10, P75 13.5, P90 19.2, max 27. These values are not substituted for canonical production evidence.

### Natural-boundary recommendation

`RECOMMENDATION = DEFER_NUMERIC_TRIGGER_BUCKETS`

No numeric boundary can be naturally recommended from a canonical population with N=0 without inventing methodology or using ineligible manual evidence. Stage 9C must not hardcode buckets. After canonical scheduled-production samples exist, boundaries should be proposed from the versioned canonical empirical distribution and separately approved by the Founder.

## 7. Exact residual preserved-OHLC gap

Required session plan for every sample:

```text
Reference = 2026-08-19
T+1      = 2026-08-20
T+3      = 2026-08-24
T+5      = 2026-08-26
```

The complete Close path also requires Aug 21 and Aug 25. The exact distinct missing ticker/date set is:

| Ticker | Missing regular-Close sessions | Distinct gaps |
|---|---|---:|
| AAPL | 2026-08-19, 2026-08-20, 2026-08-21, 2026-08-24, 2026-08-25, 2026-08-26 | 6 |
| AMZN | 2026-08-19, 2026-08-20, 2026-08-21, 2026-08-24, 2026-08-25, 2026-08-26 | 6 |
| GOOGL | 2026-08-19, 2026-08-20, 2026-08-21, 2026-08-24, 2026-08-25, 2026-08-26 | 6 |
| META | 2026-08-19, 2026-08-20, 2026-08-21, 2026-08-24, 2026-08-25, 2026-08-26 | 6 |
| MSFT | 2026-08-19, 2026-08-20, 2026-08-21, 2026-08-24, 2026-08-25, 2026-08-26 | 6 |
| NVDA | 2026-08-19, 2026-08-20, 2026-08-21, 2026-08-24, 2026-08-25, 2026-08-26 | 6 |
| TSLA | 2026-08-19, 2026-08-20, 2026-08-21, 2026-08-24, 2026-08-25, 2026-08-26 | 6 |
| **Total** | **7 tickers × 6 sessions** | **42** |

Horizon applicability is exact:

| Session | Role | Affected horizons for each ticker |
|---|---|---|
| 2026-08-19 | Reference | T+1, T+3, T+5 |
| 2026-08-20 | T+1 | T+1, T+3, T+5 |
| 2026-08-21 | T+3/T+5 Close path | T+3, T+5 |
| 2026-08-24 | T+3 | T+3, T+5 |
| 2026-08-25 | T+5 Close path | T+5 |
| 2026-08-26 | T+5 | T+5 |

Six preserved OHLC payloads exist for AAPL, AMZN, GOOGL, META, NVDA, and TSLA, but they were received Aug 13–14 and do not contain any required session above. No preserved MSFT OHLC payload exists. No refetch was attempted.

## 8. Paid-call and external-contact proof

Database API audit counters were identical before and after migration/materialization:

```text
api_usage_audit rows before = 464
api_usage_audit rows after  = 464
consumed_quota rows before  = 382
consumed_quota rows after   = 382
PAID_NIGHTWATCH_CALLS       = 0
```

External targets contacted during this task:

1. `https://github.com/lililinuk/options-anomaly-scanner.git` — `git fetch origin main`, Stage 9A `git push origin main`.
2. `aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres` — read-only inventory/audit, additive Alembic migrations, and Stage 9B materialization.

No Nightwatch URL or API endpoint, npm registry, deployment service, or other external URL was contacted. `npm ci --offline` used only the local cache.

## 9. Verification

| Check | Result |
|---|---|
| Focused Stage 9A + Stage 9B tests | 40 passed |
| Complete backend suite | 453 passed |
| Repository-wide Ruff | passed |
| Python compilation | passed |
| Alembic heads | `20260827_0019 (head)` |
| Isolated PostgreSQL Stage 9B DDL compilation | passed |
| Live database migration/current version | `20260827_0019` |
| Dry-run materialization | passed; transaction rolled back |
| Committed materialization | passed |
| Immediate committed idempotence replay | 0 inserts; 28 reuses |
| Frontend ESLint | passed |
| Frontend glossary check | passed; 34 governed concepts |
| Frontend Stage 7 regression | 13 passed |
| Frontend production build | passed |
| `git diff --check` before commit | passed |

One exploratory `alembic history --indicate-current` command was initially run without loading the canonical environment and timed out against the default localhost database. It performed no write. The isolated DDL check passed, and the configured production target was subsequently migrated and directly verified at `20260827_0019`.

Automated tests used fixtures/mocks and made no live Nightwatch call.

## 10. Live/Research firewall proof

- No scanner, ranking, live API route, current-candidate route, frontend route, or workflow imports Forward Outcome.
- The only command entry is an explicit manual CLI materializer; no scheduler was added.
- No Phase 2A threshold/route file changed.
- No Phase 2B semantic file changed.
- No direction inference, Actionability, win/success rate, ranking, calibration, or Research UI was added.
- All 21 persisted measurements have `direction = UNRESOLVED`.
- Frozen baselines remain 7, ProductCandidates remain 7, historical candidate triggers remain 82, and raw vendor payloads remain 451.

## 11. Carried items and Stage 9C readiness

1. **Residual OHLC:** 42 distinct due ticker/session gaps remain. Any vendor refresh requires later explicit authorization and should fetch each distinct ticker once for shared due samples.
2. **Canonical distribution:** N=0 canonical scheduled-production candidates; numeric trigger-count boundaries remain deferred.
3. **Corporate-action coverage:** known-event quarantine is implemented, but the known-event registry is empty and completeness is not claimed. No suspect heuristic was invented.
4. **Outcome population:** zero outcome metrics are available until preserved data is added or a separately authorized due-only refresh occurs.

```text
STAGE9B_RESULT = PASS_WITH_CARRIED_ITEMS
STAGE9B_IMPLEMENTATION_COMPLETE = YES
STAGE9B_PRESERVED_DATA_MATERIALIZATION_COMPLETE = YES
STAGE9B_RESIDUAL_MISSING_OHLC_DISTINCT_TICKER_DATES = 42
STAGE9B_LATER_VENDOR_REFRESH_AUTHORIZED = NO
STAGE9C_TECHNICAL_READINESS = NOT_READY_FOR_PRIMARY_RESEARCH_DATA
STAGE9C_AUTHORIZED = NO
```

Stage 9B's implementation boundary is complete and reproducible. This report does not authorize Stage 9C.

## 12. Dual-copy integrity

Byte-identical copies are required at the Stage 9B worktree and canonical evidence paths. Their final SHA-256 is reported in the handoff alongside this report rather than self-embedded, which would invalidate the file's own digest.
