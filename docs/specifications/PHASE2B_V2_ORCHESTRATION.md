# Phase 2B v2 Research State Orchestration

1. Phase 2A routes select an exact contract candidate and preserve raw provenance.
2. The accepted Phase 2B v1.x flow owns vendor transport and immutable normalized ticker context.
3. `python -m app.cli build-phase2b-v2-states --contract SYMBOL` reads the latest persisted candidate
   evaluation, its ticker context, the latest matching Phase 2A contract/expiry rows, and exact
   cluster membership.
4. The pure v2 domain builder creates the six independent state dimensions and readiness checklist.
5. One append-only `phase2b_candidate_states` row is written. Replaying the same evaluation/spec
   reuses it, so it is idempotent.
6. `GET /api/v1/scans/candidates/{symbol}/confirmation` continues returning every v1.x field and
   additionally returns nullable `v2_state`. The fixed Next.js proxy remains the only browser path.

The state build performs zero Nightwatch calls and consumes zero quota. It cannot create a state for
an expiry-only row because no exact contract evaluation exists. Controlled validation should reuse
persisted NVDA and TSLA evidence unless a separate authorized context refresh is genuinely required.
