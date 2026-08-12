# Phase 2A v1.1 Implementation and Runtime Validation Report

Date: 2026-08-12  
Scope: Daily Full OI Archive, Dual Discovery, OI Positioning Structure  
Specification: `signal_spec_v1.1_phase2a`  
Phase 2B: not started

## Git

- Accepted Phase 2A baseline: `4bb3f8261c49e88cb58635ceaf5764e55a7760b8`.
- Clean repository HEAD at task start: `fb810bab4f3886e7126c64b5dd8b12e762595a1e`. This is the documentation-only Vendor Capability Validation commit whose parent history contains the accepted baseline.
- Primary implementation commit: `b06b8011bfcb797508723311b9e8cf99a91fca2c` (`feat: add daily oi archive and dual discovery`).
- Runtime-aligned Radar display fix: `e064f008f0c0a027d679cf0cdcdf5c7504e82795` (`fix: clarify oi radar dashboard status`).
- Accepted history was not rewritten or squashed.
- This report is added by a later documentation-only commit; its SHA is reported in the final handoff because a commit cannot contain its own SHA.

## Database

- Connection target: the configured development Supabase PostgreSQL database. No database credential was printed or copied into tracked files.
- SQLAlchemy/Alembic runtime: PostgreSQL, confirmed by `PostgresqlImpl` and transactional DDL.
- Alembic current revision: `20260812_0005 (head)`.
- Alembic head revision: `20260812_0005 (head)`.
- New migration: `20260812_0005_phase2a_v11_daily_oi_archive.py`; prior migrations were not modified.
- Existing data is preserved through additive tables/columns and nullable v1.1 fields for historical v1.0 rows.
- New tables verified in the real database:
  - `daily_oi_archive_runs`
  - `daily_oi_archive_tickers`
  - `expiry_oi_daily_snapshots`
  - `contract_oi_daily_snapshots`
  - `oi_change_radar_observations`
- Uniqueness is enforced for `(ticker, expiration, vendor_oi_date)`, `(ticker, contract_symbol, vendor_oi_date)`, and `(source_request_id, contract_symbol)` Radar evidence.
- Database read-back verified archive rows, contract rows, expiry rows, scan results, clusters, Radar rows, and API usage observations.

## Specification

- The immutable current version is `signal_spec_v1.1_phase2a`.
- Historical v1.0 scan rows were not rewritten or recalculated.
- `SIGNAL_SPECIFICATION_V1.md` documents exact v1.0 to v1.1 changes, fixed component anchors, missing-evidence behavior, and the removal of runtime-unsupported contract-volume scoring.
- `SCAN_ORCHESTRATION_V1.md` documents two independent workflows and separate budgets.
- No Phase 2B logic, Tradeability Score, investor-direction inference, or predictive claim was added.

## Daily OI Archive

- Command: `python -m app.cli archive-mag7-oi`.
- Scope: all configured MAG7 tickers and every available expiration from 0 through 180 calendar DTE, with Call and Put contracts archived symmetrically.
- Trigger configuration: enabled, `Asia/Singapore`, local time `12:00`, `max_dte=180`.
- The clock is only a trigger. Nightwatch `vendor_oi_date`/`as_of` is the stored observation identity.
- Same vendor date is idempotently skipped as `NO_NEW_VENDOR_OI_SNAPSHOT`; no execution-date OI date is manufactured.
- A durable in-process scheduler was intentionally not introduced. Deployment must invoke the CLI/job through an external durable scheduler.
- Archive budget is independent: 250 consumed units and 350 network attempts. Budget exhaustion marks the run `PARTIAL_ARCHIVE_BUDGET_LIMIT`, every remaining known expiry `BUDGET_NOT_ATTEMPTED`, and later tickers `BUDGET_NOT_ATTEMPTED`.
- A chain is accepted only when `truncated == false` and `returned_contract_count == total_contracts`. Incomplete responses preserve raw evidence and never generate fabricated contracts or complete-universe concentration metrics.

## Expiry History

- `options.oi_per_expiry` is the authoritative daily expiry OI source.
- Stored fields include vendor date/as-of, Call OI, Put OI, Total OI, DTE, immutable bucket, archive run, request/raw evidence references, and specification version.
- Total, Call, and Put OI Shares use their corresponding complete 0-180 DTE denominators; zero denominators produce null rather than a fabricated zero.
- OI Skew is retained as positioning context only and is not interpreted as bullish or bearish.
- Total/Call/Put OI Share Change uses percentage-point change across distinct valid OI observation sessions.
- 3/5/10 observation features remain null when the required historical observation does not exist.

