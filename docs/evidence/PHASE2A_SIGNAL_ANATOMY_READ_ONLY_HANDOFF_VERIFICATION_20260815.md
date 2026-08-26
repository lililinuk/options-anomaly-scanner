# Phase 2A Signal Anatomy — Read-Only Handoff Verification

Date: 2026-08-15  
Repository: `lililinuk/options-anomaly-scanner`

## A. Repository Authority

- Branch: `main`
- HEAD: `1e29c92956b39f005dab0c4eb163150ee12a0c9d`
- Locally available `origin/main`: `1e29c92956b39f005dab0c4eb163150ee12a0c9d`
- Current specification: `signal_spec_v1.3_phase2a`
- Working tree before inspection: not clean
- Pre-existing untracked file: `docs/evidence/PHASE2B_V31_FIRST_REAL_GITHUB_SCHEDULED_RUN_CLOSEOUT_20260815.md`
- Tracked diff: none
- Staged diff: none
- The verification itself changed no repository file.

The CLI and FastAPI instantiate `app.scanner.v13.Mag7Scanner`. The current production chain is therefore v13 -> v12 -> v11. The older `app.scanner.service` remains imported for shared exception/summary types, but is not the scanner class instantiated by the current entry points.

## B. Executive Verification Matrix

| Concept | Status | Production? | Dashboard? | Exact formula verified? |
|---|---|---:|---:|---:|
| Radar | `IMPLEMENTED_AND_ACTIVE` | YES | YES | YES |
| Contract Persistence | `IMPLEMENTED_AND_ACTIVE` | YES | YES | YES |
| Expiry Persistence | `IMPLEMENTED_AND_ACTIVE` | YES | PARTIAL | YES |
| Expiry Activity | `IMPLEMENTED_AND_ACTIVE` | YES | YES | YES |
| 0DTE Participation | `IMPLEMENTED_AND_ACTIVE` | YES | PARTIAL | YES |
| Contract Positioning Structure | `IMPLEMENTED_AND_ACTIVE` | YES | YES | YES |
| Cluster | `IMPLEMENTED_AND_ACTIVE` | YES | PARTIAL | YES |
| Volume/OI | `IMPLEMENTED_BUT_NOT_CURRENTLY_ACTIVE / legacy` | NO | NO | Legacy formula verified |
| Positioning Breadth | `IMPLEMENTED_AND_ACTIVE` | Phase 2B state | YES | YES |
| LOW_OI_BASE | `IMPLEMENTED_AND_ACTIVE` | Radar risk flag | YES | YES |
| Legacy v1.2 Discovery Score | `IMPLEMENTED_BUT_NOT_CURRENTLY_ACTIVE / legacy` | Not active deep-dive selector | Not rendered | YES |
| Monthly OPEX | `IMPLEMENTED_DISPLAY_ONLY` | Label/context only | YES | N/A |
| Nightwatch MCP | `NOT_FOUND` | NO | NO | N/A |
| Signal Decay | `INTENTIONALLY_EXCLUDED` | NO | NO | N/A |

The current Phase 2A production candidate selector uses the v1.3 three-route priority, not a universal Same-Day/Persistent Discovery Score.

## C. Contract Persistence — Exact Formula

### Historical observations

One valid Contract OI observation is a `contract_oi_daily_snapshots` row for an exact contract on one distinct `vendor_oi_date`.

- Contract rows are written only when the chain has `truncated == false` and returned contract count equals `total_contracts`.
- Uniqueness is `ticker + contract_symbol + vendor_oi_date`.
- Windows contain 3, 5, or 10 valid observations, not calendar days.
- Dates are deduplicated before scoring.
- Missing dates are absent observations; they are not interpolated or converted to zero.
- A disappeared contract is not interpreted as zero OI or a closed position.
- A first observation has `delta_oi_1 = NULL` and `first_observation = true`.
- Fewer than three observations produces a NULL score/state/winning window and `INSUFFICIENT` confidence.

For a window of N valid observations:

