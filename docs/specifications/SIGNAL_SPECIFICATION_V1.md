# Signal Specification — Phase 2A

Current immutable version: `signal_spec_v1.3_phase2a`

Historical version `signal_spec_v1.0_phase2a` remains attached to its existing scan records and is
never recalculated in place. Version `signal_spec_v1.1_phase2a` also remains immutable. Phase 2A v1.2 describes activity and OI positioning structure. It does
not infer opening buyers, investor direction, BUY/SELL, GEX trading logic, lifecycle, Tradeability,
or any Phase 2B signal.

## v1.2 → v1.3 three-route amendment

v1.3 retains all accepted v1.2 Same-Day and Persistent formulas but removes the universal Discovery
Score from the primary workflow. Radar Event, Persistent Positioning, and Expiry Activity are
independent routes. Accepted v1.0, v1.1, and v1.2 rows remain immutable.

The initial Radar profile uses minimum aggregate Premium USD 150,000 and minimum absolute OI
difference 2,500. Both values live only in runtime/versioned configuration and are supplied to the
eligibility evaluator; the evaluator contains neither value. The 2,500 value is a rounded
calibration from the Pre-v1.3 diagnostic p75 absolute OI Diff of approximately 2,648, not a universal
market truth. Review it after at least 20 distinct valid Radar sessions. Each event and run retains
the effective profile ID, version, values, and configuration hash, so later profile activation cannot
rewrite historical eligibility and future profile shapes need no schema redesign.

Relative OI Change is context only. Exact Radar/archive matching does not parse OSI. Exact complete
0–90 DTE matches may enter Deep Dive; 91–180 DTE is `LONG_DTE_RADAR_WATCH`; unmatched/incomplete
evidence remains visible without fabricated structure. Monthly OPEX inference and Same-Day Score
Basis have weight zero. No Phase 2B behavior is introduced.

## v1.0 → v1.1 amendment

Runtime validation proved that expiry breakdown has total volume/OI but no per-expiry Call/Put
volume, while chain snapshot has complete contract OI/quotes/Greeks but no contract volume or last.
Therefore v1.1:

- replaces `volume-oi-per-expiry` discovery with separate `expiry-breakdown` activity and archived
  `oi-per-expiry` positioning;
- removes per-expiry Volume Skew from discovery;
- separates Same-Day Activity and Persistent Positioning and selects by their maximum;
- adds append-only daily expiry and complete-chain OI history over 0–180 DTE;
- replaces Contract Anomaly Score with Contract Positioning Structure Score;
- removes Contract Volume/OI, premium, historical volume, and Intraday Burst scoring;
- turns `oi-change` into supplemental OI Change Radar evidence only;
- replaces volume/premium clusters with same-right OI-positioning clusters.

## v1.1 → v1.2 calibration amendment

The controlled v1.1 run demonstrated that a broad cross-expiry comparator made all seven ticker
maxima DTE 0 and saturated every Neighbor component. Version 1.2 therefore:

- stores one valid DTE-0 activity snapshot per ticker/vendor activity date;
- sets DTE-0 Same-Day to null until 20 prior valid DTE-0 observations exist;
- scores ready DTE-0 observations against their own prior-20 median/MAD and empirical percentile;
- retains the raw cross-expiry neighbor ratio for DTE-0 diagnostics at scoring weight zero;
- restricts nonzero-DTE peers by bucket, DTE distance, type preference, maximum four and minimum two;
- replaces max-only Discovery with primary score plus a 0/3/6/10 confirmation bonus;
- adds Discovery Evidence Breadth while leaving underlying eligibility thresholds unchanged;
- makes ticker maxima and the full cross-MAG7 distribution independently visible.

No v1.0 or v1.1 scan is rewritten.

## Universe, dates, and tenor

The configuration-driven universe remains AAPL, MSFT, NVDA, AMZN, META, GOOGL, TSLA. Market scan
DTE uses `America/New_York`. Daily archive history uses Nightwatch `vendor_oi_date`/`as_of`; job time
never manufactures an OI date. Buckets are VERY_SHORT 0–7, SHORT 8–30, MEDIUM 31–90, LONG 91–180.
Daily history includes all four buckets; deep candidate analysis uses only 0–90 DTE.

## Daily expiry positioning

`oi-per-expiry` supplies Call OI and Put OI. For each ticker's 0–180 surface:

- `total_oi = call_oi + put_oi`;
- `total_oi_share = expiry_total_oi / ticker_total_oi`;
- `call_oi_share = expiry_call_oi / ticker_call_oi`;
- `put_oi_share = expiry_put_oi / ticker_put_oi`;
- `oi_skew = (call_oi - put_oi) / total_oi`.

Zero denominators yield null. OI Skew is context, never investor direction.

Across distinct valid OI observation sessions, 3/5/10-window features are net OI change, OI growth,
total/Call/Put OI-share change, positive/negative interval counts, and build/decline persistence.
Share changes are percentage-point differences: 8% → 24% is +16pp. Missing window history is null.
Confidence is `<3 INSUFFICIENT`, `3–4 LOW`, `5–9 MEDIUM`, `10+ FULL`.

For each available expiry window, fixed-scale Persistent Positioning components are:

- absolute OI Share Change max 40: .5/1/2/5/10pp → 0/8/16/28/40;
- absolute OI Growth max 30: 5/10/25/50/100% → 0/5/12/20/30;
- direction-matching interval share max 30: 50/60/70/80/90/100% → 0/5/10/18/25/30.

The overall score is the maximum available 3/5/10-window score, not an average. Net positive is
`PERSISTENT_BUILD`, net negative is `PERSISTENT_DECLINE`; neither implies trade direction.

