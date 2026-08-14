# Phase 2B v2 Trade Setup State Model — Implementation Report

Date: 2026-08-14  
Starting Git SHA: `bf52abd17216bc279e0e94d0813129800ff9b86a`  
Implementation commit: recorded in Git and in the delivery message (the report is part of that commit)

## Scope and specification

- Added immutable `signal_spec_v2.0_phase2b` without rewriting Phase 2A or Phase 2B v1.x evidence.
- Added six independent state objects: Positioning, Price, Volatility, Dealer/GEX, Execution, and
  Research Readiness.
- Added no universal, weighted, tradeability, conviction, bullish, or bearish score.
- Direction remains `UNRESOLVED`.
- Phase 2B v3 was not started.

## State model

Positioning counts Radar Event, Contract Persistence, Expiry Persistence, Structure, and exact
Cluster membership as five independent evidence families. Each family counts at most once. Radar's
numeric fields remain one family. Insufficient persistence history is explicitly
`NOT_YET_AVAILABLE`; one present family is `SINGLE_EVIDENCE`, and two or more are `MULTI_EVIDENCE`.

Price reuses the accepted v1.x regular-session trend and raw return/SMA/ATR context unchanged.

Term topology uses the exact candidate node and nearest shorter/longer nodes with only a `1e-12`
floating-point equality tolerance. It persists raw nodes, IVs, differences, neighbor mean, and
implied move. No economic threshold or direction label was introduced.

Dealer sign uses only an exact candidate expiry × strike cell. Source quality, cell status, and sign
remain separate. A compatibility regression found during controlled validation was fixed: accepted
v1.1 rows stored exact GEX in the nested `candidate_cell`, while newer rows also expose flattened
fields. Both preserved shapes now produce the same exact sign without modifying old rows.

Execution reuses bid/ask/mid/spread/OI/Greeks and accepted Phase 2A risk/liquidity evidence. No new
execution threshold was added.

Research Readiness checks six layers. Zero missing/degraded layers is `CONTEXT_COMPLETE`, one is
`CONTEXT_PARTIAL`, and two or more is `CONTEXT_LIMITED`. This is context completeness, not alpha or
trade quality.

## Persistence and database

- New append-only table: `phase2b_candidate_states`.
- Migration: `20260814_0010`, applied to real PostgreSQL.
- Alembic current/head: `20260814_0010` / `20260814_0010`.
- Uniqueness: `(candidate_evaluation_id, specification_version)`.
- Preserved links: source evaluation, ticker context, contract/expiry provenance, exact cluster IDs,
  source timestamps, source context spec/config/hash, and v2 state config/hash/rule versions.
- Database read-back confirmed every expected v2 state column.
- Replaying the same source evaluations returned `created=0`, `reused=2`.

## API and dashboard

- Existing confirmation payload fields remain unchanged; nullable `v2_state` is additive.
- V2 state is constrained to the same source candidate evaluation returned by the v1.x payload, so
  stale state cannot be silently mixed with a newer context.
- Research rows now expose `entity_type=CONTRACT|EXPIRY_ONLY`. Expiry-only rows do not fabricate a
  contract state, Greeks, execution, or exact GEX cell.
- Dashboard candidate detail adds Research State and Positioning Evidence near the top while retaining
  raw Price, Volatility, Dealer/GEX, Liquidity/Greeks, and timestamps.
- The browser still uses only the fixed Next.js candidate proxy. The frontend contains no Nightwatch
  transport or secret.
- Browser QA rendered the dashboard with no console warnings/errors. The current dashboard dataset
  had no latest route-qualified candidate row, so visual click-through was unavailable; both NVDA
  and TSLA fixed-proxy payloads were verified directly through the running Next.js application.

## Controlled persisted-data validation

No Nightwatch endpoint was contacted. No paid unit was consumed.

| Contract | Positioning | Price | Term | Dealer sign | Dealer quality | Readiness | Direction |
|---|---|---|---|---|---|---|---|
| NVDA260821C00220000 | MULTI_EVIDENCE | UPTREND | LOCAL_PEAK | POSITIVE_NET_GEX | AVAILABLE_DEGRADED | CONTEXT_PARTIAL | UNRESOLVED |
| TSLA260814C00335000 | SINGLE_EVIDENCE | DOWNTREND | INCOMPLETE | UNKNOWN | UNAVAILABLE | CONTEXT_PARTIAL | UNRESOLVED |

NVDA's one degraded layer is Dealer/GEX source quality. TSLA's exact candidate term node is ready
even though neighbor topology is incomplete; its one missing layer is unavailable Dealer/GEX.

## Quality gate

- Backend pre-change baseline: `194 passed`.
- Backend final: `220 passed`.
- Ruff: passed.
- Frontend ESLint: passed.
- Frontend production build: passed; all seven Next.js routes compiled.
- Glossary completeness: passed (`27` registered visible columns, `116` documented fields).
- Alembic real PostgreSQL migration/current/head: passed.
- PostgreSQL state read-back and idempotency: passed.
- Fixed Next.js proxy read-back for NVDA and TSLA: passed.
- Browser QA: passed with zero console warnings/errors.
- Automated tests made no live Nightwatch calls.

## Security and call ledger

- `.env`, backend `.env`, and frontend `.env.local` remain ignored.
- No tracked file contains a `DATABASE_URL=` or `NIGHTWATCH_API_KEY=` assignment.
- Frontend application code contains neither database nor Nightwatch credential material.
- No Authorization header field is persisted by the schema or v2 state.
- Nightwatch endpoints called: none.
- Network attempts: `0`.
- Paid units consumed: `0`.

## Open issues

- Contract and expiry persistence remain `NOT_YET_AVAILABLE` until sufficient distinct historical OI
  observations exist; the implementation intentionally does not invent history.
- NVDA Dealer/GEX source evidence is vendor-degraded and TSLA Dealer/GEX is unavailable in the
  preserved context. These correctly prevent `CONTEXT_COMPLETE` and are not implementation errors.
