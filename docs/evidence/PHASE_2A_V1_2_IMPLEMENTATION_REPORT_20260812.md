# Phase 2A v1.2 Calibration Amendment — Implementation Report

Date: 2026-08-12
Scope: Phase 2A only; Phase 2B was not started.

## Git

- Starting SHA: `68e29876c1658eaefaa2a46a0a3f5e17258291a4`
- Implementation commit: `0815c0e0a9cbca36255b2943a251ac41119fc5ac`
- Commit message: `fix: calibrate 0dte activity and discovery ranking`
- Accepted v1.0 and v1.1 history was not rewritten.
- The report itself is committed separately so the implementation SHA remains auditable.

## Specification

- New immutable version: `signal_spec_v1.2_phase2a`.
- Historical `signal_spec_v1.0_phase2a` and `signal_spec_v1.1_phase2a` records remain unchanged.
- `SIGNAL_SPECIFICATION_V1.md` and `SCAN_ORCHESTRATION_V1.md` contain an explicit v1.1 → v1.2 change section.
- The v1.1 Persistent Positioning economic formula was not changed.

## 0DTE Baseline

- DTE 0 is excluded from ordinary cross-expiry Neighbor scoring.
- The prior 20 valid DTE-0 observation sessions for the same ticker are used; the current observation is excluded by a strict earlier-date query.
- Weekends, holidays, and missing sessions do not create synthetic rows.
- Formal score requires 20 prior valid observations. With fewer than 20, Same-Day is `NULL`, status is `INSUFFICIENT`, and raw metrics remain descriptive.
- Persisted statistics: prior-20 mean, median, MAD, empirical percentile, robust deviation, observation count, method, and coverage.
- Robust deviation uses `(current_share - median) / (1.4826 × MAD)` and the configured 70-point anchors.
- Historical percentile uses the deterministic weak empirical rank `count(prior <= current) / 20` and the configured 30-point anchors.
- Zero or unusably small MAD uses the percentile-only fixed 30-point evidence basis; it is not rescaled to 100.
- A missing current Volume Share cannot be scored or archived as a valid 0DTE observation.
- Raw cross-expiry Neighbor Ratio is retained only as `weight 0` diagnostic evidence.
- Current snapshots are idempotent by `ticker + observation_date`.

## Non-0DTE Same-Day

- DTE 1–7, 8–30, and 31–90 use separate peer pools.
- DTE 0 is never a peer.
- Maximum DTE distances are ±3, ±7, and ±14 respectively.
- Same verified expiry type is preferred where available; otherwise nearest DTE distance is used.
- At most four peers are selected and at least two are required.
- Insufficient or zero-median peers make Neighbor unavailable; the missing 40-point component is not rescaled.
- Non-0DTE Volume Share retains the v1.1 60-point anchors and works without historical observations.
- Peer count, peer DTEs, quality, and peer median volume are persisted for auditability.

## Persistent Positioning

- Expiry and contract Persistent Positioning formulas, 3/5/10-session windows, fixed weights, winning-window `MAX`, and confidence rules remain v1.1 behavior.
- Fewer than three valid OI observations remains `NULL / INSUFFICIENT`; missing history is not zero.

## Discovery

- Primary is the strongest available Same-Day or Persistent score.
- Secondary is the weaker score when both exist.
- Confirmation bonus is +0 below 40, +3 from 40–64.999, +6 from 65–79.999, and +10 at 80+, capped at 100.
- Scores are not averaged and a weak secondary signal never dilutes a strong primary signal.
- Source is `SAME_DAY`, `PERSISTENT`, `BOTH`, or `NONE`; `BOTH` requires a secondary score of at least 40.
- Evidence breadth is 0, 1, or 2 and is stored separately from the score.
- Eligibility still requires raw Same-Day ≥40, Persistent ≥65, or the explicit structural cold-start flag. The bonus cannot create eligibility.
- Structural-cold-start-only rows keep `Discovery = NULL` and are surfaced separately.

## Database

