# NIGHTWATCH Trading Dashboard vNext — Implementation Report

**Implementation date:** 2026-08-30
**Status:** IMPLEMENTED_ON_ISOLATED_FEATURE_BRANCH
**Integration status:** NOT_AUTHORIZED
**Branch:** `feat/trading-dashboard-vnext`

## 1. Authority and base

```text
CANONICAL_SPEC_USED=F:\options-anomaly-scanner\docs\evidence\NIGHTWATCH_TRADING_DASHBOARD_VNEXT_AMENDMENT_CANONICAL_SPEC_20260827.md
BASE_HEAD=5daff22ae780fe0fab18994c8a50ad66a9e145de
GCP_CANONICAL_MIGRATION_PRESENT_ON_BASE=YES
ALEMBIC_20260828_0020_PRESENT=YES
LOCAL_HEAD_EQUAL_TO_FRESH_ORIGIN_MAIN_AT_PREFLIGHT=YES
WORKTREES_CREATED=0
```

Preflight ran on a clean `main`. Freshly fetched `origin/main` and local `HEAD` both resolved to `5daff22ae780fe0fab18994c8a50ad66a9e145de`. The base contained the accepted Google Cloud canonical scheduler migration, canonical slot/attempt tables, immutable slot identity, intended market-date semantics, and the three accepted `RADAR_OI`, `DEALER_GEX`, and `ACTIVITY_VNEXT` slots.

## 2. Exact files changed

Application/read-model files:

- `backend/app/api/router.py`
- `backend/app/api/routes/trading_dashboard.py`
- `backend/app/dashboard/__init__.py`
- `backend/app/dashboard/trading.py`
- `frontend/app/page.tsx`
- `frontend/app/api/trading-dashboard/proxy.ts`
- `frontend/app/api/trading-dashboard/route.ts`
- `frontend/app/trading-dashboard-semantics.ts`
- `frontend/app/trading-dashboard-types.ts`
- `frontend/app/trading-dashboard.module.css`
- `frontend/app/trading-dashboard.tsx`

Test/fixture files:

- `backend/tests/test_trading_dashboard.py`
- `backend/tests/test_trading_dashboard_contracts.py`
- `frontend/tests/mock-trading-backend.mjs`
- `frontend/tests/trading-dashboard.test.mjs`

Evidence:

- `docs/evidence/NIGHTWATCH_TRADING_DASHBOARD_VNEXT_IMPLEMENTATION_REPORT_20260830.md`

No migration, workflow, scheduler, acquisition, Stage 9, Phase2A, or GCP infrastructure file changed.

## 3. Before/after information architecture

| Before | After |
|---|---|
| Browser-date “Today’s Product Candidates” label | Explicit latest successful Candidate population market date and scan identity |
| Repeated persisted-trigger chips | Compact active anomaly count and family counts |
| Complete persisted trigger/provenance wall | Compact Why Found plus at most one Featured active anomaly per native-ranked family |
| Frozen baseline selected by default | Current Trading Context read model; Frozen baseline excluded and identified as preserved Research/Audit evidence |
| AVAILABLE used as the main health signal | Independent `CURRENT`, `STALE`, and `UNAVAILABLE` source freshness |
| Historical and expired evidence visible in the main route | Active/unexpired B4 evidence only; no expired/historical toggle |
| Historical GEX context tied to the selected evaluation | Latest eligible persisted Dealer/GEX archive, active expiries only |
| Manual scan/refresh actions inside the primary surface | Read-only persisted Trading Dashboard; no vendor action on page load |

## 4. Candidate population semantics

The new read model selects the latest `ScanRun` that is all of:

- `status == COMPLETE`;
- current accepted `SIGNAL_SPEC_VERSION`;
- `candidate_materialized_at IS NOT NULL`.

Ordering uses persisted `market_date`, `completed_at`, and `started_at` descending. A successful empty population remains an available successful result with zero Candidates. Historical rows are not relabelled as today.

No Founder-accepted Candidate-population freshness duration exists. The read model therefore reports an available population as `STALE` with `NO_ACCEPTED_CANDIDATE_FRESHNESS_RULE` instead of inventing `CURRENT`.

## 5. Active-only and Featured semantics

Trigger expiry is resolved from the accepted immutable source row for each family. Activity remains valid only through the authoritative final XNYS close for its expiry identity. Non-session expiry identities use the prior XNYS session close. Unknown-expiry evidence is excluded rather than assumed active.

Candidate Card and Why Found counts use the resulting active/unexpired evidence only. B4 receives that same active list; no expired, historical, archived, or Show Expired control exists.

Featured selection is deterministic and family-native:

- Radar: accepted `premium_usd`, then absolute `delta_oi` ordering;
- Expiry Activity: accepted native Same-Day Activity Score;
- Contract Persistence: omitted because no accepted native presentation ranking exists.

At most one item per family and three total can render. No synthetic Radar score, universal score, cross-family score, direction, or recommendation was created. The legend defines highlight as `PRIORITY_TO_INSPECT` only.

## 6. Current Trading Context vs Frozen First-Knowledge

