# Signal Engine Scope

## Agreed hierarchy

Future analysis proceeds hierarchically. A single unusual contract is evidence, never a final directional trade signal.

1. Contract
2. Expiry
3. Strike structure
4. Ticker positioning
5. Position lifecycle
6. Price / GEX / IV confirmation
7. Tradeability score

Every derived result must identify its raw and normalized evidence and the exact configuration/version used to produce it. Aggregate open interest must never be used to infer opening/closing participant identity.

## Tenor model

Calendar-DTE buckets are prepared as:

- `VERY_SHORT`: 0–7
- `SHORT`: 8–30
- `MEDIUM`: 31–90
- `LONG`: 91–180

A future detection stores immutable `dte_at_detection` and `bucket_at_detection`. `current_dte` and `current_bucket` are dynamic and calculated independently. Neither is signal age.

## Lifecycle vocabulary

The append-only lifecycle vocabulary is:

`DETECTED`, `OI_PENDING`, `BUILD_CONFIRMED`, `ACTIVE`, `REINFORCED`, `PARTIAL_UNWIND`, `MAJOR_UNWIND`, `POSSIBLE_ROLL`, `CLOSED`, `EXPIRED`.

These are schema/type placeholders only. Phase 1 defines no transition or inference rules.

## Financial decision logic

**NOT YET SPECIFIED — DO NOT INVENT**

This includes anomaly thresholds, signal thresholds, score weights, confirmation formulas, lifecycle inference rules, directional classification, trade construction, and buy/sell outputs. When specified, all thresholds and weights must live in validated versioned configuration rather than hard-coded business logic.

