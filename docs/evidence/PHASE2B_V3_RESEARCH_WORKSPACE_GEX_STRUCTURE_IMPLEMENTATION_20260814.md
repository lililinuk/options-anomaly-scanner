# Phase 2B v3 Candidate Research Workspace and GEX Structure — Implementation Report

Date: 2026-08-14
Production specification: `signal_spec_v3.0_phase2b`

## Git

- Starting SHA: `616de8bd4c8a1f758d913fd1ed36e7df48c2ee70`.
- Accepted Phase 2B v2 anchor `eb2b2be87e56effb85537e1e6f1a55785dc043eb` was verified as an ancestor.
- Commit message: `feat: add phase2b v3 research workspace and gex structure`.
- Final commit SHA: reported in the completion handoff. A commit cannot embed its own final SHA in
  a tracked file without changing that SHA.
- No history was rewritten. The completion handoff confirms the final clean-tree state.

## Specification

`docs/specifications/SIGNAL_SPECIFICATION_PHASE2B_V3.md` defines the immutable
`signal_spec_v3.0_phase2b`. V1.x evaluations and `signal_spec_v2.0_phase2b` rows are preserved and
continue to appear in the additive API response.

Explicit rule versions:

- `dealer_gex_primary_floor_v1`
- `dealer_gex_primary_upper_node_v1`
- `dealer_gex_below_floor_path_v1`
- `dealer_gex_adjacent_expiry_context_v1`

The implementation does not create PRICE_DIRECTIONAL_BIAS, a four-thesis model, a GEX score, a
trade score, BUY/SELL, Long Call/Put, Short Call/Put, or Phase 2B v4 behavior.

## Three Evidence Roles

### Opportunity / Positioning

Exact-contract Radar Event, aggregate Contract Premium Activity, Volume, Trades, current OI, ΔOI,
relative OI change, structure, persistence, cluster, and Evidence Breadth are grouped together.
They answer why the contract was surfaced and remain non-directional.

### Underlying Directional Context

The workspace reuses the accepted factual `UPTREND`/`DOWNTREND`/`MIXED`/`UNKNOWN` Price Trend with
latest valid regular close, SMA20, SMA50, 1D/5D/20D returns, ATR, and data quality. The expandable
audit exposes the accepted source comparisons. No top-level Model Bullish/Bearish state is added.

### Trade-Structure / Path Context

Factual volatility, anchor-expiry Dealer/GEX structure, and execution are shown separately. They
describe environment, conditional path, and practical execution—not an underlying direction or
trade recommendation.

## UI Changes

The exact contract is the primary heading. The validated NVDA layout begins:

```text
NVDA 2026-08-21 $220 Call
DTE at Detection: 9 · Bucket: SHORT

ROLE 1  WHY FOUND / POSITIONING
ROLE 2  UNDERLYING PRICE
ROLE 3  TRADE-STRUCTURE / PATH CONTEXT
```

Price Trend, Observed Flow, and Dealer/GEX derived states have expandable audit views. Expiry-only
rows open a contract workspace only when `entity_type=CONTRACT`; no exact-contract fields are
fabricated for `EXPIRY_ONLY`.

## Contract Activity Semantics

- `Premium Activity` is vendor-reported aggregate exact-contract Radar activity. It may represent
  many trades; it is not labeled as one order, a whale order, bullish premium, or opening premium.
- Volume and Trades are displayed beside Premium Activity.
- Positive ΔOI means net OI increased between vendor observations. It does not identify bought
  contracts, economic direction, or opening/closing side.
- Current OI is sourced from accepted complete chain/archive evidence and displayed separately.
- Radar date, chain/archive date, chain quote time, price time, volatility time, and Dealer time
  remain separately inspectable. Known Radar/chain date differences are not hidden.

## Observed Flow Direction

`Observed Flow Direction` remains compact `UNRESOLVED`. The drill-down states that buyer/seller
initiation, opening/closing intent, spreads, hedges, and other multi-leg structures are not resolved.
The UI explicitly says that `UNRESOLVED` is not Neutral.

## Volatility Redesign

