# Phase 2B v3.1 Dealer/GEX Time-Series Archive

Immutable specification version: `signal_spec_v3.1_phase2b`

This is an additive data-foundation amendment to `signal_spec_v3.0_phase2b`. Existing v3.0
workspaces and all earlier Phase 2A/2B evidence remain unchanged. V3.1 adds no trade recommendation,
Actionability Score, directional-flow inference, GEX direction score, lifecycle state, or Phase 3
behavior.

## Archive authority and scope

The archive captures the full multi-expiry Nightwatch Dealer heatmap for every configured MAG7
ticker through:

```text
GET /v1/derived/heatmap/{ticker}/snapshot?format=full
```

The fixed universe is AAPL, MSFT, NVDA, AMZN, META, GOOGL, and TSLA. Capture is independent of
current candidate selection. Requests are sequential (`concurrency=1`), use zero retries, and are
bounded to seven network attempts and seven consumed units per configured MAG7 run.

Source quality is one of:

- `AVAILABLE`: complete, timestamped, usable full surface;
- `AVAILABLE_DEGRADED`: timestamped surface with explicit, retained degradation;
- `INCOMPLETE_OR_TRUNCATED`: retained attempt/raw evidence, no analytical cells;
- `UNAVAILABLE`: retained attempt metadata, no analytical cells.

Unavailable and missing values are never converted to numeric zero. An actual vendor zero is
preserved. A missing Call, Put, or net GEX value remains null.

## Observation identity and append-only persistence

`dealer_gex_archive_runs` records the external trigger, intended slot, XNYS session date, universe,
configuration/spec versions, per-run outcome counts, network attempts, and safe quota deltas.

`dealer_gex_snapshots` records ticker, vendor `generated_at`, UTC capture time, spot, quality,
endpoint/capability identity, request/raw-evidence references, and a versioned surface identity.

`dealer_gex_snapshot_cells` records every usable expiration/strike cell with nullable net, Call,
and Put GEX values.

Analytical identity is a deterministic hash of ticker, actual vendor observation timestamp,
`format=full`, and `nightwatch_dealer_heatmap_full_v1`. Replaying the same vendor surface reuses the
existing analytical observation. Uniqueness is not ticker plus calendar date; future independently
configured intraday slots can coexist. There is no retention deletion in v3.1.

## Time-series and future-label boundary

Coverage diagnostics report distinct valid observations, first/latest vendor timestamps, usable
and degraded observations, and unavailable/incomplete attempts. The archive retains the source
metadata needed for a later calibration gate, but v3.1 computes no future price label, no realized
outcome, no Dealer build/decay/migration state, and no Actionability feature.

## Candidate-workspace consumption

New `signal_spec_v3.1_phase2b` workspaces choose the latest usable archived surface only when both:

1. `vendor_observed_at <= candidate_evaluated_at`; and
2. `captured_at <= candidate_evaluated_at`.

This prevents look-ahead. If no eligible archive surface exists, the preserved source-aligned
Phase 2B ticker context remains the fallback. Provenance records the selected snapshot ID, raw
payload/request references, vendor time, capture time, and source type. Candidate analysis still
uses only the anchor expiration plus the nearest previous and nearest next expirations. Archiving a
full surface does not broaden the existing analysis scope.

## Explicit non-goals

V3.1 does not infer Dealer inventory, opening/closing intent, buyer/seller initiation, future
returns, or production evolution states. It does not change Phase 2A scores, eligibility, ticker
selection, contract structure rules, or cluster rules. It does not start Phase 3.
