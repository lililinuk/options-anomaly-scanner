# Project guidance

- Never expose, print, log, or commit secrets. The Nightwatch API key is server-side only and must never enter frontend code or a `NEXT_PUBLIC_*` variable.
- Never make live Nightwatch calls in automated unit tests. Use fixtures and mocks for every external API.
- Report exactly which external URLs/API endpoints were contacted during a task.
- Do not invent financial formulas, anomaly thresholds, or score weights. Thresholds and weights belong in validated configuration.
- Financial logic must be traceable, documented, and reproducible from preserved raw source evidence.
- Preserve immutable historical detection fields, including DTE and bucket at detection; never overwrite history with dynamic state.
- Use UTC for persisted timestamps and `America/New_York` for US market-session/date logic. Never use the host timezone as market truth.
- Keep transport, ingestion, normalized models, analytics, persistence, and API routes separated.
- Run relevant backend tests and frontend lint/build checks before reporting completion.