```text
net_oi_change_N = current_oi - first_oi
oi_growth_N = net_oi_change_N / first_oi
absolute_build_share_N =
    abs(net_oi_change_N) / current_same_side_expiry_oi
```

Zero or NULL denominators produce NULL. The implementation does not replace these denominators with 1.

### Components

1. Absolute OI Growth — maximum 35

| Absolute growth | Points |
|---:|---:|
| 10% | 0 |
| 25% | 8 |
| 50% | 16 |
| 100% | 25 |
| 200%+ | 35 |

2. Absolute Build Share — maximum 35

| `abs(net ΔOI) / current same-side expiry OI` | Points |
|---:|---:|
| 0.25% | 0 |
| 0.5% | 5 |
| 1% | 12 |
| 2% | 22 |
| 5%+ | 35 |

3. Directional Persistence — maximum 30

| Matching transition share | Points |
|---:|---:|
| 50% | 0 |
| 60% | 5 |
| 70% | 10 |
| 80% | 18 |
| 90% | 25 |
| 100% | 30 |

All anchors use capped piecewise-linear interpolation. Values below the first anchor receive the first anchor's points; values above the last anchor are capped.

Contract Persistence does **not** use Absolute OI Share Change. That component belongs to Expiry Persistence.

### Directional persistence

```text
net > 0:
    state = PERSISTENT_BUILD
    persistence = positive transitions / (N - 1)

net < 0:
    state = PERSISTENT_DECLINE
    persistence = negative transitions / (N - 1)

net == 0:
    state = FLAT
    persistence = 0
```

The implementation does not require every observation to increase. It measures the proportion of transitions whose sign agrees with the window's net direction. Intermediate reversals are allowed. A persistent decline can receive a high or full score because magnitude inputs are absolute and negative transitions are rewarded when net OI is negative. Build/decline does not imply bullish/bearish direction.

### Winning window

```text
window_score =
    available Absolute Growth points
  + available Absolute Build Share points
  + available Directional Persistence points
```

- Missing components are omitted without rescaling.
- Unavailable windows are excluded.
- Overall score is the maximum available 3/5/10-window score, not an average.
- A score tie selects the larger window because the implementation compares `(score, window, state)` tuples.
- Winning window, state, and component breakdown are persisted.

## D. Expiry Persistence — Exact Formula

Expiry observations come from append-only `expiry_oi_daily_snapshots` produced from `options.oi_per_expiry`:

```text
expiry_total_oi = call_oi + put_oi
expiry_total_oi_share =
    expiry_total_oi / ticker total OI in the 0–180 DTE scope
```

Expiry history does not require the corresponding contract chain to be complete. The expiry OI snapshot is created from a valid, single-vendor-date `oi_per_expiry` surface before chain completeness is evaluated.

Windows are the last 3, 5, or 10 distinct vendor OI observations.

### Components

1. Absolute OI Share Change — maximum 40

```text
oi_share_change_N = current_total_oi_share - first_total_oi_share
scoring input = abs(oi_share_change_N)
```

0.5/1/2/5/10 percentage points -> 0/8/16/28/40.

2. Absolute OI Growth — maximum 30

```text
oi_growth_N = (current_total_oi - first_total_oi) / first_total_oi
```

5/10/25/50/100% -> 0/5/12/20/30.

3. Directional Persistence — maximum 30

Uses the same net-direction and matching-transition calculation as Contract Persistence. 50/60/70/80/90/100% -> 0/5/10/18/25/30.

Call and Put OI Share Changes are also calculated and preserved but are not expiry score components. Missing components remain NULL and are not rescaled. The overall score is the maximum available 3/5/10-window score; ties favor the larger window. Confidence is `<3 INSUFFICIENT`, `3–4 LOW`, `5–9 MEDIUM`, `10+ FULL`.

| Expiry Persistence | Contract Persistence |
|---|---|
| Absolute OI Share Change, 40 | Absolute OI Growth, 35 |
| Absolute OI Growth, 30 | Absolute Build Share against same-side expiry OI, 35 |
| Directional Persistence, 30 | Directional Persistence, 30 |
| Input OI is Call OI + Put OI | Input OI is exact contract OI |
| Valid expiry OI surface is sufficient | Complete chain contract archive required |