## Contract History

- Complete daily contract OI snapshots are append-only by vendor date.
- Stored data includes contract identity, expiration/right/strike, DTE/bucket, OI, bid/ask, IV, supported Greeks, underlying price, source timestamps, raw evidence, request ID, archive run, and spec version.
- Local `delta_oi_1d` and 3/5/10 history are derived only from distinct archived observations.
- First observation does not assume prior OI was zero.
- A missing/expired contract is not inferred closed solely from absence.

## Same-Day Discovery

- Current activity uses per-expiry `options.expiry_breakdown` and ticker-day `options.options_volume` independently.
- Ticker Call/Put Volume, OI, skew, and premium context remain ticker-scoped and are never attributed to a selected expiry.
- Same-Day Activity Score remains on a fixed 0-100 scale:
  - Expiry Volume Share: 60 maximum.
  - Comparable-expiry Volume Neighbor Ratio: 40 maximum.
- Unsupported per-expiry Call/Put Volume Skew was removed.
- Missing components are not rescaled to 100; score basis weight, coverage, and missing components are persisted.

## Persistent Discovery

- Expiry and contract history calculate 3/5/10 valid-observation windows.
- Expiry score uses absolute OI Share Change, absolute OI Growth, and Directional Persistence; the overall value is the maximum available window, never an average.
- Contract score uses absolute OI Growth, absolute build relative to same-side expiry OI, and Directional Persistence; it also takes the maximum available window.
- History confidence is `INSUFFICIENT`, `LOW`, `MEDIUM`, or `FULL` at the specified observation counts.
- Fewer than three observations produces a null score.
- `STRUCTURAL_COLD_START_ELIGIBLE` is separate, explicitly configured, and is not mixed into Persistent Positioning Score.

## Dual Discovery

- `expiry_discovery_score = MAX(same_day_activity_score, expiry_persistent_positioning_score)`.
- Discovery source persists `SAME_DAY`, `PERSISTENT`, or `BOTH`.
- Eligibility is Same-Day >= 40 or Persistent >= 65, with the separate cold-start structural flag.
- At most four deep tickers are selected, with at most one expiration in each `VERY_SHORT`, `SHORT`, and `MEDIUM` bucket.
- Interactive scans reuse the latest valid archive and do not rebuild the 0-180 DTE chain archive.

## Contract Positioning Structure

- Runtime-unsupported Contract Anomaly inputs were removed from v1.1 production scoring: Contract Volume/OI, Premium, Historical Contract Volume Abnormality, and Intraday Burst.
- Contract Positioning Structure Score is 0-100 and uses fixed configured components:
  - same-side expiry OI concentration: 40;
  - neighbor-strike OI anomaly: 30;
  - bid/ask liquidity quality: 15;
  - absolute-delta/moneyness quality: 15.
- Spread above 50% is a hard reject from the tradeable structural-candidate set.
- Low delta is not hard rejected; `LOTTO_RISK` remains descriptive.
- The score describes current OI surface structure, not unusual trading volume.

## OI Change Radar

- `options.oi_change` is supplemental `OI_CHANGE_RADAR` evidence only.
- Ranked subset rows preserve previous/current/delta OI, relative change, volume, trades, average price, premium, rank, bid/ask/fill, observation dates, raw evidence, and request ID.
- The ranked subset is never an OI Share denominator and is not the Daily OI Memory source.
- Absence does not lower a score.
- Dashboard status distinguishes `OBSERVED`, `NOT_OBSERVED` after a tested ticker, and `NOT_TESTED` when the ticker was outside the Radar deep-dive request set.

## Clusters

- Call and Put clusters remain separate.
- Cluster scoring is OI-based only:
  - OI-weighted constituent structural strength: 30;
  - same-side expiry OI concentration: 35;
  - strike coherence: 25;
  - aggregate liquidity: 10.
- Premium concentration, volume concentration, and volume-weighted behavior are not used.
- Available history also exposes constituent build/decline counts, OI-weighted persistence, and cluster net OI change without adding an opaque trading score.

## Dashboard

