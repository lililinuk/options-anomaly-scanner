# NIGHTWATCH vNext — Stage 9A Direct Start Authorization
## Supersedes the Prior Baseline-HOLD / Delta-Review Gate

**Date:** 2026-08-27  
**Status:** FOUNDER AUTHORIZED — START STAGE 9A NOW  
**Authorized baseline:** `ae8e4a28de411b61fdfd1933118f62159381eaed`

## 1. Authorization decision

The prior Stage 9A baseline HOLD is superseded.

Stage 9A may start directly from:

`main @ ae8e4a28de411b61fdfd1933118f62159381eaed`

No separate baseline-validation test cycle or independent delta-review gate is required before Stage 9A implementation.

Normal Stage 9A implementation tests remain required before Stage 9A can be accepted.

## 2. Intervening changes

Known intervening commits since the original authorization baseline:

1. `1a07e7e7d5e4be8a4f6576721bed9110bd9313f1` — `fix(phase2a): handle incomplete daily OI chains`
2. `ae8e4a28de411b61fdfd1933118f62159381eaed` — `docs: freeze trading dashboard vNext amendment spec`

Founder decision: these changes do not require reopening Stage 9 Design before Stage 9A starts.

The Trading Dashboard vNext amendment is documentation-only and explicitly preserves the separation between Current Trading Context, immutable Frozen First-Knowledge research evidence, and future Stage 9 Research.

Stage 9A must implement against the actual current repository state; it must not revert or bypass the accepted Phase 2A incomplete-chain handling.

## 3. Canonical evidence

Before code changes, ensure the following files exist under:

`F:\options-anomaly-scanner\docs\evidence`

- `NIGHTWATCH_VNEXT_STAGE9_DESIGN_GATE_FINAL_20260827.md`
- `NIGHTWATCH_VNEXT_STAGE9_HISTORICAL_TRIGGER_RETENTION_DESIGN_DECISION_20260826.md`
- `NIGHTWATCH_VNEXT_STAGE9A_FORWARD_OUTCOME_FOUNDATION_EXECUTION_PACKAGE_20260827.md`
- `NIGHTWATCH_VNEXT_STAGE9A_DIRECT_START_AUTHORIZATION_20260827.md`

If supplied as attachments and absent, copy byte-for-byte and verify SHA-256.

If a same-name canonical file exists and differs, do not overwrite; return HOLD_CONFLICT.

Also read the current repository's Founder-approved Trading Dashboard vNext canonical amendment as an additional authoritative boundary document.

## 4. Stage 9A scope remains unchanged

Proceed with Stage 9A foundation only.

Still prohibited:

- Stage 9B historical outcome materialization/backfill
- Stage 9C Research Workspace implementation
- second Forward Outcome scheduler
- paid Nightwatch API calls
- live ranking changes
- Phase 2A threshold changes
- bullish/bearish outcome inference
- live/current-candidate consumption of Forward Outcome
- mutation of Frozen First-Knowledge Baseline

## 5. Required implementation behavior

Start by creating the temporary Stage 9A worktree from the current verified `origin/main`.

Suggested:

- `F:\options-anomaly-scanner-stage9a`
- `vnext/stage9a-forward-outcome-foundation`

Implement the existing Stage 9A Execution Package from the renewed baseline.

No extra pre-implementation test gate is required.

However, the Stage 9A completion report must still include the full required focused tests, relevant backend suite, lint/static checks, migration integrity checks, Live/Research firewall proof, and zero-paid-call proof.

## 6. Completion report addition

Include:

`DIRECT_START_BASELINE = ae8e4a28de411b61fdfd1933118f62159381eaed`

and state:

`SEPARATE_BASELINE_VALIDATION_GATE = WAIVED_BY_FOUNDER`

This waiver applies only to the additional pre-implementation baseline review/test cycle. It does not waive Stage 9A implementation verification.
