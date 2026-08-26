# Candidate Forward Outcome Data Availability / Design Gate — 2026-08-15

## 1. Executive conclusion

**Gate result: CONDITIONAL PASS.**

```text
EVENT-DATE / EVENT-RESPONSE OUTCOMES
= DATA FOUNDATION AVAILABLE

DECISION-TIME / ACTIONABILITY OUTCOMES
= NOT READY

SECOND DAILY SCHEDULER
= NOT REQUIRED
```

The current repository and preserved data can support a direction-neutral research dataset for:

- T+1 regular-session Close Return;
- T+3 regular-session Close Return;
- T+5 regular-session Close Return;
- Maximum Upside Excursion over an explicitly defined future-session window;
- Maximum Downside Excursion over an explicitly defined future-session window.

Nightwatch daily OHLC already supplies `trading_date`, regular-session Open/High/Low/Close, explicit session labels, and enough recent history to backfill the project's current August 2026 candidate dates after each horizon matures. One OHLC response can be reused across every due candidate for the same ticker.

The project does **not** yet persist one unified candidate-event record containing both an authoritative event date and an authoritative system knowledge timestamp/reference price. Current candidate times are distributed across Radar, scan, expiry, contract, and Phase 2B tables. Therefore an event-date study can answer:

> What happened to the underlying after the dated anomaly/activity event?

but it must not be presented as:

> What return was available from the instant the system knew and could act?

The latter requires a separately specified decision-time anchor and broader prospective price capture.

No outcome model, threshold, database object, scheduler, API route, production signal, or dashboard element was implemented in this gate.

## 2. Scope and authority

The handoff explicitly identifies this task as the next approved substantive task and requires a diagnostic/design gate before implementation. It asks:

1. which candidate detection timestamps are persisted;
2. whether a reliable detection/reference price is persisted;
3. whether OHLC can reconstruct T+1/T+3/T+5 close returns;
4. whether OHLC can reconstruct maximum upside/downside;
5. which outcomes are fully backfillable;
6. which useful inputs are not backfillable;
7. whether another scheduler is necessary;
8. the API/quota cost of each design option.

This report answers those questions without changing Phase 2A v1.3, Phase 2B v3.1, Dealer/GEX accumulation, non-directional semantics, or production behavior.

## 3. Repository preflight

| Item | Value |
|---|---|
| Branch | `main` |
| HEAD / locally known `origin/main` | `1e29c92956b39f005dab0c4eb163150ee12a0c9d` |
| Database migration version | `20260815_0013` |
| Tracked modifications before this gate | none |
| Staged changes | none |
| Pre-existing untracked evidence files | three; preserved and not modified |

The three pre-existing files were:

- `docs/evidence/NIGHTWATCH_EXACT_CONTRACT_AGGRESSOR_FLOW_INTENT_CAPABILITY_GATE_20260815.md`;
- `docs/evidence/PHASE2A_SIGNAL_ANATOMY_READ_ONLY_HANDOFF_VERIFICATION_20260815.md`;
- `docs/evidence/PHASE2B_V31_FIRST_REAL_GITHUB_SCHEDULED_RUN_CLOSEOUT_20260815.md`.

## 4. Read-only database validation

Two successful database connections were used. Each transaction executed:

```sql
SET TRANSACTION READ ONLY
```

and was rolled back after aggregate/safe-summary reads. No insert, update, delete, DDL, migration, or commit occurred. One initial sandboxed connection attempt was denied before reaching the database.

No Nightwatch endpoint or other HTTP API was contacted during this gate.

## 5. Current candidate evidence surfaces

There is no single authoritative `candidate_events` table today. Candidate-related facts are spread across several immutable or append-only surfaces.

### 5.1 `scan_runs`

Available fields:

- UTC `started_at` and `completed_at`;
- New York `market_date`;
- specification version;
- run status and configuration evidence.

Observed database coverage:

| Metric | Value |
|---|---:|
| Scan runs | 6 |
| Completed rows | 6 |
| First started | 2026-08-11 17:01:13 UTC |
| Last started | 2026-08-13 06:50:39 UTC |
| Market-date range | 2026-08-11 through 2026-08-13 |

Run time is a system execution time, not automatically the vendor activity/event time.

### 5.2 Radar exact-contract events

`oi_change_radar_observations` preserves:

- exact contract symbol and ticker;
- vendor `observation_date` and `previous_date`;
- UTC `captured_at`;
- New York `ny_market_date`;
- threshold profile/config identity;
- material/deep-dive eligibility;
- immutable Radar evidence.

Observed coverage:

| Metric | Value |
|---|---:|
| Rows | 550 |
| Distinct exact contracts | 479 |
| Tickers | 7 |
| Deep-dive eligible rows | 88 |
| Eligible rows with `captured_at` | 88 / 88 |
| Eligible rows with `ny_market_date` | 88 / 88 |
| Vendor observation dates | 2026-08-11 and 2026-08-12 |

The 88 eligible rows collapse to nine ticker/event-date groups. All were captured on 2026-08-13 UTC. This proves that event/activity date and system knowledge/capture time are distinct facts and cannot be represented by one generic `detected_at` without losing semantics.

### 5.3 Phase 2A expiry route candidates

`expiry_observations` preserves:

- ticker + expiration + scan-run identity;
- UTC `observed_at`;
- DTE and bucket at detection;
- independent route flags and ordered trigger sources;
- `deep_dive_eligible`;
- `selected_for_deep_scan`.

The accepted v1.3 run produced:

| Metric | Value |
|---|---:|
| Route-eligible expiries | 26 |
| Actually selected ticker/expiry pairs | 10 |
| Trigger composition | 8 Expiry Activity only; 8 Structural Cold Start only; 6 Radar + Expiry Activity; 3 Radar only; 1 Expiry Activity + Structural Cold Start |

`deep_dive_eligible` and `selected_for_deep_scan` answer different questions. A research cohort must state which one it uses; it must not silently treat all eligible expiries as the finite selected Deep Dive cohort.

### 5.4 Phase 2A exact-contract candidates

`contract_scan_observations` preserves exact contract, ticker, expiration, right, strike, UTC `observed_at`, DTE/bucket at detection, evidence, trigger sources, and `deep_dive_eligible`.

Observed v1.3 result:

| Metric | Value |
|---|---:|
| Deep-dive eligible contract rows | 17 |
| With `observed_at` | 17 / 17 |
| Ticker distribution | AAPL 4; AMZN 4; NVDA 5; TSLA 4 |

These rows are not a substitute for expiry candidates. The system intentionally has different evidence entities and routes.

### 5.5 Phase 2B candidate evaluations

`phase2b_candidate_evaluations` preserves precise UTC `evaluated_at`, source timestamps, contract identity, source evidence, and `direction=UNRESOLVED`.

Observed coverage:

| Metric | Value |
|---|---:|
| Evaluations | 4 |
| Distinct contracts | 2 |
| Distinct tickers | 2 |
| `UNRESOLVED` | 4 / 4 |

The same NVDA contract was evaluated more than once. Phase 2B is manually/explicitly materialized and is not a complete candidate registry. `evaluated_at` is therefore a context-evaluation timestamp, not the universal Phase 2A detection time.

### 5.6 Future `signal_detections` surface

The foundational `signal_detections` table exists and has append-only detection fields, but contains zero rows. Its explicit columns do not include exact contract symbol, route identity, knowledge/event date separation, reference price, or outcome-spec identity.

It is not current outcome authority and should not be silently populated under an undefined contract.

## 6. Candidate time semantics

The minimum no-lookahead design requires separate names for separate facts:

| Time/date | Meaning | Current source |
|---|---|---|
| `event_date` | Date represented by the vendor evidence/activity observation | Radar `observation_date`; daily activity `observation_date` / `vendor_date`; OI archive `vendor_oi_date` |
| `knowledge_at` | First UTC time this system persisted or derived eligibility from the evidence | Radar `captured_at`; scan/row `observed_at`; raw `received_at` |
| `selection_at` | Time a finite scan selection was made | scan run/selected row times |
| `context_evaluated_at` | Time Phase 2B context was materialized | `phase2b_candidate_evaluations.evaluated_at` |
| `price_as_of` | Vendor time for the proposed reference price | Stock State `as_of`, chain `underlying_as_of`, or daily bar boundary |

These must not be collapsed into one timestamp.

### Concrete evidence

Radar events dated 2026-08-11 and 2026-08-12 were captured on 2026-08-13. The accepted v1.3 scan itself ran around 02:50 America/New_York on 2026-08-13, before the regular session.

