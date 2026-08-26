# Nightwatch Stage 6 Baseline Cutoff Remediation — Accepted Result
Source: Founder-provided Stage 6 remediation completion result
Preservation mode: verbatim

Stage6 remediation is now passed

STAGE6_BASELINE_CUTOFF_REMEDIATION=PASS.

The narrow repair is contained to vnext.py⁠￼ and test_stage6_balanced_context.py⁠￼.

* Baseline evidence cutoff now comes from candidate_first_knowledge_at.
* Refresh cutoff remains context_evaluated_at.
* Raw sources, chain data, and Dealer/GEX use the explicit cutoff.
* OHLC bars after the cutoff’s New York trading date are excluded. Missing or malformed bar dates fail closed.
* The format provides authoritative trading_date per bar and payload-level vendor observation time, but no per-bar intraday timestamp.
* No migration or unrelated subsystem was changed.

Verification passed:

* Remediation regressions: 8/8
* Full Stage 6: 27/27
* Stage 5: 14/14
* Stage 4: 24/24
* Stage 3/time: 13/13
* Full backend: 376/376
* Ruff: PASS
* Alembic single head: 20260818_0017
* git diff --check: PASS
