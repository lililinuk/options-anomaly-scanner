# Phase 2B v1 Implementation Report

Date: 2026-08-13

Starting SHA: `77c40466569f90b4f51be9af77fef8a5eb2e6ee5`

Specification: `signal_spec_v1.0_phase2b`

## Scope

Implemented an append-only Deep Dive Confirmation Context around selected Phase 2A candidates:

- canonical daily-price preflight and deterministic local price calculations;
- separately timestamped current Stock State and contract strike location;
- raw vendor IV Rank;
- exact-expiry Term Structure mapping and nearest shorter/longer nodes;
- multi-expiry Dealer Heatmap quality, exact cell, strike row, and vendor-ranked rows;
- persisted Phase 2A positioning, liquidity, Greeks, archive, and config evidence reuse;
- shared per-ticker snapshot orchestration, immutable candidate evaluations, backend candidate API,
  same-origin Next.js proxy, dashboard context workspace, and zh-TW field guide.

No universal confirmation/conviction/tradeability/directional score was created. Phase 2A
discovery, scoring, Radar thresholds, Persistent formulas, Expiry Activity, archive behavior,
and four-section ordering were not changed. Direction is always `UNRESOLVED`.

Deferred: IV-vs-RV classification, risk-reversal interpretation, Event Risk, Standard GEX
candidate structure, and 0DTE Dealer GEX.

## Configuration and persistence

Phase 2B freshness and at-spot tolerance are server-side runtime settings under config version
`2026-08-13.v1`. Every ticker snapshot and evaluation persists its specification, config
version/hash, effective config, independent source timestamps, quality states, and raw references.
Refreshing appends a snapshot and does not reinterpret an earlier evaluation.

Migration `20260813_0009` created:

- `phase2b_ticker_context_snapshots`
- `phase2b_candidate_evaluations`

PostgreSQL migration/current/head validation:

- implementation: PostgreSQL (`PostgresqlImpl`), transactional DDL;
- current: `20260813_0009 (head)`;
- head: `20260813_0009 (head)`;
- both tables confirmed through PostgreSQL inspection;
- controlled read-back: one NVDA ticker snapshot and one candidate evaluation.

## Acquisition economy and failure isolation

`Phase2bContextService` accepts selected contract symbols only. No selected/persisted Deep Dive
candidate means zero requests. Candidate tickers are deduplicated, one snapshot is shared across
all contracts for a ticker, and a config-matching fresh snapshot is reused. Each of the five
endpoint failures is isolated and recorded; the Phase 2A candidate remains available. No chain
endpoint is used.

Manual developer command:

```text
python -m app.cli refresh-phase2b-context --contract NVDA260821C00220000
```

## Daily-session preflight

The controlled `1d` response contained 400 bars across 134 trading dates:

- postmarket: 134 rows;
- premarket: 133 rows;
- regular: 133 rows;
- one trading date had no regular row;
- one date therefore failed the exactly-one-regular-row invariant; no duplicate regular row was
  selected.

Result: `DAILY_SESSION_POLICY_UNRESOLVED`. Raw OHLC was preserved, but all multi-session returns,
SMAs, rolling high/low, ATR14, distance-to-SMA, and strike-distance-ATR are null. No premarket,
postmarket, last-row, or maximum-volume fallback was invented. Stock State and numeric strike
distance remain available. `price_adjustment_semantics=UNCONFIRMED` is persisted/displayed.

## Controlled NVDA validation

### Candidate and Phase 2A reuse

- contract: `NVDA260821C00220000`;
- expiration / DTE / right / strike: 2026-08-21 / 9 / C / 220;
- trigger: `RADAR_EVENT`;
- Radar premium: USD 10,434,044;
- OI Diff: +4,531; relative change 0.07211294;
- volume / trades: 24,458 / 2,887;
- Contract Positioning Structure score: 70.722;
- archive: `COMPLETE`;
- Radar threshold profile: `2026-08-13.v1` with immutable config hash;
- contract and expiry persistence: unavailable for this candidate;
- clusters: none for this candidate expiry.

### Price

- Stock State: 223.7347, previous close 224.09, premarket;
- Stock State as-of: 2026-08-13T09:25:04.000Z;
- session change: -0.0015855236735240474;
- price-history state: `PARTIAL`, `DAILY_SESSION_POLICY_UNRESOLVED`;
- 1D/5D/20D returns, SMA20/SMA50, trend, rolling high/low, ATR14: null;
- strike distance: -3.7347 USD / -0.016692538081933717;
- strike location: `BELOW_SPOT`;
- strike distance ATR: null;
- price adjustment: `UNCONFIRMED`.

The historical chain spot 218.94 was retained separately and was not overwritten.

### Volatility

- archived contract IV: 0.2973;
- ticker IV Rank: 32.4659, vendor date 2026-08-12,
  as-of 2026-08-12T18:35:19.966Z;
- candidate term node: exact match, DTE 9, IV 0.3310389567749655,
  implied move USD 7.85191163037332 / 3.52815461793696%;
- shorter node: 2026-08-19, DTE 7, IV 0.3193913570189355;
- longer node: 2026-08-24, DTE 12, IV 0.3116061174389525;
- candidate-minus-shorter: 0.01164759975602997;
- candidate-minus-longer: 0.019432839336012975;
- contract-minus-expiry-node: -0.03373895677496547;
- no curve, IV/RV, skew, cheap/rich, or direction classification.