Using the 2026-08-13 closing price as a “detection price” for that premarket scan would look ahead through the entire 2026-08-13 session. That is not allowed.

## 7. Current reference-price candidates

### 7.1 Phase 2B Stock State

Nine of nine ticker context snapshots preserved `current_price_usd` plus vendor `as_of` and session. Examples include premarket and postmarket observations.

Strengths:

- precise vendor timestamp;
- contemporaneous snapshot;
- session label retained.

Limitations:

- available only where Phase 2B was explicitly run;
- not persisted for all 26 expiry candidates or all 88 Radar events;
- premarket/postmarket snapshot is not automatically a regular-session executable price;
- repeated Phase 2B evaluation is not the canonical initial knowledge time.

Conclusion: useful prospective evidence, not a universal backfillable reference.

### 7.2 Phase 2B latest regular close

Eight of nine ticker contexts contained a normalized latest regular close. The initial NVDA context lacked the later canonical fields, while the preserved raw payload allowed a later reprocessing path to calculate them.

Strengths:

- stable session-close reference;
- raw OHLC is preserved and reproducible;
- can be backfilled for recent events.

Limitations:

- “latest” can refer to the last completed session before a premarket detection;
- it is not always the same as event date or knowledge date;
- split-adjustment semantics are unconfirmed.

### 7.3 Archived option-chain underlying price

`contract_oi_daily_snapshots` preserves `underlying_price` and `underlying_as_of`.

Strengths:

- already bound to exact archived contract evidence;
- source time preserved.

Limitations:

- unavailable for unjoined/incomplete/out-of-scope Radar rows and expiry-only candidates;
- can be temporally older than the eligibility decision;
- must not overwrite or stand in for a later Stock State price.

### Conclusion

```text
Reliable universal detection-time price persisted?
NO

Reliable recent event-date regular close backfillable?
YES, subject to session/date and adjustment controls
```

## 8. Preserved daily OHLC availability

The current Phase 2B source is:

```text
GET /v1/stocks/ohlc/{ticker}?candle_size=1d
```

Existing evidence documents weight 1 per ticker and no date-range/pagination parameter. A response returns the newest 400 rows from a larger source set and is marked truncated.

Current database inventory:

| Metric | Value |
|---|---:|
| Preserved raw daily-OHLC payloads | 6 |
| Tickers | AAPL, AMZN, GOOGL, META, NVDA, TSLA |
| Missing MAG7 ticker | MSFT |
| Rows per payload | 400 |
| Source total | 755–757 bars |
| Valid regular-session dates | 133–134 per ticker |
| Duplicate regular rows per date | 0 |
| Regular-date range | approximately 2026-02-02/03 through 2026-08-12/13 |

Each raw payload contains:

- `trading_date`;
- `bar_start` and `bar_end`;
- `session`;
- `open_usd`, `high_usd`, `low_usd`, `close_usd`;
- Volume fields;
- vendor `as_of` and truncation/count metadata.

The repository already has a canonical parser that keeps exactly one `session=regular` row per trading date and surfaces missing/ambiguous dates instead of converting them to zero.

## 9. Current outcome maturity and stored coverage

For the nine existing Radar ticker/event-date groups:

| Stored condition | Groups |
|---|---:|
| Event-date regular close present | 9 / 9 |
| At least one future regular session present | 6 / 9 |
| At least three future regular sessions present | 0 / 9 |
| At least five future regular sessions present | 0 / 9 |

This does not mean T+3/T+5 is unavailable from the vendor. It means the raw payloads already preserved in this database were captured before those horizons matured or before a later OHLC refresh.

As of 2026-08-15, no 2026-08-11 or 2026-08-12 candidate has matured through five subsequent XNYS sessions. T+5 outcomes must remain `PENDING`, not zero and not missing-as-failure.

## 10. Trading-session indexing

T+1, T+3, and T+5 must mean valid XNYS trading sessions, not calendar days and not host-local dates.

The repository already depends on `exchange_calendars` and uses the authoritative `XNYS` calendar for Dealer/GEX scheduling. Forward outcomes can reuse that calendar in a later implementation.

Required rules:

- New York session date is authoritative;
- persisted timestamps remain UTC;
- holidays and weekends do not consume a horizon;
- early closes remain valid sessions;
- missing or duplicate regular OHLC rows make the affected outcome unavailable/partial;
- a horizon remains pending until its Nth valid future session exists.

## 11. Direction-neutral metric contract — proposed for later specification

Current candidate direction is `UNRESOLVED`. Do not name these values favorable/adverse MFE/MAE.

For an explicitly approved reference price `P_ref` and Nth future valid session:

```text
Close Return N
= Close(T+N) / P_ref - 1
```

For a separately declared window of future valid sessions from T+1 through T+N:

```text
Maximum Upside Excursion N
= max(High[T+1 ... T+N]) / P_ref - 1

Maximum Downside Excursion N
= min(Low[T+1 ... T+N]) / P_ref - 1
```

These are transparent candidate definitions for the future specification, not production formulas implemented by this gate. No threshold, weight, label, win/loss rule, or composite score is proposed.

The handoff names Maximum Upside and Maximum Downside without a horizon. The future specification must either persist them for each approved horizon or explicitly name a single window. It must not hide an unstated window in code.

## 12. Two research modes that must remain separate

### 12.1 Event-response research — conditionally ready

Purpose:

> What happened to the underlying after the dated anomaly/activity event?

Recommended initial reference semantics:

- `event_date` comes from authoritative vendor evidence, not scan host date;
- `P_ref` is the canonical regular-session close on that event date;
- future sessions begin strictly after `event_date`.

This is retrospectively backfillable for recent candidate dates and suitable for research into post-event behavior. It is not an executable-entry claim because the system may have learned the event later.

### 12.2 Decision-time / actionability research — not ready

Purpose:

> What happened after the system knew the candidate and a defined reference price became available?

This requires:

- canonical `knowledge_at` per candidate event;
- a rule for the first eligible price at or after knowledge time;
- explicit handling for premarket, regular, postmarket, and stale snapshots;
- broader prospective preservation of that price for every candidate;
- an execution/availability interpretation that is not implied by OHLC alone.

Daily Open may be usable when knowledge occurred before that session opened, but it would be invalid when knowledge occurred after the Open. Stock State can be contemporaneous but is not systematically preserved. This mode remains a separate future design gate.

## 13. Route-specific event-date mapping

The initial event-response cohort must preserve route semantics:

| Route/entity | Candidate event date | Current feasibility |
|---|---|---|
| Exact-contract Radar | `oi_change_radar_observations.observation_date` | authoritative and backfillable |
| Expiry Activity | daily activity `observation_date` / vendor date tied through preserved source evidence | feasible, but `expiry_observations` itself does not copy a dedicated activity date |
| Expiry Persistence | winning observation's vendor OI date | feasible from OI history; must not use scan date blindly |
| Contract Persistence | exact contract vendor OI observation date | feasible from contract archive; must preserve winning observation/source |
| Structural Cold Start | underlying chain/OI observation date plus scan knowledge time | feasible only after explicit source-date mapping |

Do not combine these routes under one guessed `market_date`. Rows whose authoritative event date cannot be resolved should be `EVENT_DATE_UNRESOLVED` and excluded from numeric outcomes until repaired from preserved evidence.

## 14. Cohort identity and repeated observations

One ticker can produce multiple contracts and expiries on the same event date. Their underlying forward returns will be identical when they share the same ticker/date/reference policy.

Naively treating each contract as an independent market outcome would inflate sample size.

A future dataset should preserve both:

- candidate-level rows, so option evidence remains traceable; and
- `ticker + event_date + reference_policy` grouping, so later empirical analysis can cluster/deduplicate market outcomes appropriately.

The cohort must also retain:

- source table and immutable source row ID;
- candidate entity level (`CONTRACT`, `EXPIRY`, or other explicit type);
- specification/config versions effective at detection;
- eligibility versus selected status;
- trigger sources;
- historical DTE/bucket;
- scan status and evidence completeness.

## 15. Backfill classification