## E. Expiry Activity — Exact Formula

`EXPIRY_ACTIVITY` means current-session activity concentration. `EXPIRY_PERSISTENCE` means multi-observation OI accumulation or decline.

### Volume Share

For DTE > 0:

```text
expiry_volume_share =
    current expiry total_volume
    / sum(all expiry total_volume in the ticker's 0–180 DTE scope)
```

The numerator is expiry-level total volume from `options.expiry_breakdown`. The denominator includes all 0–180 DTE expiries, including DTE 0. There is no expiry-level Call/Put volume split. Ticker-level Call/Put fields from `options.options_volume` are context only.

Score maximum 60: 5/10/20/30/40/50% -> 0/10/25/40/50/60.

### Comparable neighbor

Only DTE 1–90 has a scored neighbor component.

| Bucket | Peer scope | Maximum DTE distance |
|---|---|---:|
| VERY_SHORT_NONZERO | 1–7 | ±3 |
| SHORT | 8–30 | ±7 |
| MEDIUM | 31–90 | ±14 |

- DTE 0 is excluded.
- Peers stay in the same bucket and distance limit.
- Matching verified vendor expiration type is preferred.
- Selection then sorts by absolute DTE distance and DTE.
- Maximum four peers; minimum two.
- Comparison statistic is median peer volume.

```text
neighbor_ratio =
    target expiry total_volume / median(selected peer total_volume)
```

Score maximum 40: 1.2/1.5/2/3/5x -> 0/8/15/25/40.

If fewer than two peers exist or the median is non-positive, the neighbor component is unavailable. The Volume Share component remains on its fixed 60-point basis; it is not rescaled.

The total Same-Day Activity Score is the sum of available Volume Share and Neighbor points. Same-Day >=40 makes the expiry eligible for the `EXPIRY_ACTIVITY` route. DTE 91–180 can have a descriptive/share-only score but cannot enter v1.3 Deep Dive, which limits candidates to DTE <=90.

### Ranking and OPEX

The active v1.3 route order is:

1. `RADAR_EVENT`
2. `CONTRACT_PERSISTENCE` / `EXPIRY_PERSISTENCE`
3. `EXPIRY_ACTIVITY`
4. `STRUCTURAL_COLD_START`

Within the Expiry Activity route, rows sort by Same-Day score descending, then ticker and expiration ascending. Selection allows at most four tickers and three expiries per ticker. Current v1.3 code does not enforce one expiry per bucket, despite the older v1.2 documentation statement.

Monthly OPEX is an inferred third-Friday context label with score weight zero. It adds no bonus or penalty. Verified vendor expiration type can affect peer preference; the inferred OPEX label itself does not.

## F. 0DTE — Exact Baseline, Score and Ranking

### Baseline

- Same ticker only.
- Exactly the previous 20 `ZeroDteActivityDailySnapshot` observations.
- Query condition is `observation_date < current observation date`, excluding current from its own baseline.
- Weekends, holidays, and gaps do not add synthetic rows.
- A row is saved when a successful parsed `expiry_breakdown` contains a DTE-0 expiry for the current New York market date, Volume Share is available, and the ticker/date uniqueness key does not already exist.
- The current implementation uses New York `market_day`, not a vendor activity date, because `expiry_breakdown` lacks a verified usable activity date.

Fewer than 20 prior observations produces:

```text
same_day_activity_score = NULL
same_day_baseline_status = INSUFFICIENT
basis = 0
```

No raw Volume Share or raw cross-expiry neighbor substitute is used.

### Statistics and score

```text
mean = arithmetic mean(prior shares)
median = median(prior shares)
MAD = median(abs(prior share - median))
historical_percentile = count(prior share <= current share) / 20
```

Ties count at or below current.

If `MAD > 1e-9`:

