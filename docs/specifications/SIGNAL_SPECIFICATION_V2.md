# Phase 2B v2 Trade Setup Research State Specification

Immutable specification version: `signal_spec_v2.0_phase2b`

This specification adds an append-only, evidence-based research state over preserved Phase 2A and
Phase 2B v1.x context. It does not replace or recalculate v1.x rows. It does not define a universal,
weighted, tradeability, conviction, bullish, or bearish score. Direction is always `UNRESOLVED`.

## Independent dimensions

Each contract state preserves six independent objects: Positioning Evidence, Price Context,
Volatility Context, Dealer/GEX Context, Execution Context, and Research Readiness. No function sums,
averages, or otherwise collapses these dimensions into a financial ranking.

### Positioning evidence

The five evidence families are Radar Event, Contract Persistence, Expiry Persistence, Structure,
and exact Cluster membership. Each family counts at most once; Radar premium, OI difference,
relative change, volume, and trades remain one Radar family. Presence is explicit, including
`NOT_YET_AVAILABLE` for persistence with insufficient history. One present family is
`SINGLE_EVIDENCE`; two or more are `MULTI_EVIDENCE`. The raw count and provenance identifiers are
persisted.

### Price

Price reuses the accepted regular-session observations, return/SMA/ATR calculations, gap policy,
and `UPTREND`/`DOWNTREND`/`MIXED`/`UNKNOWN` state unchanged. Raw strike and SMA distances remain
descriptive; v2 adds no near/far thresholds.

### Volatility and term topology

IV Rank remains a raw ticker value with vendor date/as-of. Candidate term topology requires the
exact candidate expiry node and the nearest shorter and longer nodes. Numeric values are compared
without an economic threshold. `1e-12` is used only as floating-point equality tolerance. States:

- `LOCAL_PEAK`: candidate IV is strictly above both neighbors;
- `LOCAL_TROUGH`: candidate IV is strictly below both;
- `RISING_THROUGH_CANDIDATE`: shorter < candidate < longer;
- `FALLING_THROUGH_CANDIDATE`: shorter > candidate > longer;
- `FLAT_OR_EQUAL`: an equality exists within tolerance;
- `INCOMPLETE`: any required node or IV is missing.

The candidate/neighbor IVs, expiries, pairwise differences, neighbor mean, candidate-minus-neighbor
mean, implied move, and source dates remain reconstructable.

### Dealer/GEX

GEX sign uses only the exact candidate expiry × strike cell. Positive, negative, and exact zero map
to `POSITIVE_NET_GEX`, `NEGATIVE_NET_GEX`, and `ZERO_NET_GEX`; missing/unavailable/non-numeric exact
cell maps to `UNKNOWN`. `AVAILABLE`, `AVAILABLE_DEGRADED`, `INCOMPLETE_OR_TRUNCATED`, and
`UNAVAILABLE` source quality is stored separately from exact-cell status and sign. A degraded exact
cell remains factual but is not fully ready.

### Execution

Execution reuses Phase 2A bid, ask, midpoint, spread, OI, Greeks, risk flags, hard-reject reason, and
accepted liquidity component. V2 introduces no liquidity or tradeability threshold.

## Research Readiness

The checklist has six layers: positioning, price, IV Rank, exact candidate term, Dealer/GEX, and
execution. Radar alone is sufficient positioning provenance. Price requires accepted `AVAILABLE` or
`AVAILABLE_WITH_GAPS`. IV Rank needs a numeric value plus date/as-of. Term readiness needs an exact
numeric candidate node; complete neighboring topology is not required. Dealer is fully ready only
with an exact numeric cell from a non-degraded, non-truncated source. Execution requires preserved
bid/ask and Greek evidence.

Zero missing/degraded layers is `CONTEXT_COMPLETE`, one is `CONTEXT_PARTIAL`, and two or more is
`CONTEXT_LIMITED`. The checklist, count, reasons, and rule version are persisted. These states
describe research-context completeness, not alpha, market quality, or a recommendation.

## Persistence and entity safety

`phase2b_candidate_states` is append-only and unique by source candidate evaluation plus v2 spec.
It links the v1.x candidate evaluation, ticker context, Phase 2A contract/expiry observations, and
exact cluster IDs. Both the v2 state config/hash and source context config/hash are preserved.

Expiry-only research rows are explicitly `EXPIRY_ONLY`. They remain visible but do not create a
contract identity, execution/Greeks, exact GEX cell, or contract v2 state.

## Version delta

V1.x context fields and APIs remain available. V2 adds state objects and readiness alongside them;
it does not overwrite historical rows. Phase 2B v3 is outside this specification.
