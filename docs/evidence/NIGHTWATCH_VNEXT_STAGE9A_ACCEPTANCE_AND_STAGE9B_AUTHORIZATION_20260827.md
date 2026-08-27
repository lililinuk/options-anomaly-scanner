# NIGHTWATCH vNext — Stage 9A Acceptance + Stage 9B Authorization

**Date:** 2026-08-27  
**Decision:** Stage 9A accepted as `PASS_WITH_CARRIED_ITEMS`; Stage 9B authorized after Stage 9A integration.

## Stage 9A acceptance
Accepted without another retest cycle:
- ProductCandidate occurrence = one Research Sample
- canonical `scheduled_daily` = primary-research eligible
- Frozen First-Knowledge immutability
- historical-trigger retention
- XNYS session/reference mapping
- T+1/T+3/T+5 maturity
- direction-neutral Close Return / Close-path Max Upside / Max Downside
- cohort foundation metadata
- Live/Research firewall
- zero paid Nightwatch calls and zero historical outcome backfill in Stage 9A

Administrative closeout only:
- verify the worktree and canonical Stage 9A completion-report copies are byte-identical;
- record both SHA-256 values;
- if different, HOLD_CONFLICT rather than overwrite.

## Price-basis amendment for Stage 9B v1
The earlier Stage 9A blocker requiring a proven adjusted/corporate-action-consistent basis is relaxed for **Stage 9B descriptive Research v1**.

Founder-locked:

`STAGE9B_PRICE_BASIS_POLICY = RAW_REGULAR_CLOSE_RESEARCH_V1`

Use preserved regular-session Close values from one consistent raw parsing/provenance path.

Every measurement must be labeled truthfully as raw/unadjusted. Never call it:
- adjusted return
- total return
- corporate-action-consistent return

Important clarification: raw prices do not necessarily “adjust back” after 15 days. A stock split permanently changes the nominal price scale. Therefore corporate actions remain a data-quality issue, but they do not block the whole Stage 9B pipeline.

## Corporate-action handling v1
1. Preserve raw price basis/provenance on every measurement.
2. Add/retain explicit metadata capable of identifying raw-v1 and later corrected revisions.
3. If a **known price-scale-changing** action crosses a horizon (split, reverse split, stock dividend, spin-off/special distribution that mechanically rebases price), flag/quarantine the affected horizon from primary descriptive aggregation rather than treating the raw return as economically continuous.
4. Do not require a complete corporate-action service before Stage 9B starts.
5. If no known event is recorded, Stage 9B may compute the raw-price research outcome; this is an explicitly accepted v1 limitation.
6. Ordinary cash dividends remain part of raw **price return** semantics in v1; Stage 9B is not a total-return study.
7. Any later adjusted/corrected outcome must be append-only/versioned; never silently overwrite raw-v1.

## Stage 9B authorization
After the accepted Stage 9A implementation/evidence is integrated into canonical `main`, Stage 9B may proceed.

Still prohibited:
- Stage 9C Research UI
- live Actionability feedback or ranking changes
- Phase 2A/2B semantic changes
- bullish/bearish inference
- second Forward Outcome scheduler
- live/current-candidate consumption of Forward Outcome

`SECOND_FORWARD_OUTCOME_SCHEDULER = NO`

Stage 9B should first materialize everything possible from preserved historical OHLC. For the initial Stage 9B implementation run, make zero paid Nightwatch calls and report any residual due-only OHLC gap before later authorization.