The workspace displays IV Rank, Candidate IV, local Term Structure topology, Implied Move, nearest
shorter/longer nodes, differences, quality, and as-of evidence. Generic `Volatility Direction =
UNKNOWN`, cheap/rich IV, favorable/unfavorable, and long/short-vol recommendations are absent.

## Dealer/GEX Structure

- Anchor Expiry is the exact candidate expiration.
- Primary Floor is maximum positive net GEX strictly below spot on the anchor ladder; absolute GEX,
  negative nodes, and above-spot nodes are excluded.
- Primary Upper Positive-GEX Node is maximum positive net GEX strictly above spot.
- Immediate Below-Floor Node is the nearest usable lower strike.
- `STABILIZATION_BIAS` is conditional support-like structure while spot remains above the positive
  Floor; it is not guaranteed support or a buy signal.
- `DOWNSIDE_ACCELERATION_RISK` appears only when the immediate below-Floor cell is negative and is
  explicitly conditional on a Floor break.
- The five nearest lower cells plus every positive-below-spot candidate used by Floor selection are
  available in the audit; the UI never says no support exists farther below.
- Adjacent context uses only nearest previous + anchor + nearest next at the Floor strike. It never
  defines, changes, or scores the anchor Floor.
- `AVAILABLE` and `AVAILABLE_DEGRADED` normalized surfaces are usable while preserving source
  quality. `INCOMPLETE_OR_TRUNCATED` and `UNAVAILABLE` produce no structure or fake zero.

No full cross-expiry resonance or production GEX evolution model was added. Three preserved NVDA
ticker contexts were found, but they share the same Dealer source timestamp, so they are repeated
normalizations of one observation—not comparable temporal snapshots. BUILDING/DECAYING/MIGRATING
is therefore not feasible from current evidence and remains deferred.

## Persistence / Database

- Server confirmed: PostgreSQL 17.6 (`PostgresqlImpl`), not SQLite or a mock.
- Migration before: `20260814_0010`.
- Alembic head/current after: `20260814_0011`.
- New table: `phase2b_v3_research_workspaces`.
- Verified related tables: `phase2b_candidate_evaluations`, `phase2b_candidate_states`,
  `phase2b_ticker_context_snapshots`, and `phase2b_v3_research_workspaces`.
- The new append-only row stores normalized role objects, GEX structure, immutable source IDs,
  timestamps, config hash, and four rule versions. It references existing raw evidence instead of
  copying a full Heatmap payload.
- Unique identity is source v2 state + specification version.
- Controlled first run: `created=2 reused=0 missing=0`.
- Immediate replay: `created=0 reused=2 missing=0`.

## API

The FastAPI candidate confirmation response retains v1/v2 properties and adds
`v3_research_workspace` with `contract_identity`, `opportunity_positioning`, `underlying_price`,
`trade_structure` (volatility, dealer_gex, execution), provenance, rule versions, and config
identity. The Next.js `/api/candidate-context` proxy successfully returned v1, v2, and v3 together.
The read path and materializer do not import or call Nightwatch transport.

## Dashboard

Browser-skill QA validated the fixed local proxy and rendered dashboard:

- exact NVDA heading and detection DTE/bucket visible;
- three role modules visible;
- Premium/Volume/Trades and ΔOI/Current OI separated;
- price and GEX audit controls expand successfully;
- raw previous/anchor/next GEX values and all rule versions visible;
- no Volatility Direction, Dealer Direction, Model Bullish, or Trade Bullish labels;
- TSLA remains visible with Dealer Data unavailable and null nodes rendered as em dashes;
- browser console errors: 0.

## Chinese Field Guide

The central zh-TW glossary now documents Contract Premium Activity, exact-contract ΔOI, Observed
Flow Direction, Underlying Price Trend, Anchor Expiry, Primary Floor, Primary Upper Positive-GEX
Node, Immediate Below-Floor Node, Stabilization Bias, Downside Acceleration Risk, Adjacent Expiry
Context, and Dealer Source Quality. It emphasizes conditional/non-directional semantics and null
versus numeric-zero safety.

## NVDA Validation