```text
robust_deviation =
    (current_volume_share - median) / (1.4826 × MAD)
```

Robust-deviation points, maximum 70: <=1/1.5/2/3/4+ -> 0/15/30/50/70.

Historical-percentile points, maximum 30: <=70/80/90/95/100th -> 0/10/20/25/30.

```text
0DTE Same-Day Score =
    robust-deviation points + historical-percentile points
```

If `MAD <= 1e-9`, the robust component is unavailable and status becomes `READY_PERCENTILE_FALLBACK`. Only the fixed-scale 30-point percentile component remains; no rescaling occurs.

### Production participation

There is no separate production metric named 0DTE Participation Rank. The calibrated Same-Day score participates in the `EXPIRY_ACTIVITY` route when it is available and >=40. Its historical percentile is relative to the same ticker's own prior 20 sessions, not a cross-MAG7 rank. Global candidate ordering occurs only afterward through the v1.3 route selector.

Same-Day, Expiry Persistence, Contract Persistence, and Radar are independent routes in v1.3. There is no active averaging or v1.2 MAX/secondary-bonus combination for Deep Dive selection. A NULL 0DTE Same-Day score can still enter through qualifying Persistence. Structural Cold Start is independent and does not manufacture a score.

The v1.2 `discovery_with_confirmation()` result is still calculated, persisted, and returned by some backend summary endpoints, but it is a legacy side output rather than the active v1.3 selector.

### Dashboard

The backend `zero_dte_status` payload includes current volume, Volume Share, raw descriptive neighbor ratio, baseline count/required, mean, median, MAD, percentile, robust deviation, method, and calibrated score.

The current Next.js `Payload` type does not include `zero_dte_status`, so there is no dedicated 0DTE baseline/distribution panel. The Expiry Activity table shows score, Volume Share, raw Neighbor Ratio, component-point columns, score basis, and baseline status/count only for route-qualified rows.

Backend-only, not currently rendered: mean, median, MAD, historical percentile, robust deviation, method, and the explicit X/20 denominator.

Two presentation discrepancies exist:

1. `same_day_score_basis()` recognizes non-0DTE component keys only, so 0DTE VS Points, Neighbor Points, and Score Basis do not correctly explain the calibrated robust/percentile score.
2. API/UI `neighbor_ratio` is the persisted raw broad ratio, whereas Neighbor Points for non-0DTE are based on the stricter comparable-peer median. These may differ.

## G. Contract Positioning Structure — Exact Formula

### Components

1. Same-side expiry OI concentration, maximum 40

```text
contract_oi_share =
    contract current OI
    / total OI of all complete-chain contracts
      in the same expiry and same right
```

0.5/1/2/5/10/20% -> 0/5/12/22/32/40.

2. Neighbor-strike OI anomaly, maximum 30

The complete same-side strike ladder is sorted. Other contracts within ordinal distance two are used, allowing up to two neighbors on each side.

```text
neighbor_strike_ratio =
    contract OI / median(neighbor contract OI)
```

Missing or non-positive median makes this component unavailable. Anchors: 1.2/1.5/2/3/5x -> 0/5/10/18/30.

3. Liquidity quality, maximum 15

```text
mid = (bid + ask) / 2
spread_pct = (ask - bid) / mid
```

<=5/10/20/30/50% -> 15/13/10/6/2. Spread over 50% produces `SPREAD_OVER_50_PERCENT`. A partially supplied but unusable quote produces `UNUSABLE_QUOTE`. Both quotes missing makes the component unavailable without an automatic reject.

4. Delta/moneyness quality, maximum 15

| `abs(delta)` | Points |
|---|---:|
| <0.10 | 3 |
| 0.10–<0.20 | 7 |
| 0.20–<0.35 | 12 |
| 0.35–0.65 | 15 |
| >0.65–<0.80 | 12 |
| 0.80–<0.90 | 8 |
| >=0.90 | 6 |

`abs(delta) < 0.10` adds `LOTTO_RISK` but is not a hard rejection.