### Dealer/GEX

- quality: `AVAILABLE_DEGRADED`; vendor state `degraded`;
- generated: 2026-08-13T09:41:13.889185441Z;
- session date ET: 2026-08-13; market status closed; Heatmap spot 223.8;
- truncation: false; 771 cells and 101 row stacks returned;
- exact `expiration=2026-08-21 AND strike=220` cell: **YES**;
- cell net/call/put dealer GEX USD: 59,652,544 / 59,166,863 / 485,681;
- strike 220 row net/absolute GEX USD: 81,553,764 / 121,659,202; vendor rank 1;
- vendor top five strikes: 220, 225, 235, 230, 227.5;
- nearest returned positive/negative net rows to stock-state price: 222.5 / 217.5;
- no missing cell was converted to zero, no complete-surface concentration was calculated, and
  no support/resistance/wall/flip or GEX score was invented.

### Execution and direction

- bid / ask / midpoint: 3.85 / 3.95 / 3.90;
- spread: USD 0.10 / 2.564102564102566%;
- OI: 62,832;
- delta / gamma: 0.4787 / 0.0369;
- theta / vega / charm: -0.2247 / 14.4368 / -1.0396;
- quote and Greeks as-of: 2026-08-11T20:00:00.657Z;
- `DIRECTION=UNRESOLVED`.

## Exact Nightwatch ledger

Controlled validation contacted only `https://api.yehangshe.com` through the server-side client.

| Endpoint | Ticker | Safe parameters | HTTP | Attempts | Retries | Paid units | Remaining | Request ID |
|---|---|---|---:|---:|---:|---:|---:|---|
| `/v1/stocks/ohlc/NVDA` | NVDA | `candle_size=1d` | 200 | 1 | 0 | 1 | 99,843 | `req_ef825487d45fb12c7df2dd7c` |
| `/v1/stocks/stock-state/NVDA` | NVDA | none | 200 | 1 | 0 | 1 | 99,842 | `req_d0d98afef7eeb5880413b94d` |
| `/v1/volatility/iv-rank/NVDA` | NVDA | none | 200 | 1 | 0 | 1 | 99,841 | `req_d360f2594de2d87f8ba6f859` |
| `/v1/volatility/term-structure/NVDA` | NVDA | none | 200 | 1 | 0 | 1 | 99,840 | `req_3bb22a1aa33fc405a9efa1fc` |
| `/v1/derived/heatmap/NVDA/snapshot` | NVDA | `format=full` | 200 | 1 | 0 | 1 | 99,839 | `req_8c473dbd1205d3ae68fc7d55` |

Actual provider quota immediately before/after the fresh set: 99,844 / 99,839. Paid units: 5.
Network attempts: 5. Retries: 0. Cache reuse: none because no prior Phase 2B snapshot existed.
The older pre-run database audit value was 99,854 because the preceding diagnostic probes were
not production-persisted; the first controlled response establishes the actual 99,844 baseline.

No RV, stats, skew, Standard GEX, 0DTE Dealer GEX, earnings, chain snapshot, MAG7 scan, or Daily
Archive call occurred.

## API, dashboard, and field guide

- FastAPI read-only route: `/api/v1/scans/candidates/{contract}/confirmation`.
- Same-origin browser proxy: `/api/candidate-context?contract=...`, with a strict contract-symbol
  allowlist and a fixed backend route. It cannot trigger arbitrary Nightwatch calls.
- The browser displays Candidate Summary, Why Found, Price, Volatility, Dealer/GEX, Positioning,
  Liquidity/Greeks, and per-source Data Age without a composite score.
- Browser QA confirmed the persisted candidate detail, `Direction: UNRESOLVED`, premarket label,
  unavailable price-history state, split caveat, degraded Heatmap warning, exact cell, distinct
  row-stack, timestamps, and no console errors/warnings.
- Frontend source contains no Nightwatch URL/client/API key. Browser communication remains with
  same-origin Next.js routes only.
- The Traditional Chinese field guide documents Price Trend, ATR, Strike Distance ATR, IV Rank,
  Term Structure, Implied Move, Dealer Heatmap, Candidate GEX Cell, Row Stack, Degraded, and
  Direction Unresolved.

## Quality gates

- Backend: 171 tests passed.
- Ruff: passed.
- Alembic current/head: `20260813_0009` / `20260813_0009`.
- PostgreSQL read-back: passed.
- Frontend ESLint: passed.
- Frontend production build: passed; candidate-context route included.
- Glossary completeness: passed; 20 legacy columns and 102 documented fields.
- Browser QA: passed; no console errors/warnings.
- Phase 2A regression: accepted Phase 2A test suite passed unchanged.
- Secret safety: `.env` remains ignored; no API key, Authorization header, database credential,
  or browser secret was persisted or exposed.

## Open issues

1. The actual daily OHLC history is missing one regular-session row. Until vendor/session semantics
   change or an accepted policy is specified, multi-session price technicals remain unavailable.
2. OHLC split-adjustment semantics remain unconfirmed.
3. Dealer Heatmap is usable but vendor-marked `degraded`; sparse missing cells remain unknown.
4. IV-vs-RV, skew, authoritative Event Risk, Standard GEX, and 0DTE Dealer GEX remain explicitly
   deferred to later accepted specifications.