## Same-Day Activity Score

`expiry-breakdown` supplies per-expiry total volume. Its vendor activity date defines DTE and the
valid activity observation session. For DTE > 0:

- Expiry Volume Share max 60: 5/10/20/30/40/50% → 0/10/25/40/50/60;
- comparable-expiry Volume Neighbor Ratio max 40: 1.2/1.5/2/3/5x → 0/8/15/25/40.

Comparable peers exclude DTE 0 and stay inside 1–7 (±3 DTE), 8–30 (±7), or 31–90 (±14). They
prefer a matching verified type, take the nearest four at most, and require at least two. The peer
count/DTEs/quality/median are persisted. The pool is never broadened to force a score. Missing
Neighbor points are not rescaled.

For DTE 0, the current session is never included in its own baseline. Exactly the previous 20 valid
same-ticker DTE-0 activity sessions are required; gaps, weekends, and holidays do not count. Fewer
than 20 gives `same_day_activity_score = null` and `INSUFFICIENT`. Once ready, persist mean, median,
MAD, empirical percentile (`prior_value <= current` count / 20), observation count and method:

- robust deviation `(current_share - median) / (1.4826 * MAD)`, max 70:
  ≤1/1.5/2/3/≥4 → 0/15/30/50/70;
- historical percentile, max 30: ≤70/80/90/95/100th → 0/10/20/25/30.

If MAD is zero or ≤ configured epsilon, robust deviation stays unavailable and only the fixed-scale
30-point percentile component is used. It is never rescaled. Raw current volume/share and the old
cross-expiry neighbor remain diagnostic; the latter has DTE-0 scoring weight zero.

Ticker-day `options-volume` Call/Put volume, OI, skew, and premiums remain ticker-only context and
must not be attributed to an expiry.

## Discovery confirmation

With one available track, Discovery equals that track. With two, primary is MAX and secondary is
MIN. Secondary <40 adds 0; 40–64.999 adds 3; 65–79.999 adds 6; ≥80 adds 10. Discovery is capped at
100 and is never an average. Source is BOTH only when secondary ≥40 contributes a bonus; otherwise
it is the primary track. Neither available gives null/NONE. Evidence Breadth is 0, 1, or 2 for zero,
one, or two meaningful tracks.

Eligibility still requires Same-Day ≥40 or Persistent ≥65; a confirmation bonus cannot create it. A
separate configurable `STRUCTURAL_COLD_START_ELIGIBLE` flag uses current OI Share ≥20% while history
has fewer than three observations; it never creates a Discovery score. At most four tickers are
selected, with at most one strongest eligible VERY_SHORT, SHORT, and MEDIUM expiry per ticker.

## Complete contract history

A daily chain is accepted only when `_meta.truncated == false` and returned rows equal
`total_contracts`. Calls and Puts are archived symmetrically with OI, quotes, IV, Greeks, spot, source
IDs, and vendor timestamps. `(ticker, contract_symbol, vendor_oi_date)` is unique and append-only.
Two observations give `delta_oi_1 = current - prior`; first observation has unknown prior, never zero.
Absence on a later day does not imply closing activity.

Contract persistence uses the maximum available 3/5/10-window score:

- absolute OI growth max 35: 10/25/50/100/200% → 0/8/16/25/35;
- absolute net build / current same-side expiry OI max 35:
  .25/.5/1/2/5% → 0/5/12/22/35;
- direction-matching interval share max 30 with the same 50–100% anchors.

## Contract Positioning Structure Score

The fixed 0–100 score uses only runtime-verified chain fields:

- contract OI / same-side expiry OI max 40: .5/1/2/5/10/20% → 0/5/12/22/32/40;
- OI / median nearby same-right strike OI max 30: 1.2/1.5/2/3/5x → 0/5/10/18/30;
- bid/ask spread quality max 15: 5/10/20/30/50% → 15/13/10/6/2;
- abs(delta) quality max 15: 0–.10=3, .10–.20=7, .20–.35=12, .35–.65=15,
  .65–.80=12, .80–.90=8, .90–1=6.

Spread above 50% is a structural-candidate hard reject. Low delta adds `LOTTO_RISK`, not rejection.
Classifications are IGNORE <50, OBSERVE 50–64, STRUCTURAL_CANDIDATE 65–74, STRONG_STRUCTURE 75–84,
EXTREME_STRUCTURE ≥85. Component values are preserved. Contract persistence and Radar remain separate
fields; no opaque combined score is created.

## OI Change Radar

The ranked `oi-change` subset is persisted when requested for selected tickers. Presence adds
supplemental previous/current/delta OI, volume, trades, price, premium, rank, quote, and date evidence.
Absence is `NOT_OBSERVED`, never negative evidence. Radar is never an OI Share denominator or daily
memory source.

## Cluster Positioning Score

Calls and Puts never merge. Candidate strikes may bridge one listed strike and span at most 20% of
available spot. Components are:

- OI-weighted constituent structure max 30;
- cluster OI / same-side expiry OI max 35: 5/10/20/40/60% → 0/5/12/22/35;
- coherence max 25: 2/3/4+ strikes → 12/18/25, minus 5 for a one-strike gap;
- aggregate constituent liquidity max 10.

Score ≥65 is VALID_CLUSTER and ≥80 STRONG_CLUSTER. Context includes persistent build/decline counts,
OI-weighted persistent score, and available window net OI change. It is not a final trading score.

## Intraday

Contract intraday is research-only because runtime validation returned only HTTP 202. It is not
required, not aggressively polled, and has weight 0 in every v1.2 score.