Contract: `NVDA260821C00220000`

- Identity: NVDA 2026-08-21 $220 Call; DTE at detection 9; bucket SHORT.
- Premium Activity: $10,434,044; Volume 24,458; Trades 2,887.
- ΔOI: +4,531; Current OI: 62,832.
- Radar observation: 2026-08-12; chain observation: 2026-08-11.
- Observed Flow Direction: `UNRESOLVED`.
- Price Trend: `UPTREND`; volatility topology: `LOCAL_PEAK`; execution: `AVAILABLE`.
- Persisted Dealer spot: 223.8; source quality: `AVAILABLE_DEGRADED`.
- Primary Floor: 220, net GEX +59,652,544.
- Primary Upper Positive-GEX Node: 235, net GEX +23,738,526.
- Immediate Below-Floor Node: 217.5, net GEX -15,769,680.
- Hold condition: `STABILIZATION_BIAS`.
- Break condition: `DOWNSIDE_ACCELERATION_RISK`.
- Previous 2026-08-19 at 220: -773,790; next 2026-08-24 at 220: -3,048,716.
- Actual Adjacent Expiry Context: `NOT_ALIGNED`. Persisted evidence, rather than the earlier design
  illustration, is authoritative.

## TSLA Validation

Contract: `TSLA260814C00335000`

- Identity: TSLA 2026-08-14 $335 Call; DTE at detection 2; bucket VERY_SHORT.
- Positioning remains available as `SINGLE_EVIDENCE`; Price Trend is `DOWNTREND`; volatility
  topology is `INCOMPLETE`; execution is `AVAILABLE`.
- Dealer availability: `DATA_UNAVAILABLE`; source quality: `UNAVAILABLE`.
- Primary Floor, Primary Upper Node, and Immediate Below-Floor Node: null/em dash.
- Break state and Adjacent Expiry Context: `UNAVAILABLE`.
- No numeric zero is fabricated.

## Tests

- Pre-change backend baseline: 220 passed.
- Final backend: 239 passed. Pytest emitted only an environment cache-write warning; tests passed.
- Ruff: all checks passed with `--no-cache`.
- Alembic real PostgreSQL upgrade/current/head: passed at `20260814_0011`.
- PostgreSQL schema/read-back and idempotent replay: passed.
- Frontend ESLint: passed.
- Frontend production build: passed; 7 routes generated, including the fixed candidate proxy.
- Glossary completeness: 39 visible/legacy analytical columns, 128 documented fields; passed.
- Fixed Next.js proxy: NVDA and TSLA v3 payloads passed while v1/v2 remained present.
- Browser QA: NVDA, TSLA, audit expansion, null safety, field guide, and console (0 errors) passed.
- Automated tests made no live Nightwatch calls.

## Nightwatch Ledger

- Nightwatch endpoints called: none.
- Nightwatch network attempts: 0.
- Paid units consumed: 0.
- No external HTTP API was contacted. Local QA used only `http://127.0.0.1:3000`, its fixed
  `/api/candidate-context` proxy, and the local FastAPI confirmation read route. The configured
  development PostgreSQL server was contacted; its address and credentials are intentionally not
  reported.

## Security

- The one local `.env` found is Git-ignored.
- Both configured secret values were compared against every tracked file: 0 matches.
- Frontend contains no database URL, Nightwatch credential, public Nightwatch variable, direct
  Nightwatch host, or Authorization header.
- QA logs contain 0 configured secret-value matches.
- All 76 PostgreSQL JSON/JSONB columns were scanned for Authorization keys and Bearer credential
  patterns: 0 rows matched.
- No Authorization header was persisted; no full vendor payload was copied to v3 rows.

## Open Issues

- Dealer/GEX temporal evolution cannot be evaluated because preserved NVDA contexts currently
  reference one unique Dealer observation timestamp. This is a research limitation, not a v3
  runtime blocker.
- The NVDA source is `AVAILABLE_DEGRADED`; v3 exposes that quality plainly. A fresher or complete
  source was intentionally not requested because validation targeted zero Nightwatch calls.
- No Phase 2B v4 work was started.
