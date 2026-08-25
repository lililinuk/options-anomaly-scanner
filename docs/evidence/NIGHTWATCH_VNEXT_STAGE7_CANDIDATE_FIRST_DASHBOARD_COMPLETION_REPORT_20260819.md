# Nightwatch vNext Stage 7 — Candidate-First Dashboard Completion Report

**Execution completed:** 2026-08-20

**Stage package date:** 2026-08-19

**Scope:** Stage 7 only

## Outcome

Stage 7 is complete with the two pre-existing carried items preserved. The dashboard now presents truthful system/data health first, then every persisted ProductCandidate for the current scan, followed by candidate-first research context and finally supporting raw/audit evidence. The frontend does not rank, truncate, or recompute ProductCandidate eligibility.

One local acceptance commit was created for the already accepted Stage 6 predecessor. Stage 7 remains uncommitted on its dedicated branch/worktree. No push, pull request, merge, migration, remote database action, workflow dispatch, live Nightwatch request, or paid vendor call occurred.

## Acceptance evidence

- Persisted candidate projection: all seven deterministic MAG7 ProductCandidates render; the inherited Deep Dive selection remains four; no valid candidate is omitted.
- Context identity: `FIRST_KNOWLEDGE_BASELINE` remains the default frozen view and `REFRESH` evaluations are separately selectable.
- Shared/evidence boundaries: B1/B2/B3 render once per selected candidate; B4 renders once per trigger and keeps contract and expiry entities distinct.
- Safety boundaries: no ticker/conviction/composite/execution score, BUY/SELL, direction, active Evidence Breadth, unverified IV Rank classification, stabilization/downside label, or Phase 2B Gamma/Theta/Vega claim is introduced.
- Operations: scan and context-refresh costs/scopes are disclosed before action; context refresh is explicit and never runs on initial render.
- Transport: candidate-context and system-status same-origin proxies preserve backend non-2xx responses, map invalid backend JSON to 502, and map transport failure to 503.
- Time: timestamps use fixed `America/New_York` primary rendering with labeled UTC detail; date-only values remain date-only.
- 0DTE: provisional, canonical, and legacy/ambiguous identities remain distinct, with maturity/count and fallback consequence visible.

## Verification

| Gate | Result |
|---|---:|
| Stage 7 backend/API | 15/15 PASS |
| Stage 7 frontend | 13/13 PASS |
| Glossary semantics | 34 concepts PASS |
| Stage 6 regressions | 27/27 PASS |
| Stage 5 regressions | 14/14 PASS |
| Stage 4 regressions | 24/24 PASS |
| Stage 3/time regressions | 13/13 PASS |
| Full backend | 379/379 PASS |
| Ruff (`--no-cache`) | PASS |
| TypeScript (`tsc --noEmit`) | PASS |
| Frontend lint | PASS |
| Frontend production build | PASS |
| Alembic heads | `20260818_0017` (single head) |
| `git diff --check` | PASS |

Local loopback route verification used a deterministic fixture backend and confirmed HTTP 200 for the dashboard, current scan, system status, candidate-context history, and explicit candidate refresh. It returned seven candidates and distinct baseline/refresh evaluations for the mixed-trigger NVDA fixture. The in-app browser connector could not start because its bundled `browser-service.mjs` dependency was rejected by the connector's trusted-code-path policy; no alternate browser control surface was used. Automated layout/semantics, proxy, lint, type, and production-build gates remain complete.

## Carried items

```text
CURRENT_TRIGGER_FRESHNESS_MODE=CALIBRATION_REQUIRED
RADAR_OI_SCHEDULE_ACTIVATION=PENDING_ROLLOVER_EVIDENCE
```

## Required closeout matrix