- The browser communicates only with fixed same-origin Next.js routes, which proxy to FastAPI; no frontend Nightwatch request or credential exists.
- The production dashboard displays Same-Day, Persistent, Discovery Score/Source, OI Share, OI Share Change, OI Skew, History Coverage, Contract Structure/Persistent scores, Radar status, Call/Put cluster scores, and archive vendor date/freshness.
- OI Share is rendered as a percentage.
- Unavailable values render as an em dash, never numeric zero.
- System status reads the latest persisted API usage observation and, after the controlled validation, returned database connected, Nightwatch connected, quota remaining 99,890, and HTTP 200.
- Browser QA validated the production Next.js -> FastAPI -> PostgreSQL path, the 7-row result table, the zh-TW guide, and zero browser console warnings/errors.
- A nullable score bug discovered during QA was regression-tested. The latest-result API was changed from per-row database reads to batched reads, reducing observed local response time from about 40 seconds to about 6 seconds.

## Chinese Field Guide

- The central zh-TW glossary now explicitly defines Same-Day Activity Score, Persistent Positioning Score, OI Share, percentage-point OI Share Change, Contract Positioning Structure Score, Contract Persistent Positioning Score, OI Change Radar, ticker-level Call/Put activity, and Phase 2A v1.1 Intraday Activity weight zero.
- It explicitly states that structure is not investor direction and that ticker-wide activity is not expiry-level evidence.
- Automated completeness covers 18 visible analytical columns and 74 documented fields.

## Automated Tests and Quality Checks

- Backend: `103 passed in 1.24s` using mocks/fixtures and with no live Nightwatch calls.
- Ruff: `All checks passed!`.
- Frontend ESLint: passed (`npm run lint`).
- Frontend production build: passed with Next.js 16.3.0; static `/`, `/field-guide`, and dynamic fixed proxy routes built successfully.
- Glossary: 18 visible analytical columns, 74 documented fields; null-safety and v1.1 visible-field coverage passed.
- Alembic: current/head both `20260812_0005`; PostgreSQL transactional migration confirmed.
- `git diff --check`: no whitespace errors.

## Live Daily Archive

Archive run: `19ab0f69-e033-49c0-8c3b-22fc5dba49d9`  
Status: `PARTIAL` because some vendor chain responses were incomplete or HTTP 202.  
Vendor OI date for every ticker: `2026-08-11`.

| Ticker | Expiries | Complete | Incomplete | Contracts persisted |
|---|---:|---:|---:|---:|
| AAPL | 15 | 10 | 5 | 1,376 |
| AMZN | 15 | 8 | 7 | 922 |
| GOOGL | 15 | 8 | 7 | 1,326 |
| META | 15 | 9 | 6 | 2,634 |
| MSFT | 15 | 8 | 7 | 1,262 |
| NVDA | 15 | 11 | 4 | 1,584 |
| TSLA | 15 | 9 | 6 | 2,186 |
| **Total** | **105** | **63** | **42** | **11,290** |

- Consumed units: 79 of the archive budget of 250.
- Network attempts: 112 of the archive budget of 350.
- HTTP results: 79 HTTP 200 and 33 HTTP 202.
- Read-back matched the CLI totals.
- Only one archive was run; it was not repeated to improve completeness.

## Live Interactive Scan

Successful validation run: `d0fcf187-dcab-42b7-8690-9d3087e47668`  
Status: `PARTIAL`, truthfully caused by selected NVDA `2026-08-12` lacking a complete archived chain.  
Consumed units: 4; network attempts: 4; cache hits: 14; fresh requests: 4.  
Daily archive requests: 0; Intraday requests: 0.  
Deep tickers: 4; selected expiries: 7; contracts analyzed: 1,642; structural candidates: 43; cluster objects: 2; Radar matches: 66.

