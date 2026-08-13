# Phase 2B v1.1 Implementation Report — Valid Regular-Session Price Series

Date context: 2026-08-13  
Starting Git SHA: `a38e4f331951b262243a2dbd9340b68afe641b6d`  
Specification: `signal_spec_v1.1_phase2b`

## Git

- Starting SHA: `a38e4f331951b262243a2dbd9340b68afe641b6d`.
- Implementation SHA: recorded in the completion response after this report is committed.
- The implementation is limited to Phase 2B Price Context normalization, configuration,
  presentation, tests, and documentation.
- No Phase 2A behavior, financial threshold/formula, migration, schema, or direction semantics
  changed.

## Specification and immutability

The immutable amendment is documented in
`docs/specifications/SIGNAL_SPECIFICATION_PHASE2B_V1_1.md`. The active specification identifier is
`signal_spec_v1.1_phase2b`, and the active configuration version is `2026-08-13.v1.1`.

PostgreSQL read-back proves append-only behavior for the controlled candidate:

| Version | NVDA ticker contexts | Candidate evaluations |
| --- | ---: | ---: |
| `signal_spec_v1.0_phase2b` | 1 | 1 |
| `signal_spec_v1.1_phase2b` | 1 | 1 |

The v1.0 rows were not updated or deleted. The v1.1 context reused five preserved raw payload
references and five source request-ID references. Direction remains `UNRESOLVED`.

## Canonical Session Policy

Implemented policy: `VALID_REGULAR_SESSION_OBSERVATIONS`.

- Exactly one `regular` row for a trading date is selected.
- A date with no `regular` row is excluded and recorded as missing.
- A date with multiple `regular` rows is excluded and recorded as ambiguous.
- Premarket/postmarket data is never substituted.
- Remaining valid rows are ordered by trading date; a gap does not invalidate surrounding rows.

Persisted coverage includes raw bars, distinct dates, valid observations, missing/ambiguous counts
and dates, oldest/latest valid dates, coverage state, adjustment caveat, and the effective
calculation basis.

## Price Calculations

All windows are versioned configuration, not scattered business constants.

- `return_N = latest valid close / close N valid observations back - 1`; this requires `N + 1`
  valid observations.
- SMA20/SMA50 are arithmetic means of the latest 20/50 valid closes.
- High20/Low20 are extrema over the latest 20 valid regular observations.
- `TR_t = max(high-low, abs(high-previous close), abs(low-previous close))`.
- ATR14 is the arithmetic mean of the latest 14 TR observations and requires 15 price
  observations; no Wilder smoothing is used.
- SMA distances and Price Trend use the latest valid regular close.
- Strike distance uses independently timestamped current Stock State; strike distance ATR uses
  current price together with historical ATR14.
- A missing prerequisite nulls only that feature. It does not null unrelated features.
- Price adjustment semantics remain `UNCONFIRMED` and are disclosed rather than used to suppress
  otherwise valid calculations.

## Database

- Database type validated by Alembic: PostgreSQL (`PostgresqlImpl`, transactional DDL).
- Alembic current: `20260813_0009 (head)`.
- Alembic head: `20260813_0009 (head)`.
- `python -m alembic upgrade head`: passed; no new migration was required.
- PostgreSQL read-back: passed for the appended ticker context and candidate evaluation.
- Immutable v1.0 and appended v1.1 row counts are shown above.

## Dashboard

The Phase 2B Price Context card now separates:

- Current Stock State price/session and its `as_of` timestamp;
- Latest Valid Regular Close and trading date.

It displays 1D/5D/20D return, SMA20/SMA50, distances to both SMAs, 20-session high/low, ATR14,
Price Trend, strike distance percent/ATR, coverage state, valid-session count, and compact gap
count. Missing/ambiguous dates are available in an expandable data-quality detail. The
split-adjustment caveat remains visible.

The fixed Next.js candidate-context proxy returned HTTP 200 with v1.1, `AVAILABLE_WITH_GAPS`, 133
valid sessions, one missing regular date, `UPTREND`, and `UNRESOLVED` direction. The browser did
not contact Nightwatch.

## Field Guide — zh-TW

Traditional Chinese entries now explicitly document:

- 有效正常交易時段觀測;
- 歷史缺口;
- Current Stock State versus Latest Valid Regular Close;
- valid-observation return indexing;
- SMA20/SMA50 valid-session windows;
- arithmetic-mean ATR14 and its 15-observation prerequisite;
- Price Trend's latest-regular-close reference;
- unconfirmed split-adjustment semantics.

Glossary completeness passed with 20 legacy analytical columns and 108 documented fields.

## Tests and quality gates