The Structure Score is the sum of available fixed-scale component points, without rescaling.

- <50 `IGNORE`
- 50–<65 `OBSERVE`
- 65–<75 `STRUCTURAL_CANDIDATE`
- 75–<85 `STRONG_STRUCTURE`
- >=85 `EXTREME_STRUCTURE`

`is_candidate = score >=65 AND no hard reject`.

There is no separate low-OI threshold. The score identifies contracts that are unusually concentrated inside the current complete same-expiry, same-right OI strike surface, while retaining liquidity and delta context. It is not a current-day unusual trading score and does not use Volume, Premium, ΔOI, historical Volume, or Intraday Burst.

It is persisted in `contract_scan_observations`, returned by Radar/Research Candidate/ticker-summary/Phase 2B APIs, displayed in Radar details and Research Candidates, and documented by the central glossary's Contract Positioning Structure entry.

## H. Cluster — Exact Formula

### Construction

- Members are Contract Structure candidates (`is_candidate = true`).
- Calls and Puts are always separated.
- Clusters stay within one expiry.
- The full same-side strike ladder defines adjacency.
- Consecutive candidate ladder index gap must be <=2.
- Group span from its first strike to a new member must be <=20% of spot when spot is available.
- With no spot, the span restriction is skipped.
- Minimum two contracts; no explicit maximum.

### Score

1. Constituent structural strength, maximum 30

```text
strength = Σ(structure_score × contract_oi) / Σ(contract_oi)
points = strength / 100 × 30
```

2. Same-side expiry OI concentration, maximum 35

```text
cluster_oi_share =
    Σ(cluster contract OI) / same-side expiry total OI
```

5/10/20/40/60% -> 0/5/12/22/35.

3. Strike coherence, maximum 25

- Two members: 12
- Three: 18
- Four or more: 25
- If any adjacent candidate pair has ladder index gap two, subtract 5.

4. Liquidity, maximum 10

```text
mean(available constituent liquidity points) / 15 × 10
```

All-liquidity-missing produces zero for this cluster component.

```text
Cluster Score = A + B + C + D
```

- >=80 `STRONG_CLUSTER`
- >=65 `VALID_CLUSTER`
- otherwise `INVALID_CLUSTER`

All formed groups, including invalid clusters, are persisted.

Premium and Volume do not participate and their legacy persistence fields are NULL. ΔOI/Persistence is descriptive context only: build/decline constituent counts, OI-weighted persistent score, and 3/5/10 net OI change sums.

Positioning center is OI-weighted strike, not Premium-weighted strike:

```text
Σ(strike × contract_oi) / Σ(contract_oi)
```

Shape is `TIGHT_CLUSTER` when span <=7.5% spot; otherwise `BROAD_CLUSTER`. Current positioning clusters do not produce `LADDER`.

`STRUCTURE_PRESENT` means a numeric structure score exists, even if classified IGNORE. `CLUSTER_PRESENT` means the exact contract ID appears in a persisted cluster's `source_contract_ids`; because invalid groups are persisted, it does not prove cluster score >=65.

The API exposes ticker-summary Call/Put cluster scores and exact Phase 2B membership. The current dashboard displays only Cluster presence inside candidate context, not a cluster table or score.

## I. Volume/OI Audit

`VOLUME_OI_NOT_USED_IN_PRODUCTION_SCORING`

Legacy `score_contract()` and the legacy scanner service calculate:

```text
volume / max(previous_oi, 1)
```

Legacy tests still cover this calculation, and the database model retains `volume_oi_ratio`. The active v11/v12/v13 structure scanner explicitly writes `volume`, `volume_oi_ratio`, estimated Premium, historical Volume abnormality, Intraday Burst, and legacy anomaly score as NULL.

Volume/OI is therefore neither a current discovery input nor a current score or dashboard metric. Its status is `IMPLEMENTED_BUT_NOT_CURRENTLY_ACTIVE / legacy`.