| Ticker | Same-Day | Persistent / coverage | Discovery / source | Selected expiries | Structural candidates | Call / Put clusters | Radar matches |
|---|---:|---|---|---|---:|---|---:|
| AAPL | 93.478 | null / INSUFFICIENT | 93.478 / SAME_DAY | 2026-08-12 VERY_SHORT | 3 | 0 / 1 (61.5) | 15 |
| AMZN | 83.892 | null / INSUFFICIENT | 83.892 / SAME_DAY | none (outside top four) | 0 | 0 / 0 | not tested |
| GOOGL | 88.681 | null / INSUFFICIENT | 88.681 / SAME_DAY | none (outside top four) | 0 | 0 / 0 | not tested |
| META | 100.000 | null / INSUFFICIENT | 100.000 / SAME_DAY | 2026-08-12 VERY_SHORT; 2026-08-21 SHORT | 20 | 0 / 1 (71.8) | 20 |
| MSFT | 91.738 | null / INSUFFICIENT | 91.738 / SAME_DAY | none (outside top four) | 0 | 0 / 0 | not tested |
| NVDA | 98.735 | null / INSUFFICIENT | 98.735 / SAME_DAY | 2026-08-12 VERY_SHORT; 2026-08-21 SHORT | 4 | 0 / 0 | 4 |
| TSLA | 100.000 | null / INSUFFICIENT | 100.000 / SAME_DAY | 2026-08-12 VERY_SHORT; 2026-08-21 SHORT | 16 | 0 / 0 | 27 |

Persistent scores are correctly unavailable because only one valid vendor OI observation exists. No history was invented.

An earlier validation attempt, run `d06ff4bc-b503-4bce-bda8-c6288b0b8d60`, made 14 successful activity requests but exceeded the local runtime window during N+1 PostgreSQL reads. It was explicitly marked `FAILED_RUNTIME_TIMEOUT`; its raw evidence and audit rows remain truthful. The batch-read regression fix was then validated by the single successful run above. The retry was for a runtime defect, not to improve financial results.

## Nightwatch Call Ledger

Every Nightwatch endpoint actually contacted during this task is listed below. No `/discover`, `/openapi.json`, `/health`, paid endpoint outside this list, or `contract_intraday` call was made.

| Endpoint pattern | Attempts | HTTP 200 | HTTP 202 | Purpose |
|---|---:|---:|---:|---|
| `/v1/options/oi-per-expiry/{ticker}` | 7 | 7 | 0 | daily expiry OI surface |
| `/v1/options/chain-snapshot/{ticker}` | 105 | 72 | 33 | complete 0-180 DTE archive |
| `/v1/options/expiry-breakdown/{ticker}` | 7 | 7 | 0 | same-day activity surface; later reused from cache |
| `/v1/options/options-volume/{ticker}` | 7 | 7 | 0 | ticker-day Call/Put context; later reused from cache |
| `/v1/options/oi-change/{ticker}` | 4 | 4 | 0 | selected-ticker Radar evidence |
| **Total** | **130** | **97** | **33** | no retries |

## Quota

- Pre-validation remaining quota: 99,987 (inferred from the first response header after its one-unit request).
- Post-validation remaining quota: 99,890.
- Paid units consumed: 97 total.
  - Daily archive: 79.
  - First interactive attempt: 14.
  - Successful interactive validation: 4.
- Network attempts: 130 total.
- Separate per-workflow limits were respected: archive 79/250 units and 112/350 attempts; interactive attempts 14/75 and 4/75 units respectively.
- HTTP 202 chain responses consumed no paid unit according to persisted usage metadata.

## Security

- `.env` is ignored by `.gitignore` and is not tracked.
- The actual `DATABASE_URL` value had zero matches in tracked files.
- The actual `NIGHTWATCH_API_KEY` value had zero matches in tracked files.
- Frontend source had zero matches for database/Nightwatch secret symbols or Authorization handling.
- The API key remains server-side and is never printed by either CLI.
- Authorization is constructed only inside the Nightwatch transport. Headers are not included in raw evidence, usage audit, archive, normalized snapshot, scan, Radar, API, or frontend models.
- Raw evidence stores response payloads and safe request metadata, never request Authorization headers.
- Browser traffic remained Next.js/FastAPI only; there was no direct browser-to-Nightwatch request.

## Open Issues

- The live vendor returned 42 incomplete/pending chains (33 were HTTP 202). Those expiries are explicitly incomplete and have no fabricated contract universe; a future externally scheduled archive may fill them only when a newer authoritative vendor OI date is available.
- Only one valid OI observation session exists, so 3/5/10 observation Persistent Positioning values and OI Share Change are correctly null. This resolves naturally through future idempotent daily archives.
- Deployment still needs to configure an external durable scheduler for the documented `Asia/Singapore` 12:00 archive trigger. No unsafe in-process scheduler was added.
- There is no remaining implementation blocker, and Phase 2B has not started.