- Actual server: PostgreSQL 17.6 (`PostgresqlImpl`, transactional DDL).
- Alembic current: `20260812_0007 (head)`.
- Alembic head: `20260812_0007`.
- Applied migrations: `20260812_0006` and `20260812_0007`.
- Verified tables: `scan_runs`, `expiry_observations`, `zero_dte_activity_daily_snapshots`, `daily_oi_archive_runs`, `expiry_oi_daily_snapshots`, and `contract_oi_daily_snapshots`.
- Missing expected tables: none.
- Controlled run read-back: 111 expiry observations and 7 0DTE activity snapshots.
- All 7 cold-start 0DTE rows have `same_day_activity_score = NULL`; the legacy preliminary score is also `NULL`, not zero.

## Dashboard

- Ticker summary ranks only normally eligible expiries with a valid Discovery Score.
- An unscored DTE-0 row cannot win merely because its raw volume is largest.
- Structural-cold-start-only rows are exposed separately without an invented ranking score.
- Added cross-MAG7 distribution counts and ranked Top Expiry Discoveries.
- Added DTE, Discovery Source, Evidence Breadth, and detailed 0DTE baseline display.
- `NULL` values render as an em dash, never zero.
- Raw 0DTE Neighbor Ratio is explicitly labeled descriptive and `weight 0`.
- Browser QA against a production Next.js build confirmed FastAPI → PostgreSQL data through the fixed Next proxy, no console warnings/errors, and no page-level horizontal overflow at the tested 1265 px viewport.
- Browser code contains no direct Nightwatch transport; browser communication remains limited to the project's Next.js API routes.

## Chinese Field Guide

The central zh-TW guide now defines:

- Same-Day Activity Score for non-0DTE and separately calibrated DTE 0;
- 0DTE Baseline;
- Rolling Mean;
- Rolling Median + MAD;
- Historical Percentile;
- Discovery Score confirmation;
- Evidence Breadth;
- Cold Start as data coverage, not a market signal.

Glossary completeness remains enforced automatically.

## Tests and Quality Checks

- Backend: `135 passed in 1.47s`.
- Ruff: `All checks passed!`.
- Frontend ESLint: passed with no findings.
- Frontend production build: passed; `/`, `/field-guide`, `/api/mag7-scan`, and `/api/system-status` built successfully.
- Glossary: 20 visible analytical columns and 80 documented fields; null-safety and v1.2 distribution coverage passed.
- Alembic: current/head both `20260812_0007`; PostgreSQL read-back passed.
- Dashboard QA: actual production page, proxy data, distribution, 0DTE null rendering, and field guide verified.
- Automated tests made no live Nightwatch calls.

The host's pre-existing `.pytest_cache` directory had a Windows write/cleanup fault. The complete suite was therefore run with pytest's cache provider disabled; no test case or assertion was skipped. The unrelated globally installed LangSmith pytest plugin was also disabled.

## Controlled Validation

One interactive v1.2 scan was run. No second Daily OI Archive was run; the scan reused the existing archive.

- Run ID: `0f9ad2eb-29f3-4a34-833b-3b1241114451`
- Status: `PARTIAL`
- Tickers: 7
- Deep tickers: 4
- Deep expiries: 4
- Contracts read/analyzed from archive: 696
- Structural contract candidates: 26
- Clusters: 1
- OI Change Radar matches: 18
- Daily archive requests: 0
- Intraday requests: 0
- Duration: 235.422 seconds

The status was `PARTIAL` because the selected AMZN 2026-08-21 archive chain was `INCOMPLETE_CHAIN`. Selected MSFT, AAPL, and GOOGL chains were complete. No missing AMZN contracts were fabricated.

### Per-MAG7 strongest normally scored expiry

| Ticker | Strongest expiry | DTE | Same-Day | Persistent | Discovery | Source | Breadth | 0DTE baseline |
|---|---:|---:|---:|---:|---:|---|---:|---:|
| AAPL | 2026-08-21 | 9 | 50.140 | — | 50.140 | SAME_DAY | 1 | 0/20 |
| MSFT | 2026-08-21 | 9 | 51.555 | — | 51.555 | SAME_DAY | 1 | 0/20 |
| NVDA | — | — | — | — | — | NONE | 0 | 0/20 |
| AMZN | 2026-08-21 | 9 | 51.849 | — | 51.849 | SAME_DAY | 1 | 0/20 |
| META | 2026-08-21 | 9 | 44.675 | — | 44.675 | SAME_DAY | 1 | 0/20 |
| GOOGL | 2026-08-21 | 9 | 48.599 | — | 48.599 | SAME_DAY | 1 | 0/20 |
| TSLA | 2026-08-21 | 9 | 40.000 | — | 40.000 | SAME_DAY | 1 | 0/20 |