Current `LOW_OI_BASE` is a Radar risk flag when `previous_oi < 100`. It does not reject the event. There is no current Volume/OI cap, and low-OI/high-Volume contracts remain allowed if the independent Radar material gate passes.

The glossary still describes Volume/OI without clearly marking it as legacy.

## J. Radar — Exact Current Production Gate

- Capability: `options.oi_change`
- REST path: `/v1/options/oi-change/{ticker}`
- Collected by the Daily Radar Collector.
- Interactive scans reuse persisted Radar and do not request `oi-change`.
- The payload is a vendor-ranked changed-contract subset, not a complete OI universe.

The parser persists all rows in `data.contracts`; no fixed vendor row count is encoded. Runtime validation observed 50 NVDA rows, but 50 is not a guaranteed production contract.

Versioned material profile:

- ID: `radar_material_event`
- Version: `2026-08-13.v1`
- Minimum Premium: USD 150,000
- Minimum absolute ΔOI: 2,500

```text
material =
    premium_usd is not NULL
AND delta_oi is not NULL
AND premium_usd >= 150000
AND abs(delta_oi) >= 2500
```

The rule is AND. Relative OI Change is context only.

Scope after literal contract-symbol archive matching:

- no exact match -> `UNJOINED`
- outside DTE 0–180 -> `OUTSIDE_ARCHIVE_SCOPE`
- incomplete chain -> `INCOMPLETE_CHAIN`
- DTE 91–180 -> `LONG_DTE_RADAR_WATCH`
- complete DTE 0–90 -> `FULL_DEEP_DIVE_ELIGIBLE`

Only material, full-deep-dive rows qualify for the Radar route. Unmatched rows remain persisted and visible without fabricated expiry/right/strike/structure fields.

All parsed rows are retained. The API obtains each ticker's latest material date and sorts Premium descending, then absolute ΔOI descending. `latest_contract_events` contains 15; `all_material_contract_events` contains all material rows and the dashboard offers Inspect all. Vendor rank is display evidence, not the current primary sort key. Route selection uses the maximum Radar Premium per expiry and gives Radar the highest route priority.

Premium, Volume, Trades, previous/current OI, ΔOI, relative OI Change, price fields, and vendor rank together count as one `RADAR_EVENT` evidence family. Only Premium and absolute ΔOI form the material gate.

## K. Positioning Breadth

The five independent families are:

1. `RADAR_EVENT`
2. `CONTRACT_PERSISTENCE`
3. `EXPIRY_PERSISTENCE`
4. `STRUCTURE`
5. `CLUSTER`

Presence rules:

- Radar material event or Radar trigger -> PRESENT.
- Persistence numeric score -> PRESENT.
- Persistence score NULL with fewer than three valid observations -> `NOT_YET_AVAILABLE`.
- Other no-score persistence state -> ABSENT.
- Numeric structure score -> PRESENT.
- Exact cluster membership -> PRESENT.

```text
evidence_family_count = count(PRESENT families)

0 -> NO_EVIDENCE
1 -> SINGLE_EVIDENCE
>=2 -> MULTI_EVIDENCE
```

The actual field is `evidence_family_count`; no current field named `positioning_evidence_count` was found. Each family counts at most once. `MULTI_EVIDENCE` means evidence breadth only, not bullish/bearish direction, conviction, or a trade recommendation.

## L. Dashboard / API / zh-TW Field Guide Coverage

