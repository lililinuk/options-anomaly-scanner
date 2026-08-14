# Phase 2B v1.2 — Dealer Heatmap Unavailable-State Resilience

Specification identifier: `signal_spec_v1.2_phase2b`

Status: production-resilience amendment to accepted `signal_spec_v1.1_phase2b`.

## Scope

This amendment changes only Dealer Heatmap availability, null safety, failure isolation, persisted
source-failure evidence, candidate API serialization, and unavailable-state presentation. It does
not change Phase 2A, Phase 2B price or volatility calculations, financial thresholds, scores,
rankings, GEX interpretation, or direction. `DIRECTION = UNRESOLVED` remains authoritative. Phase
2B v2 setup states are not implemented here.

## Dealer Heatmap is optional context

Dealer Heatmap is not a candidate eligibility dependency. Its analytical availability is one of:

- `AVAILABLE`: a usable, non-degraded surface was returned;
- `AVAILABLE_DEGRADED`: usable cells and row stacks were returned with vendor degraded state;
- `INCOMPLETE_OR_TRUNCATED`: usable returned collections are explicitly incomplete/truncated;
- `UNAVAILABLE`: no usable surface exists.

An unavailable Dealer layer never suppresses or rejects an otherwise valid Phase 2A candidate.
Positioning, Price, IV Rank, Term Structure, and Execution remain independently usable. Direction
remains `UNRESOLVED`.

## Normalization boundary

The normalization boundary accepts HTTP/source failure, absent payload, omitted collections,
`NULL` collections, empty arrays, and malformed/non-list optional collections without exposing a
nullable iterable downstream.

`cells` and `row_stacks` are internally normalized to filtered lists for control flow. The
analytical availability and reason are preserved separately, so an unavailable source with safe
empty control-flow lists is not reinterpreted as a valid empty surface.

- HTTP error, absent payload, or missing/null/malformed required collections → `UNAVAILABLE`.
- A successful usable response with both collections present as empty arrays → `AVAILABLE`; no
  exact candidate cell is `NOT_PRESENT` and no candidate row is `ROW_NOT_PRESENT`.
- Usable degraded data → `AVAILABLE_DEGRADED`; returned exact evidence remains unchanged.
- Usable truncated data → `INCOMPLETE_OR_TRUNCATED`.

No absent value is converted to numeric zero.

## Cell and row semantics

Candidate cell status:

- `EXACT_MATCH`: a usable surface contains the exact expiration and numeric strike pair;
- `NOT_PRESENT`: a usable surface was inspected but contains no exact pair;
- `UNAVAILABLE`: no usable surface exists.

Row-stack status:

- `ROW_EXACT_MATCH`: a usable surface contains the candidate strike row;
- `ROW_NOT_PRESENT`: a usable surface contains no candidate strike row;
- `ROW_UNAVAILABLE`: no usable surface exists.

For `UNAVAILABLE`, candidate net/call/put GEX, row net/absolute GEX, and vendor row rank are `NULL`.
`UNAVAILABLE`, `NOT_PRESENT`, and an exact cell whose returned GEX is numeric zero are distinct.

## Source-failure evidence

A caught Heatmap failure stores only safe structured evidence in the ticker context endpoint
status and normalized Dealer context:

- endpoint/capability;
- ticker;
- HTTP status;
- safe vendor error code/class when available;
- request identifier when available;
- UTC capture timestamp;
- analytical availability and reason.

The Authorization header, API key, and unnecessary raw error body are never persisted. Existing
API-usage observation remains the request-level audit record.

## Transaction and failure isolation

The server-side client makes at most one Heatmap request per unique ticker in a refresh attempt.
The request retains existing retry policy; the Phase 2B CLI continues to use concurrency 1 and
retries 0.

Heatmap errors are converted to normalized optional context before candidate evaluation. The
ticker snapshot and every candidate under that ticker therefore use one consistent unavailable
Dealer state. The service retains its existing transaction boundary: the ticker context and its
candidate evaluations commit atomically after all candidates are evaluated. Because Dealer
unavailability is data rather than an exception, it cannot roll back successful non-Dealer
context. Unrelated persistence/evaluation failures still roll back normally; database atomicity
is not weakened.

Fresh unavailable/degraded snapshots participate in the existing bounded freshness cache, which
prevents immediate duplicate calls caused by multiple contracts. This is not permanent negative
caching: a legitimate later refresh after freshness expiry, or an explicit forced refresh, may
probe again.

## Candidate API and dashboard

The persisted candidate API returns explicit unavailable states and `NULL` GEX numerics instead
of raising an evaluation-time 500. The dashboard keeps the candidate and all non-Dealer cards
visible and presents unavailable Dealer context as `Dealer/GEX：資料不可用`. It never renders the
missing surface as `0 GEX`.

These availability fields are suitable for a future research-readiness layer, but this amendment
does not implement `CONTEXT_COMPLETE`, `CONTEXT_PARTIAL`, or `CONTEXT_LIMITED`.

## Explicit exclusions

This amendment adds no support/resistance, Gamma Flip, Call Wall, Put Wall, GEX Score, GEX
normalization state, bullish/bearish inference, Trade Setup State, financial threshold, weight, or
ranking change.