All reported nonzero-DTE ticker winners used 3 comparable peers at DTE 12, 14, and 16. Persistent was unavailable because the archive still has insufficient distinct OI sessions.

### Cross-expiry distribution

- Total 0–90 DTE expiries: 90
- Scored: 83
- Normally eligible: 7
- Discovery ≥90: 0
- Discovery 80–89.999: 0
- Discovery 65–79.999: 0
- Discovery 40–64.999: 7
- Discovery <40: 76
- Unavailable: 7
- Cold start: 7

This confirms the former seven-ticker maximum-selection effect is no longer presented as though it were the full expiry distribution.

### 0DTE controlled result

All seven DTE-0 rows had:

- calibrated Same-Day: `NULL`;
- Persistent: `NULL`;
- Discovery: `NULL`;
- Source: `NONE`;
- Evidence breadth: `0`;
- baseline: `0/20`, `INSUFFICIENT`.

Raw Volume Share and raw Neighbor Ratio were preserved only for diagnostics:

| Ticker | 0DTE Volume Share | Raw Neighbor Ratio | Scoring weight |
|---|---:|---:|---:|
| AAPL | 55.718% | 73.515 | 0 |
| MSFT | 49.901% | 40.125 | 0 |
| NVDA | 55.814% | 38.209 | 0 |
| AMZN | 48.975% | 123.769 | 0 |
| META | 59.081% | 34.299 | 0 |
| GOOGL | 48.943% | 70.932 | 0 |
| TSLA | 65.122% | 149.256 | 0 |

The large ratios therefore no longer produce 0DTE scores of 93–100.

## Nightwatch Call Ledger and Quota

Only the one controlled interactive scan contacted Nightwatch during this amendment:

- `/v1/options/expiry-breakdown/{ticker}`: 7 calls, one for each MAG7 ticker.
- `/v1/options/options-volume/{ticker}`: 7 calls, one for each MAG7 ticker.
- `/v1/options/oi-change/AAPL`: 1 call.
- `/v1/options/oi-change/AMZN`: 1 call.
- `/v1/options/oi-change/GOOGL`: 1 call.
- `/v1/options/oi-change/MSFT`: 1 call.

Totals:

- Network attempts: 18.
- HTTP 200 responses: 18.
- Retries: 0.
- Pre-validation quota: 99,890 inferred from the first response's post-request remainder.
- Post-validation quota: 99,872.
- Paid units consumed: 18.
- Daily archive calls: 0.
- Chain snapshot calls: 0.
- Contract intraday calls: 0.
- No rerun was performed to improve scores.

## Security

- `.env` is Git-ignored and untracked.
- Exact local `DATABASE_URL` and Nightwatch key matches in tracked files: 0.
- Frontend references to `DATABASE_URL`, `NIGHTWATCH_API_KEY`, `Authorization`, or `NEXT_PUBLIC_*`: 0.
- Persisted raw evidence rows containing an `Authorization` key: 0.
- Persisted raw evidence rows containing either exact local secret: 0.
- No credential was printed, logged, committed, or included in this report.
- No browser-to-Nightwatch call was introduced.

## Open Issues

1. All tickers currently have 0/20 prior valid 0DTE sessions. Formal calibrated 0DTE Same-Day scores will remain unavailable until 20 distinct valid sessions accumulate; this is expected cold-start behavior, not a failure.
2. The reused AMZN 2026-08-21 archive chain is incomplete, so its contract structural deep dive remains unavailable and the controlled scan is truthfully `PARTIAL`. A future authoritative archive session may resolve it; this amendment did not rerun the archive merely to improve appearance.

No Phase 2B work was started.
