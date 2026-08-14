# Phase 2B v3 Research Workspace Orchestration

Specification: `signal_spec_v3.0_phase2b`

V3 is a database-only projection over a source-aligned Phase 2B v1 candidate evaluation, its v2
state, and its preserved ticker context. It is not part of the daily archive or interactive MAG7
scan and cannot initiate vendor transport.

## Manual build

```text
python -m app.cli build-phase2b-v3-workspaces --contract SYMBOL [--contract SYMBOL ...]
```

For every exact contract the command resolves the latest candidate evaluation, the v2 state bound
to that evaluation, its ticker context, and the latest preserved contract observation. It then:

1. preserves exact identity and immutable detection DTE/bucket;
2. organizes accepted evidence into the three v3 roles;
3. derives anchor-expiry GEX structure from the persisted normalized Heatmap;
4. writes one immutable workspace per source v2 state and v3 spec;
5. prints created/reused/missing counts plus literal `network_attempts=0 paid_units=0`.

Same-source replay returns the existing row. A newer upstream candidate evaluation or v2 state can
produce a new append-only v3 workspace; historical v1/v2/v3 rows remain unchanged.

## Read path

```text
PostgreSQL preserved evidence
  -> phase2b_v3_research_workspaces
  -> FastAPI /api/v1/scans/candidates/{contract_symbol}/context
  -> fixed Next.js /api/candidate-context proxy
  -> role-separated candidate workspace
```

The API property is additive as `v3_research_workspace`. A null property means no workspace has
been materialized for that exact source evaluation; it never triggers an on-read vendor call. The
browser communicates only with the fixed Next.js proxy and never with Nightwatch.

## Operational boundaries

- no scheduler, live refresh, or Nightwatch endpoint is added;
- no Phase 2A selection, scoring, persistence, or historical rows are changed;
- no PRICE_DIRECTIONAL_BIAS, trade thesis, BUY/SELL, or option recommendation is created;
- no GEX evolution or full cross-expiry model is inferred;
- source timestamps remain separate across Radar, chain/archive, price, volatility, and Dealer.