| Field | Backend | API | Dashboard | Glossary |
|---|---|---|---|---|
| Premium | ACTIVE Radar | YES | YES | YES |
| Volume | ACTIVE Radar/expiry | YES | Radar YES; raw expiry partial | YES |
| Trades | ACTIVE Radar | YES | YES | Radar context |
| Current OI | ACTIVE | YES | Radar details | YES |
| Previous OI | ACTIVE Radar | YES | Radar details | ΔOI context |
| ΔOI | ACTIVE Radar/persistence | YES | YES | YES |
| Relative OI Change | ACTIVE Radar context | YES | YES | YES |
| Contract Persistent Score | ACTIVE | YES | YES | YES |
| Expiry Persistent Score | ACTIVE | YES | Research Candidate/context only | Generic persistence entry |
| Winning persistence window | Contract + Expiry stored | Contract API only | Contract only | Formula described |
| Persistence history confidence | Contract + Expiry stored | Contract and ticker-summary expiry | Contract only | YES |
| Contract Structure Score | ACTIVE | YES | YES | YES |
| Cluster | ACTIVE | Summary + exact membership | Presence only | YES, partly stale |
| Positioning Evidence Breadth | ACTIVE Phase 2B state | YES | Candidate context | YES |
| Expiry Activity | ACTIVE | YES | YES | YES |
| Volume Share | ACTIVE | YES | YES | YES |
| Neighbor comparison | ACTIVE | PARTIAL/misleading raw ratio | PARTIAL | Present but formula incorrect |
| 0DTE calibrated score | ACTIVE | Full zero-DTE payload | Eligible route rows only | YES |
| 0DTE historical percentile | ACTIVE | YES | NO | YES |
| LOW_OI_BASE | ACTIVE Radar flag | `risk_flags` | Radar detail flags | YES |
| Volume/OI | Legacy only | NO | NO | YES, not marked legacy |

The backend response contains `results`, `distribution`, `top_expiries`, `zero_dte_status`, and `structural_cold_start`, but the current frontend Payload and component do not render these sections. The specification's claim that ticker maxima and the full cross-MAG7 distribution are visible therefore disagrees with the current frontend.

## M. Nightwatch REST vs MCP

Production Nightwatch transport uses a server-side `httpx.AsyncClient`:

- Default base URL is `https://api.yehangshe.com`.
- API key is held as Pydantic `SecretStr`.
- Authorization is attached only by backend transport.
- Transport, parsers, raw ingestion, normalized persistence, analytics, and routes are separated.
- Browser requests use Next.js backend proxies such as `/api/mag7-scan`; the browser does not call Nightwatch directly.

Repository-wide inspection found no MCP client dependency, `mcpServers` configuration, Model Context Protocol package, Nightwatch MCP invocation, frontend integration, or documentation-only Nightwatch MCP reference.

Final classification:

`NIGHTWATCH_MCP_NOT_PRESENT`

## N. Handoff Corrections

A future handoff must not claim that:

1. Contract Persistence uses OI Share Change. It uses Absolute OI Growth, Absolute Build Share, and Directional Persistence.
2. Persistence requires every OI observation to increase. It measures the share of transitions matching the window's net direction.
3. Persistent decline cannot score positively. Decline magnitude and consistent negative transitions are scored symmetrically.
4. Persistence windows are calendar days. They are valid observation counts.
5. Missing OI is filled with zero. Missing dates/contracts remain missing; first-observation prior OI is NULL.
6. Volume/OI is current production scoring. It is legacy, and active scans persist it as NULL.
7. Contract Anomaly Score is the current score. It was replaced by Contract Positioning Structure Score.
8. Neighbor-strike anomaly is a separate production anomaly. It is one Structure component.
9. Current clusters use Volume or Premium. They use Structure, OI concentration, coherence, and liquidity.
10. Positioning center is Premium-weighted. It is OI-weighted.
11. `CLUSTER_PRESENT` guarantees cluster score >=65. Invalid persisted groups also create exact membership.
12. `STRUCTURE_PRESENT` guarantees a structural candidate. Any numeric structure score counts as present.
13. Radar is the complete contract universe. It is a vendor-ranked changed-contract subset.
14. Radar fields count as multiple breadth families. They collectively count once as `RADAR_EVENT`.
15. `MULTI_EVIDENCE` means direction or conviction. It means breadth only.
16. The 0DTE percentile is a cross-MAG7 rank. It is same-ticker prior-20 empirical rank.
17. Raw 0DTE Neighbor Ratio affects scoring. Its weight is zero.
18. The v1.2 Discovery MAX/bonus is the active deep-dive selector. v1.3 uses route priority.
19. The dashboard renders the complete summary, distribution, or 0DTE baseline. These currently exist only in backend payloads.
20. UI Neighbor Ratio is necessarily the scored comparator. It is the persisted raw broad ratio, while points use strict peers.
21. Monthly OPEX changes score. It is a zero-weight context label.
22. Current v1.3 enforces one selected expiry per bucket. The code only limits each ticker to three expiries.
23. `expiry_breakdown` vendor date is used for activity DTE. Current code uses New York market date.
24. Every glossary field describes current production behavior. Several entries remain legacy or inaccurate.
25. Signal Decay is implemented or specified. It is intentionally excluded; ordinary freshness must not be renamed Signal Decay.

