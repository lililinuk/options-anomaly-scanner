# Scan Orchestration V1

## Manual Phase 2A flow

Every invocation receives a UUID `scan_run_id`. PostgreSQL advisory locking plus a persisted RUNNING check rejects concurrent scans. There is no scheduler (`scan_schedule_enabled=false`). The CLI is `python -m app.cli run-mag7-scan`; the dashboard uses the backend-only `POST /api/v1/scans/mag7`. The in-process HTTP request is intentionally not a durable production job queue: a process restart can interrupt it, and later production work should provide durable execution without changing the scan contract.

1. **S0 PREFLIGHT** checks PostgreSQL, persisted `/discover` capabilities, known quota, conflicts, and New York market date. It refreshes only dynamic DTE fields.
2. **S1 OI CONFIRMATION** inspects only existing PENDING records. It makes no broad OI request when none exist and appends confirmation events without changing Day-0 scores.
3. **S2/S3 AGGREGATE + PRELIMINARY** calls `volume-oi-per-expiry` once per MAG7 ticker, persists raw evidence, normalizes 0–180 DTE expiries, and scores them.
4. **S4 SELECTION** chooses at most four eligible tickers and one qualifying expiry per short bucket.
5. **S5 CHAIN + CONTRACT SCORE** calls one chain snapshot only for each selected ticker/expiry and retains Calls and Puts.
6. **S6 INTRADAY** deepens no more than 12 prioritized contracts across the entire scan and then rescores them.
7. **S7 FINAL EXPIRY + CLUSTERS** calculates final expiry evidence and same-side strike clusters.
8. **S8 SUMMARY** appends per-ticker/per-bucket positioning summaries.

The cold-start worst case is 7 aggregate + 12 chain + 12 intraday = 31 successful data requests. Per-scan hard limits remain 75 consumed units and 100 actual network attempts. A successful 200 data response counts one unit; attempts are counted independently. At a limit, deepening stops and status is `PARTIAL_BUDGET_LIMIT`. Other missing vendor data produces `PARTIAL`, never fake completeness.

Raw source reuse is keyed by endpoint plus canonical parameters for 30 minutes. Cache hits consume neither quota nor network attempts. Raw payloads are persisted before normalized/derived records; every derived record carries scan, source request/raw IDs where relevant, and `signal_spec_v1.0_phase2a`.

The browser only calls Next.js `/api/mag7-scan`, which uses the fixed FastAPI MAG7 routes. It has no generic vendor proxy and never receives the Nightwatch key. Phase 2B price/IV/GEX confirmation, direction, Tradeability, scheduling, alerts, and trade execution are out of scope.
