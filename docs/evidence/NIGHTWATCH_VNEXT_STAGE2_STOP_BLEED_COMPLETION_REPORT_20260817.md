# Nightwatch Scanner vNext —Stage 2 Completion Report

## A. EXECUTIVE RESULT

```text
STAGE2_RESULT = PASS_WITH_CARRIED_ITEMS
```

G1 and G2 are implemented and verified. No Stage 3+ work was performed.

## B. PREFLIGHT

- Repository: `F:\options-anomaly-scanner`
- Branch: `fix/oi-change-rollover-workflow-context`
- HEAD before/after: `8a2573f406d1011bc06970a34cf26e506bf29e97`
- Pre-existing dirty state: `frontend/next-env.d.ts` plus six untracked documentation files.
- All G1/G2 files were clean and matched Stage 1 evidence.
- Next.js temporarily regenerated `next-env.d.ts` during build; its exact preflight content was restored.

Stage 2 files touched:

- `backend/app/api/routes/scans.py`
- `backend/app/scanner/daily.py`
- `backend/tests/test_api.py`
- `backend/tests/test_v13_routes.py`
- `frontend/app/api/mag7-scan/route.ts`
- `frontend/app/api/mag7-scan/proxy.ts`
- `frontend/app/scan-dashboard.tsx`
- `frontend/tests/mag7-scan-proxy.test.mjs`

## C. G1 IMPLEMENTATION

Prior defect: a backend/network failure in the MAG7 GET proxy returned HTTP 200 with `scan:null` and empty results.

After the change:

- Backend exposes an explicit `run_state`.
- Proxy preserves backend non-2xx statuses and error metadata.
- Network failure returns HTTP 503 with generic `FAILED`.
- The dashboard checks `response.ok` and does not treat failure as successful emptiness.
- Empty-table messaging distinguishes failure, running, and not-run states.

Currently distinguishable:

```text
NOT_RUN
RUNNING
FAILED
SUCCESS_NO_CANDIDATE
SUCCESS_WITH_CANDIDATES
```

`DB_OFFLINE` is not fabricated from generic 5xx responses. Exact DB classification remains deferred until the backend provides sufficient evidence. Final Stage 7 layout/freshness presentation was not implemented.

## D. G1 TEST EVIDENCE

- Frontend proxy tests: 5 passed.
  - Backend 500 remains non-success.
  - Transport failure becomes generic `FAILED`, not invented `DB_OFFLINE`.
  - Successful empty, populated, and not-run responses remain distinct.
- Backend API/run-state tests passed.
- Frontend lint: passed.
- Frontend production build and TypeScript validation: passed.

## E. G2 IMPLEMENTATION

Prior mutation: `_backfill_existing_observations` reassigned existing Radar rows—`captured_at` and `ny_market_date`.

Those assignments were removed. Re-evaluation can still populate the existing analytical fields, but original capture identity remains unchanged.

New Radar evidence still persists through the existing constructor and unique identity:

```text
(ticker, contract_symbol, observation_date)
```

Idempotence remains enforced by COMPLETE coverage checks, identity lookup, and the existing unique constraint. No legacy repair or mass update was added.

## F. G2 TEST EVIDENCE

Fixture-only tests prove:

- Re-evaluation preserves known `captured_at = T0`.
- Re-evaluation preserves known `ny_market_date = D0`.
- Analytical eligibility can still be populated.
- Genuinely new evidence creates one Radar observation and one coverage row.
- Repeated processing creates no duplicate observation or coverage row.

Verification results:

- Focused backend tests: 32 passed.
- Complete backend suite: 298 passed.
- Ruff on touched backend files, cache disabled: passed.

## G. OUT-OF-SCOPE FINDINGS

Intentionally deferred:

- Full seven-time-identity model and additive evaluation versioning: Stage 3.
- Exact scan-path `DB_OFFLINE` classification.
- Candidate-first dashboard redesign and final availability presentation: Stage 7.
- All other Stage 1 carried items remain unchanged.

The pytest cache emitted a non-failing permission warning; test execution itself passed.

## H. DIFF SUMMARY

```text
files changed: 8
lines added: 320
lines removed: 23
migration files: 0
workflow files: 0
```

Pre-existing dirty files and untracked documents remain preserved.

## I. AUTHORIZATION COMPLIANCE

```text
NIGHTWATCH_REQUESTS=0
PAID_UNITS=0
REMOTE_DB_WRITES=0
MIGRATIONS_CREATED=0
WORKFLOWS_DISPATCHED=0
```

External URLs/API endpoints contacted: none. `http://backend.invalid` appears only as an inert test value passed to mocked fetch functions; no network request occurred.

No commit, push, PR, scan, refresh, archive, or workflow dispatch was performed.

## J. SPEC IMPACT

```text
REOPEN_PHASE2A_VNEXT=NO
REOPEN_PHASE2B_MODEL_B=NO
SPEC_AMENDMENT_REQUIRED=NO
STAGE_ORDER_CHANGE_REQUIRED=NO
```

## K. NEXT ACTION

```text
NEXT_AUTHORIZED_STAGE = NONE
```

> Stage 3 may be recommended after founder review, but is NOT authorized by this Stage 2 package.