The Dashboard consumes only the latest persisted `REFRESH` Candidate context as Current Trading Context. A Frozen `FIRST_KNOWLEDGE_BASELINE` is never used as a current fallback. If no persisted Current context exists, Price/IV/term data report `UNAVAILABLE` even when a Frozen baseline exists.

No context record is mutated. The endpoint is read-only and contains no `NightwatchClient`, write, refresh, acquisition, or materialization path. The read model reports the Frozen baseline only as `PRESERVED_OUTSIDE_TRADING_VIEW`.

Existing schema does not preserve refresh origin. The read model returns `origin=null` with `origin_state=NOT_PERSISTED`; the UI says the origin is not persisted. This keeps the boundary compatible with a later accepted `SCHEDULED_POST_CANDIDATE` or `MANUAL` origin without fabricating one now.

## 7. Global Current Trading Price Context / B1

One selected Price Context is reused for current strike relationships and GEX-relative presentation.

Selection order:

1. `stock_state.current_price_usd` only when its configured stock-state freshness rule reports `CURRENT`;
2. existing persisted valid regular-session close, labelled `Previous Close`, when available;
3. stale persisted stock-state value, labelled `Latest Vendor Price`, only when no eligible close exists;
4. otherwise `UNAVAILABLE`.

Stale stock state is never called Current Price. Vendor GEX spot is never selected as the current price. Source, as-of, session, label, fallback, and freshness are disclosed.

## 8. B2 — Volatility

The Trading view displays:

- raw IV Rank with source-specific freshness and `UNVERIFIED` vendor semantics;
- no LOW/MID/HIGH classification;
- no Candidate scoring or qualification use;
- active-expiry term nodes only;
- compact term topology;
- IV values as natural percentages (for example `0.331` renders as `33.1%`).

Expired term nodes are filtered from the current view.

## 9. B3 — Dealer / GEX

B3 queries the latest eligible persisted analytical Dealer/GEX archive at or before read time. It does not read Frozen GEX as current.

The block:

- reports archive as-of/captured-at and configured freshness;
- treats `AVAILABLE` independently from `CURRENT`;
- filters expired expiries using XNYS expiry-session semantics;
- uses the global selected Price Context for accepted price-relative GEX node rules;
- preserves vendor snapshot spot only as `HISTORICAL_SOURCE_METADATA`;
- labels values `Net GEX`;
- renders approximate signed integer USD millions such as `+$32M` and `-$8M`;
- retains decimal strike precision such as `212.5`;
- states that GEX sign is not equivalent to bullish/bearish direction.

Exact raw archive values remain immutable in persistence.

## 10. B4 — Active anomaly details

B4 supports any combination of active Radar, Expiry Activity, and Contract Persistence families, plus optional Featured-only filtering. It contains no historical/expired toggle.

Contract presentation prioritizes identity, expiry, Current DTE, right, strike, delta OI, premium, IV, delta, bid/ask, spread, quote time, and the shared Price Context label/freshness where available.

`Detection DTE` and `Detection bucket` remain immutable source evidence. `Current DTE` is computed for presentation and is never written back to source rows.

## 11. Freshness semantics and gaps

Configured existing Phase2B freshness rules are used for stock state, persisted regular-session OHLC context, IV Rank, term structure, and Dealer/GEX. No new duration or threshold was created.

```text
AVAILABLE_EQUALS_CURRENT=NO
CURRENT_STALE_UNAVAILABLE_DISTINGUISHED=YES
CANDIDATE_POPULATION_FRESHNESS_GAP=NO_ACCEPTED_RULE_SO_AVAILABLE_POPULATION_IS_STALE
CURRENT_PRICE_FRESHNESS_GAP=NONE_WHEN_ACCEPTED_SOURCE_TIMESTAMP_EXISTS
QUOTE_FRESHNESS_GAP=NO_ACCEPTED_QUOTE_RULE_SO_PERSISTED_QUOTES_ARE_NOT_CLAIMED_CURRENT
```

## 12. Roadmap dependency status

```text
DAILY_OHLC_IMPLEMENTED_IN_THIS_PACKAGE=NO
DAILY_OHLC_DEPENDENCY_PENDING=YES
IV_RANK_PROVENANCE_IMPLEMENTED_IN_THIS_PACKAGE=NO
IV_RANK_PROVENANCE_PENDING=YES
IV_RANK_CLASSIFICATION_CREATED=NO
AUTOMATIC_CONTEXT_CAPTURE_IMPLEMENTED=NO
AUTOMATIC_CONTEXT_CAPTURE_PENDING=YES
```

No Daily OHLC archive or acquisition path was created. The only price fallback is the already persisted valid regular-session close context where it exists. Automatic post-Candidate stock-state, OHLC, IV Rank, term-structure, or other vendor acquisition remains outside this package.

## 13. Phase2A, Stage 9, and GCP compatibility