| Gate | Exact result |
| --- | --- |
| Backend tests | 180 passed |
| Focused Phase 2B domain/orchestration | 26 passed |
| Ruff | passed |
| Frontend ESLint | passed |
| Frontend production build | passed; 7 static/dynamic routes generated |
| Glossary completeness | passed; 20 legacy columns, 108 fields |
| Alembic upgrade/current/head | passed; `20260813_0009` |
| PostgreSQL read-back | passed |
| Browser QA | dashboard and zh-TW field guide rendered; zero console errors |
| Next.js → FastAPI → PostgreSQL proxy | HTTP 200, v1.1 result |

The pytest cache emitted one non-functional sandbox permission warning; all tests passed.

Intentional v1 test changes:

- The old assertion that any missing/duplicate regular row invalidates the entire series was
  replaced by explicit missing/ambiguous date exclusion and surrounding-observation retention.
- The deterministic price test now includes an interior missing regular date and expects
  `AVAILABLE_WITH_GAPS` while all calculable features remain populated.
- The old all-or-nothing insufficient-history assertion was replaced by feature-specific boundary
  tests at 1, 5, 14, 15, 20, 21, 49, and 50 observations.
- Added explicit N+1/off-by-one, unsorted input, gap, trend, strike-location, tolerance, missing ATR,
  and preserved-raw no-network reprocessing coverage.

All unrelated Phase 2A and Phase 2B regression assertions stayed intact.

## Controlled NVDA Validation

Candidate: `NVDA260821C00220000`.

### Raw OHLC coverage

| Item | Result |
| --- | ---: |
| Raw bars | 400 |
| Distinct trading dates | 134 |
| Premarket rows | 133 |
| Regular rows | 133 |
| Postmarket rows | 134 |
| Missing regular dates | 1 (`2026-01-30`) |
| Ambiguous regular dates | 0 |
| Canonical valid observations | 133 |
| Oldest valid regular date | `2026-02-02` |
| Latest valid regular date | `2026-08-12` |

### Price references

| Item | Result |
| --- | --- |
| Current Stock State | 223.7347 |
| Current session | `PREMARKET` |
| Stock State as-of | `2026-08-13T09:25:04.000Z` |
| Latest valid regular close | 224.09 |
| Latest valid regular date | `2026-08-12` |

### Calculated price context

| Feature | Result |
| --- | ---: |
| Return 1D | 0.0302988505747126 |
| Return 5D | 0.022215126357084225 |
| Return 20D | 0.054541176470588315 |
| SMA20 | 208.3825 |
| SMA50 | 206.2618 |
| Distance to SMA20 | 0.07537821074226492 |
| Distance to SMA50 | 0.08643481245679041 |
| Rolling high20 | 225.1 |
| Rolling low20 | 190.01 |
| ATR14 | 7.834414285714287 |
| Price Trend | `UPTREND` |
| Strike distance % | -0.016692538081933717 |
| Strike distance ATR | -0.4767044304524547 |

Quality state is `AVAILABLE_WITH_GAPS`; coverage state is `VALID_WITH_GAPS`; policy is
`VALID_REGULAR_SESSION_OBSERVATIONS`; adjustment semantics are `UNCONFIRMED`. These values are
descriptive and do not change directional interpretation.

## Nightwatch Ledger and quota

No Nightwatch endpoint was called during this amendment validation.

| Source | Calls | Network attempts | Paid units |
| --- | ---: | ---: | ---: |
| Preserved `/v1/stocks/ohlc/NVDA` raw evidence | 0 | 0 | 0 |
| All other Nightwatch capabilities | 0 | 0 | 0 |

- The controlled CLI summary was: one evaluation, zero newly fetched ticker snapshots, zero reused
  current-version snapshots, one preserved-raw reprocessed snapshot, zero paid units, and zero
  network attempts.
- Pre-validation last-known quota: 99,839 remaining of 100,000.
- Post-validation quota: unchanged at 99,839; the zero-call command itself correctly reported no
  new quota observation (`None`).
- Cache/evidence reuse: existing raw OHLC plus existing Stock State, IV Rank, Term Structure, and
  Dealer Heatmap context; no MAG7 scan and no Daily Archive run.

## Security

- `.env`, `backend/.env`, and `frontend/.env` are Git ignored.
- Exact local `DATABASE_URL` matches in tracked files: 0.
- Exact local Nightwatch API key matches in tracked files: 0.
- Frontend runtime code contains neither credential and makes no direct Nightwatch request.
- The only frontend `NIGHTWATCH_API_KEY` token is a safety-check fixture that rejects such browser
  code; it is not a value or runtime credential.
- Authorization is constructed only inside the server-side transport and is not included in raw
  evidence persistence.
- No credential or Authorization header appeared in validation output or browser console.

## Open issues

- Nightwatch OHLC split-adjustment semantics remain unconfirmed by the vendor. This is disclosed as
  `UNCONFIRMED`; it does not suppress valid calculations.
- No other blocker remains for this narrow Phase 2B v1.1 amendment.

Phase 2B v2 was not started.
