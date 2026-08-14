# Phase 2B v3 Candidate Research Workspace and Dealer/GEX Structure

Immutable specification version: `signal_spec_v3.0_phase2b`

This specification supersedes the previously considered production design centered on a
`PRICE_DIRECTIONAL_BIAS`. It preserves `signal_spec_v1.2_phase2b` evaluations and
`signal_spec_v2.0_phase2b` states as immutable evidence. It adds no trade recommendation, financial
score, GEX score, directional-flow inference, or Phase 2B v4 behavior.

## Evidence roles

The candidate workspace deliberately keeps three questions separate:

1. **Opportunity / Positioning** explains why an exact contract was surfaced. Radar premium,
   volume, trades, current OI, ΔOI, structure, persistence, cluster, and evidence breadth remain
   non-directional. Premium is aggregate `Contract Premium Activity`, not one order. Positive ΔOI
   is a net OI increase, not bought contracts. `Observed Flow Direction` remains `UNRESOLVED`, which
   is a provenance warning and not Neutral.
2. **Underlying Price** reuses the accepted factual regular-session Price Trend and its close,
   SMA20, SMA50, returns, ATR, and quality. It does not translate Price Trend to BUY, SELL, an option
   side, or a trade setup.
3. **Trade-Structure / Path** presents factual volatility, rule-based Dealer/GEX structure, and
   execution evidence. These data describe environment, levels, conditional paths, and practical
   execution—not underlying direction.

Every contract heading includes ticker, exact expiration, strike, right, immutable DTE at detection,
and immutable bucket at detection when its source contract observation exists. Expiry-only Phase 2A
rows remain `entity_type=EXPIRY_ONLY` and cannot open or fabricate an exact-contract v3 workspace.

## Dealer/GEX structure rules

`ANCHOR_EXPIRY` is the candidate expiration. The source must be `AVAILABLE` or
`AVAILABLE_DEGRADED`; `INCOMPLETE_OR_TRUNCATED` and `UNAVAILABLE` do not produce a structure.
Numeric zero in an available cell is a real zero, while absent/non-numeric cells remain missing.

### Primary Floor

Rule `dealer_gex_primary_floor_v1` selects the anchor-expiry cell with maximum positive
`net_dealer_gex_usd` among cells whose strike is strictly below current spot. It never uses absolute
GEX, a negative node, or a strike above spot. No qualifying cell yields
`NO_POSITIVE_FLOOR_IDENTIFIED` and a null Floor. Exact numeric ties are deterministically resolved
to the higher strike; the full positive-below-spot set is retained in the audit.

### Primary Upper Positive-GEX Node

Rule `dealer_gex_primary_upper_node_v1` selects maximum positive net GEX strictly above spot on the
anchor expiry. It is an upper structural node, not automatically resistance or a ceiling. Exact
numeric ties resolve to the lower strike.

### Below-Floor path

The Immediate Below-Floor Node is the highest usable strike strictly below the Primary Floor. Rule
`dealer_gex_below_floor_path_v1` emits `NEGATIVE_GEX_IMMEDIATELY_BELOW` and
`DOWNSIDE_ACCELERATION_RISK` only when this immediate node has negative net GEX. The statement is
conditional on a Floor break and does not predict a break, crash, or continuation. While spot is
above the positive Floor, `STABILIZATION_BIAS` describes a support-like structural zone, not
guaranteed support or a recommendation. The nearest five lower nodes are preserved for audit, so
the UI never implies that nothing exists farther below.

### Adjacent-expiry context

Rule `dealer_gex_adjacent_expiry_context_v1` inspects only the nearest earlier and nearest later
available expirations, at the Primary Floor strike. It never changes the anchor Floor and is not
scored:

- `ALIGNED`: both neighboring expiries contain positive net GEX at the Floor strike;
- `PARTIALLY_ALIGNED`: the only usable neighbor is positive;
- `MIXED`: two usable neighbors exist and only one is positive;
- `NOT_ALIGNED`: usable neighbor evidence exists but none is positive;
- `UNAVAILABLE`: no usable neighbor cell exists or no Primary Floor exists.

The raw previous/anchor/next values and their signs are exposed. No full cross-expiry resonance,
expiry weighting, or Dealer evolution state is implemented.

## Volatility and execution

Volatility retains IV Rank, candidate IV, local term topology, implied move, nearest term nodes,
differences, quality, and as-of fields. It has no displayed `Volatility Direction`, cheap/rich state,
or long/short-vol recommendation. Execution retains bid, ask, midpoint, spread, current OI, Greeks,
and accepted Phase 2A liquidity/risk facts. Delta is not directional market evidence.

## Persistence and replay

`phase2b_v3_research_workspaces` is append-only and has a unique identity of source v2 state plus
v3 specification version. It stores normalized role objects, source IDs, timestamps, configuration
hash, and all four GEX rule versions. The full vendor Heatmap is not copied; the ticker-context ID
and existing raw evidence references remain authoritative. Replay of the same source state is a
reuse/skip. V1 evaluations and v2 states are never updated.

## API contract

The existing candidate-context response keeps all v1 and v2 properties and adds:

```yaml
v3_research_workspace:
  specification_version: signal_spec_v3.0_phase2b
  contract_identity: {}
  opportunity_positioning: {}
  underlying_price: {}
  trade_structure:
    volatility: {}
    dealer_gex: {}
    execution: {}
  provenance: {}
  rule_versions: {}
```

Materialization uses preserved PostgreSQL evidence only and makes zero Nightwatch calls.