| Outcome/input | Classification | Reason |
|---|---|---|
| Current recent Radar event-date reference close | `FULLY_BACKFILLABLE` | all nine ticker/date groups have stored regular close |
| T+1/T+3/T+5 regular Close | `BACKFILLABLE_WHEN_MATURE` | daily OHLC has exact session dates and close; current stored payloads simply predate full maturity |
| Maximum Upside/Downside using daily High/Low | `BACKFILLABLE_WHEN_MATURE` | regular OHLC includes high/low |
| Current v1.3 selected expiry cohort | `PARTIALLY_BACKFILLABLE` | event-date mapping must be resolved per route; MSFT raw OHLC is absent but can be fetched |
| Detection-time Stock State for every candidate | `NOT_BACKFILLABLE_FROM_CURRENT_ARCHIVE` | Phase 2B snapshot was not run for every candidate |
| Exact intraday path after detection | `NOT_BACKFILLABLE_FROM_CURRENT_ARCHIVE` | hourly/minute history is bounded and not systematically preserved |
| Split-adjusted return | `SEMANTICS_UNCONFIRMED` | vendor OHLC split-adjustment contract is not documented |
| Total return including dividends | `NOT_CURRENTLY_DESIGNED` | current metric request is price outcome; dividend treatment is not specified |
| Favorable/adverse MFE/MAE | `NOT_APPLICABLE_YET` | candidate direction remains unresolved |

## 16. Corporate-action and data-quality controls

Before empirical calibration:

- obtain or validate split-adjustment semantics;
- retain raw OHLC and its checksum/provenance;
- flag candidate windows crossing splits until adjustment is authoritative;
- label Close Return as price return, not total shareholder return;
- do not forward-fill missing High/Low/Close;
- do not substitute extended-hours rows for missing regular-session rows;
- preserve vendor revisions as separate evidence rather than silently rewriting prior outcomes.

## 17. API / quota design options

Nightwatch `stocks.ohlc` is documented/observed at weight 1 per ticker.

### Option A — reuse preserved raw OHLC

```text
Incremental paid units: 0
```

Use when the stored response already includes the reference date and all matured horizon dates.

### Option B — due-only batch refresh

Fetch one `1d` OHLC response per distinct ticker with at least one due outcome, then compute every due candidate for that ticker.

```text
Cost per batch = number of distinct due tickers
```

Maximum illustrative costs if every ticker is due:

| Universe | Paid units per batch |
|---|---:|
| Current MAG7 | 7 |
| 50 tickers | 50 |
| 75 tickers | 75 |
| 100 tickers | 100 |

These are transport costs, not approved scheduler frequencies.

### Option C — reuse a later Phase 2B context payload

When a later context refresh already fetched OHLC spanning the matured horizon:

```text
Incremental outcome paid units: 0
```

This is opportunistic and not complete because Phase 2B refreshes are candidate-driven.

### Option D — fetch every ticker every trading day

This would cost the full universe size each session and is not required for T+5 daily outcomes. The current endpoint retains roughly 133–134 regular dates inside the returned 400 mixed-session rows, providing ample time for a due-only catch-up before recent outcomes roll out.

## 18. Scheduler decision

```text
Is another daily scheduler actually necessary?
NO
```

A second scheduler is not justified merely to calculate forward outcomes.

Conceptual future choices, in priority order:

1. reuse preserved OHLC whenever it spans the matured horizon;
2. run a due-only/manual backfill during initial research;
3. if operational automation is later approved, add a due-only subjob to an existing durable daily workflow rather than create an independent scheduler;
4. fetch once per distinct due ticker, not once per candidate or horizon.

No scheduler change was made here.

## 19. Minimum future persistence design — not implemented

### 19.1 Immutable candidate-event registry

Conceptually preserve:

- source table/source row identity;
- entity type and exact contract/expiry identity where applicable;
- ticker;
- event date;
- knowledge timestamp;
- selection timestamp/status;
- route/trigger sources;
- historical DTE/bucket;
- specification/config versions;
- evidence completeness and raw provenance.

### 19.2 Canonical underlying daily price evidence

Conceptually preserve one immutable/revision-aware regular-session bar per:

```text
ticker + trading_date + vendor/source version
```

including OHLC, session, vendor as-of, UTC capture time, raw payload reference, adjustment semantics, and quality state.

### 19.3 Versioned outcome rows

Conceptually key rows by:

```text
candidate_event + outcome_specification_version + reference_policy + horizon
```

and preserve reference date/price, target date/close, future window High/Low evidence, maturity/quality state, input bar identities, calculation time, and reproducibility metadata.