## O. Source Evidence Index

| Conclusion | Source |
|---|---|
| Current v1.3 authority | `backend/app/scanner/config.py:6`, `backend/app/scanner/v13.py:194` |
| CLI/API active scanner | `backend/app/cli.py:148`, `backend/app/api/routes/scans.py:60` |
| Persistence windows/features | `backend/app/scanner/history.py:10-80` |
| Expiry persistence | `backend/app/scanner/history.py:83-124` |
| Contract persistence | `backend/app/scanner/history.py:127-179` |
| Anchors and thresholds | `backend/app/scanner/config.py:40-69` |
| Piecewise/null ratio behavior | `backend/app/scanner/scoring.py:13-28` |
| Daily archive validity | `backend/app/scanner/archive.py:139-301` |
| Append-only OI tables | `backend/app/db/models.py:503-567` |
| Same-Day/0DTE materialization | `backend/app/scanner/v12.py:100-283` |
| 0DTE statistics | `backend/app/scanner/scoring.py:319-406` |
| Comparable peers | `backend/app/scanner/scoring.py:409-462` |
| Legacy Discovery formula | `backend/app/scanner/scoring.py:465-490` |
| Active three-route selection | `backend/app/scanner/v13.py:205-363` |
| Structure calculation | `backend/app/scanner/v11.py:430-529`, `backend/app/scanner/scoring.py:493-578` |
| Current legacy fields set NULL | `backend/app/scanner/v11.py:490-505` |
| Cluster algorithm | `backend/app/scanner/clusters.py:191-295` |
| Cluster persistence | `backend/app/scanner/v11.py:556-592` |
| Radar material gate | `backend/app/scanner/v13.py:82-114`, `backend/app/config/settings.py:42-47` |
| Radar daily collection | `backend/app/scanner/daily.py:427-494` |
| Interactive Radar reuse | `backend/app/scanner/v13.py:365-409` |
| Positioning breadth | `backend/app/confirmation/state_v2.py:173-235` |
| Exact cluster membership | `backend/app/confirmation/state_v2.py:462-474` |
| Main scanner API fields | `backend/app/api/routes/scans.py:138-205` |
| Radar/activity API serializers | `backend/app/api/routes/scans.py:323-404` |
| Current dashboard rendering | `frontend/app/scan-dashboard.tsx:245-339` |
| Central zh-TW glossary | `frontend/app/fieldGlossary.zh-TW.ts:17-164` |
| Specification statement | `docs/specifications/SIGNAL_SPECIFICATION_V1.md:14-31` |
| REST transport | `backend/app/nightwatch/client.py:29-188` |

## P. Final Safety State

- Nightwatch calls: `0`
- External HTTP/API calls: `0`
- Database reads: `0`
- Database writes: `0`
- Scans executed: `0`
- Daily OI Archive runs: `0`
- Dealer/GEX archive runs: `0`
- GitHub Actions runs: `0`
- Repository files modified during the original read-only verification: `0`
- Staged files: `0`
- Commits: `0`
- Pushes: `0`
- Branch changes: `0`
- Ending HEAD: `1e29c92956b39f005dab0c4eb163150ee12a0c9d`
- Ending read-only verification state: the same pre-existing untracked closeout file remained; tracked files were unchanged.

This Markdown evidence file was subsequently created only because the user explicitly requested that the chat report be saved for download. It does not modify production behavior.