```text
STAGE7_RESULT=PASS_WITH_CARRIED_ITEMS

STAGE6_ACCEPTED_COMMIT=d6cb38f5399dd3e30e8855f667ee16ef93a373e0
STAGE7_BRANCH=vnext/stage7-candidate-first-dashboard
STAGE7_WORKTREE=F:\options-anomaly-scanner-stage7
STAGE7_BASE_HEAD=d6cb38f5399dd3e30e8855f667ee16ef93a373e0
ALEMBIC_HEAD_BEFORE=20260818_0017

CANDIDATE_FIRST_LAYOUT=YES
HEALTH_FIRST=YES
PRODUCT_CANDIDATES_BEFORE_RAW_ENGINE_TABLES=YES

QUALIFYING_TICKERS=7
RENDERED_PRODUCT_CANDIDATES=7
DEEP_DIVE_SELECTED_TICKERS=4
OMITTED_VALID_PRODUCT_CANDIDATES=0

DB_OFFLINE_DISTINCT=YES
NOT_RUN_DISTINCT=YES
RUNNING_DISTINCT=YES
FAILED_DISTINCT=YES
SUCCESS_NO_CANDIDATE_DISTINCT=YES
SUCCESS_WITH_CANDIDATES_DISTINCT=YES
BACKEND_FAILURE_MASKED_AS_EMPTY_SUCCESS=NO

BASELINE_REFRESH_DISTINCT=YES
BASELINE_DEFAULT_PRESERVED=YES
SHARED_B1_B2_B3_RENDERED_ONCE=YES
ANOMALY_DETAILS_PER_TRIGGER=YES
EXPIRY_ONLY_DEAD_END_FOUND=NO
EXPIRY_TRIGGER_FABRICATES_CONTRACT=NO

FIXED_NY_TIME_RENDERING=YES
UTC_DETAIL_AVAILABLE=YES
TIMESTAMP_IDENTITIES_LABELED=YES
BROWSER_LOCAL_UNLABELED_TIME_FOUND=NO

TICKER_SCORE_PRESENT=NO
CONVICTION_SCORE_PRESENT=NO
PHASE2B_COMPOSITE_SCORE_PRESENT=NO
BUY_SELL_PRESENT=NO
DIRECTIONAL_INFERENCE_PRESENT=NO
EVIDENCE_BREADTH_ACTIVE=NO

IV_RANK_CLASSIFICATION_PRESENT=NO
IV_RANK_PROVENANCE_WARNING_PRESENT=YES
STABILIZATION_BIAS_PRESENT=NO
DOWNSIDE_ACCELERATION_RISK_PRESENT=NO
GAMMA_PHASE2B_CORE_PRESENT=NO
THETA_PHASE2B_CORE_PRESENT=NO
VEGA_PHASE2B_CORE_PRESENT=NO
EXECUTION_SCORE_PRESENT=NO

INVALID_CLUSTER_POSITIVE_LEAK=NO
SUBTHRESHOLD_STRUCTURE_POSITIVE_LEAK=NO
DEEP_DIVE_PRESENTED_AS_CANDIDATE_QUALIFICATION=NO

ZERO_DTE_STATUS_VISIBLE=YES
PROVISIONAL_CANONICAL_LEGACY_DISTINCT=YES
ZERO_DTE_HISTORY_MATURITY_VISIBLE=YES
ZERO_DTE_FALLBACK_CONSEQUENCE_VISIBLE=YES

RUN_SCAN_COST_DISCLOSED=YES
RUN_SCAN_REFRESH_SCOPE_DISCLOSED=YES
CONTEXT_REFRESH_UI_ENTRYPOINT=YES
CONTEXT_REFRESH_COST_DISCLOSED=YES
BASELINE_IMMUTABILITY_DISCLOSED=YES
AUTO_CONTEXT_REFRESH_ON_RENDER=NO

GET_READ_ONLY=YES
NON2XX_PRESERVED=YES
ARBITRARY_VENDOR_PROXY_EXPOSED=NO
BROWSER_SECRET_EXPOSED=NO

GLOSSARY_UPDATED_FOR_VNEXT=YES
GLOSSARY_SEMANTIC_TESTS=YES
LEGACY_TERMS_LABELED=YES

MIGRATION_CREATED=NO
ALEMBIC_HEAD=20260818_0017
BACKEND_ANALYTICS_CHANGED=NO
STAGE6_CONTEXT_SEMANTICS_CHANGED=NO

NIGHTWATCH_REQUESTS=0
PAID_UNITS=0
REMOTE_DB_WRITES=0
REMOTE_MIGRATIONS_RUN=0
WORKFLOWS_DISPATCHED=0
STAGE6_ACCEPTED_COMMITS_CREATED=1
STAGE7_IMPLEMENTATION_COMMITS_CREATED=0
PUSHES=0
PRS_CREATED=0
MERGES=0
EXTERNAL_URLS_OR_API_ENDPOINTS_CONTACTED=[]

STAGE8_READY=YES
NEXT_AUTHORIZED_STAGE=NONE
```

Stage 8 was not started.