```text
PHASE2A_BOUNDED_SEMANTICS_CHANGED=NO
COMPLETE_BOUNDED_SNAPSHOT_RENAMED_OR_REINTERPRETED=NO
STAGE9A_CHANGED=NO
STAGE9B_CHANGED=NO
STAGE9_RESEARCH_ELIGIBILITY_CHANGED=NO
FORWARD_OUTCOME_CHANGED=NO
GCP_CANONICAL_PRODUCTION_CONTRACTS_CHANGED=NO
INFRA_GCP_FILES_CHANGED=0
CANONICAL_SCHEDULER_FILES_CHANGED=0
WORKFLOW_FILES_CHANGED=0
```

The new read model is a consumer only. It does not modify Phase2A collection/counters/full-vs-bounded semantics, Stage 9 Research Sample or Forward Outcome semantics, GCP scheduler tables/slots/provenance, canonical readiness, transport, retry, Secret Manager, or Cloud Run behavior.

## 14. Test and verification results

```text
BACKEND_DASHBOARD_FOCUSED=12 PASSED
BACKEND_DASHBOARD_API_STAGE5_STAGE6_FOCUSED=67 PASSED
STAGE9A_STAGE9B_REGRESSION=40 PASSED
PHASE2A_AND_VENDOR_BOUNDED_REGRESSION=62 PASSED
GCP_CANONICAL_SCHEDULER_REGRESSION=12 PASSED
FULL_BACKEND_SUITE=484 PASSED
FRONTEND_TRADING_STAGE7_PROXY_REGRESSION=19 PASSED
FRONTEND_GLOSSARY=PASSED (34 GOVERNED CONCEPTS)
FRONTEND_ESLINT=PASSED
NEXTJS_PRODUCTION_BUILD=PASSED
RUFF_CHECK=PASSED
RUFF_FORMAT_CHECK=PASSED
```

The Next.js build completed the homepage and `/api/trading-dashboard` route with TypeScript passing.

## 15. Visual verification

Fixture-only local data covers:

- NVDA-like high count (8 active anomalies across all three families);
- low count (one active Radar anomaly);
- multiple families;
- CURRENT Price with unavailable IV/GEX;
- STALE bounded context;
- fully UNAVAILABLE context;
- zero-active-anomaly card;
- positive and negative GEX with decimal strikes.

The local fixture backend and Next.js route both returned HTTP 200, HMR compiled without runtime errors, and the first meaningful preview was handed to the Codex browser panel.

Automated DOM inspection/screenshot capture could not complete because the installed in-app browser runtime repeatedly failed before connection with the host sandbox `setup refresh` error. The application itself continued to compile and serve successfully.

```text
VISUAL_VERIFICATION=FIXTURE_ROUTE_HTTP_200_AND_FIRST_PREVIEW_HANDOFF; AUTOMATED_BROWSER_CAPTURE_BLOCKED_BY_HOST_SANDBOX
SCREENSHOT_PATHS=NONE
```

## 16. Safety, cost, migrations, and contacts

```text
MIGRATION_CREATED=NO
NIGHTWATCH_REQUESTS=0
PAID_UNITS=0
MANUAL_WORKFLOW_RUNS=0
MANUAL_GCP_SCHEDULER_DISPATCHES=0
REMOTE_DB_WRITES=0
REMOTE_SCHEMA_WRITES=0
CANONICAL_SLOTS_CREATED=0
```

External URLs/endpoints contacted:

- `https://github.com/lililinuk/options-anomaly-scanner.git` — authorized Git fetch; later feature-branch push uses the same remote.

Local-only URLs/endpoints contacted:

- `http://127.0.0.1:8001/api/v1/dashboard/trading` — fixture-only mock backend;
- `http://127.0.0.1:3007/` — local Next.js preview;
- `http://127.0.0.1:3007/api/trading-dashboard` — local Next.js read-only proxy.

No Nightwatch endpoint, production API endpoint, GitHub Actions dispatch endpoint, GCP Scheduler dispatch endpoint, remote database write endpoint, or schema write endpoint was contacted.

## 17. Git and residual limitations

At report creation the repository was on `feat/trading-dashboard-vnext` with only the expected implementation/test/report changes present. Final commit, clean-tree, re-fetch, `origin/main` movement comparison, and feature-branch push state are recorded in the final implementation response.

Residual limitations:

1. Candidate population remains `STALE` until a Founder-accepted freshness rule exists.
2. Daily OHLC Archive Amendment remains pending; the Dashboard creates no archive.
3. IV Rank provenance remains unaccepted; raw value only, when truthful.
4. Automatic Candidate Context Capture and refresh-origin persistence remain pending.
5. When no persisted `REFRESH` context exists, current Price/IV/term data correctly remain `UNAVAILABLE`; the Frozen baseline is not substituted.
6. Automated screenshot paths are unavailable because of the host browser sandbox failure; Founder visual review can use the compiled fixture-backed local view.
7. Natural GCP production proof remains a separate acceptance gate.

```text
MERGED_TO_MAIN=NO
PUSHED_TO_ORIGIN_MAIN=NO
PRS_CREATED=0
DEPLOYED_TO_PRODUCTION=NO
NATURAL_GCP_PRODUCTION_PROOF_ACCEPTED=NO
INTEGRATION_GATE_OPEN=NO
```