Pending, unavailable, ambiguous, and mature outcomes must be different states. Missing is never zero.

## 20. No-lookahead checklist

A future implementation must reject or quarantine any row that violates these controls:

- candidate feature evidence is limited to what was available at `knowledge_at`;
- event-date and knowledge-time studies are never mixed in one unlabeled cohort;
- reference policy is explicit and versioned;
- T+N counts XNYS sessions strictly after the anchor date;
- future OHLC bars are used only as outcomes, never retroactively added to detection features;
- historical DTE/bucket and trigger sources are immutable;
- a later candidate re-evaluation does not overwrite the original event;
- duplicate candidates sharing the same ticker/date outcome are statistically grouped;
- incomplete/failed scan evidence remains labeled;
- raw source evidence and exact formula inputs remain traceable.

## 21. Final answers to the handoff questions

### 1. What candidate detection timestamps are already persisted?

Several useful timestamps are persisted (`captured_at`, `observed_at`, scan start/complete, Phase 2B `evaluated_at`), but no single unified candidate knowledge timestamp exists across every route.

### 2. Is a reliable detection/reference price persisted?

Not universally. Stock State and chain spot exist for subsets. Recent event-date regular Close is backfillable and reproducible, but is not automatically a decision-time price.

### 3. Can historical OHLC reconstruct T+1/T+3/T+5 Close Return?

Yes for an explicitly approved event-date/reference policy, after the horizon matures and subject to canonical regular-session and corporate-action controls.

### 4. Can historical OHLC reconstruct Maximum Upside/Downside?

Yes from future regular-session High/Low over a declared horizon. The horizon must be specified; the values remain direction-neutral.

### 5. Which outcomes are fully backfillable?

Recent event-date reference Close is already backfillable. T+N Close and maximum upside/downside are backfillable when mature while the dates remain inside the OHLC response/archive window.

### 6. Which useful inputs are not backfillable?

Universal detection-time Stock State, exact post-detection intraday path, authoritative split-adjusted semantics, and decision-time executable price are not available for every historical candidate.

### 7. Is another daily scheduler necessary?

No.

### 8. What is the API/quota cost?

Zero when preserved raw spans the horizon; otherwise one paid unit per distinct ticker refreshed. It is not one call per candidate or per horizon.

## 22. Gate decision

```text
Candidate Forward Outcome — Event-Date Data Availability:
PASS, CONDITIONAL ON EXPLICIT SOURCE-DATE/REFERENCE POLICY

Candidate Forward Outcome — Current Stored T+5 Maturity:
NOT YET MATURE

Candidate Forward Outcome — Decision-Time / Actionability:
NOT READY

New Daily Scheduler:
NOT REQUIRED

Production changes:
0

Database changes:
0

Nightwatch requests during this gate:
0

Paid Nightwatch units during this gate:
0
```

## 23. External contact ledger

No external HTTP URL or API endpoint was contacted.

The configured Supabase/PostgreSQL database was contacted through its existing server-side DSN for two successful read-only transactions. Credentials and the full DSN are intentionally not printed. One sandboxed connection attempt failed before reaching the database. Both successful transactions were explicitly read-only and rolled back.

## 24. Repository verification

Completed after this documentation-only report was written:

- backend: `python -m pytest -p no:cacheprovider` from `backend/` -> **273 passed**;
- frontend lint: `npm run lint` from `frontend/` -> **passed**;
- frontend production build: `npm run build` from `frontend/` -> **passed** (Next.js production build, TypeScript, and static generation);
- automated tests used repository fixtures/mocks; no live Nightwatch request was made;
- final repository review: no tracked diff and no staged diff; this report plus three pre-existing evidence reports remain untracked. No build artifact created a tracked change.

## 25. Next step only

After the earliest current cohort has actually matured through T+5, approve one **zero-write retrospective prototype** that:

1. uses only preserved candidate and raw OHLC evidence;
2. starts with one clearly named event-date cohort, preferably exact-contract Radar;
3. produces candidate-level plus ticker/event-date grouped T+1/T+3/T+5 and maximum-up/down diagnostics;
4. demonstrates all no-lookahead and maturity states;
5. does not create a production table, scheduler, threshold, score, or Actionability label.

The separate decision-time reference-price design should wait until the founder decides whether the research target is post-event behavior or realistically actionable post-detection behavior.
