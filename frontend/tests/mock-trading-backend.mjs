import { createServer } from "node:http";

const port = Number(process.env.MOCK_TRADING_PORT ?? 8001);
const generatedAt = "2026-08-30T16:00:00Z";

const anomaly = (id, family, identity, overrides = {}) => ({
  id,
  family,
  family_label: {
    RADAR_EVENT: "Radar",
    EXPIRY_ACTIVITY: "Expiry Activity",
    CONTRACT_PERSISTENCE: "Contract Persistence",
  }[family],
  entity_type: family === "EXPIRY_ACTIVITY" ? "EXPIRY" : "CONTRACT",
  identity,
  expiration: "2026-09-04",
  current_dte: 5,
  detection_dte: 7,
  detection_bucket: "DTE_7_14",
  qualifies_candidate: true,
  right: family === "EXPIRY_ACTIVITY" ? null : "C",
  strike: family === "EXPIRY_ACTIVITY" ? null : 182.5,
  delta_oi: family === "RADAR_EVENT" ? 5400 : null,
  premium_usd: family === "RADAR_EVENT" ? 3_250_000 : null,
  same_day_activity_score: family === "EXPIRY_ACTIVITY" ? 88 : null,
  same_day_score_basis: family === "EXPIRY_ACTIVITY" ? "CANONICAL_PRIOR_SESSIONS" : null,
  quote: {
    freshness: "STALE",
    as_of: "2026-08-28T19:58:00Z",
    iv: 0.331,
    delta: 0.57,
    bid_usd: 4.8,
    ask_usd: 5.1,
    spread_pct: 0.0606,
  },
  expiry_activity: family === "EXPIRY_ACTIVITY"
    ? { call_volume: 125000, put_volume: 98000, call_oi: 550000, put_oi: 490000 }
    : null,
  price_relationship: {
    availability: "AVAILABLE",
    price_context_label: "Previous Close",
    price_context_freshness: "STALE",
    reference_price_usd: 181.4,
  },
  featured: false,
  ...overrides,
});

const price = (freshness, overrides = {}) => ({
  freshness,
  label: freshness === "CURRENT" ? "Current Price" : "Previous Close",
  value_usd: 181.4,
  source: freshness === "CURRENT"
    ? "stock_state.current_price_usd"
    : "daily_ohlc.valid_regular_session_close",
  as_of: "2026-08-28T20:00:00Z",
  session: "REGULAR_CLOSE",
  fallback_used: freshness !== "CURRENT",
  ...overrides,
});

const volatility = (freshness, overrides = {}) => ({
  freshness,
  source: "persisted_current_context",
  term_as_of: "2026-08-28T19:55:00Z",
  iv_rank: {
    freshness,
    value: 47,
    as_of: "2026-08-28T19:55:00Z",
    vendor_semantics: "UNVERIFIED",
    classification: null,
    core_eligibility: "WITHHOLD_PENDING_PROVENANCE",
  },
  active_expiry_terms: {
    "2026-09-04": { candidate_term_iv: 0.331, topology: "FALLING" },
    "2026-09-11": { candidate_term_iv: 0.309, topology: "FLAT_OR_EQUAL" },
  },
  ...overrides,
});

const dealerGex = (freshness, overrides = {}) => ({
  freshness,
  source: "DEALER_GEX_ARCHIVE",
  archive_snapshot_id: "40000000-0000-4000-8000-000000000001",
  as_of: "2026-08-28T19:30:00Z",
  captured_at: "2026-08-28T19:31:00Z",
  availability: "AVAILABLE",
  vendor_snapshot_spot_usd: 180.9,
  vendor_snapshot_spot_semantic: "HISTORICAL_SOURCE_METADATA",
  relative_price_context_label: "Previous Close",
  relative_price_usd: 181.4,
  active_expiry_contexts: {
    "2026-09-04": {
      primary_floor: { strike_usd: 177.5, net_dealer_gex_usd: 32_400_000 },
      primary_upper_positive_gex_node: { strike_usd: 185, net_dealer_gex_usd: 18_200_000 },
      immediate_below_floor_node: { strike_usd: 175, net_dealer_gex_usd: -8_100_000 },
    },
  },
  sign_disclosure: "GEX sign is not equivalent to bullish/bearish direction.",
  ...overrides,
});

function candidate(id, ticker, anomalies, contexts = {}) {
  const counts = {
    RADAR_EVENT: anomalies.filter((item) => item.family === "RADAR_EVENT").length,
    EXPIRY_ACTIVITY: anomalies.filter((item) => item.family === "EXPIRY_ACTIVITY").length,
    CONTRACT_PERSISTENCE: anomalies.filter((item) => item.family === "CONTRACT_PERSISTENCE").length,
  };
  return {
    id,
    scan_run_id: "90000000-0000-4000-8000-000000000001",
    ticker,
    candidate_first_knowledge_at: "2026-08-28T20:35:00Z",
    active_anomaly_count: anomalies.length,
    active_family_counts: counts,
    featured_anomalies: anomalies.filter((item) => item.featured),
    active_anomalies: anomalies,
    current_trading_context: {
      identity: {
        state: "AVAILABLE",
        context_id: `${id}-context`,
        evaluated_at: "2026-08-28T20:05:00Z",
        origin: null,
        origin_state: "NOT_PERSISTED",
      },
      price: contexts.price ?? price("STALE"),
      volatility: contexts.volatility ?? volatility("STALE"),
      dealer_gex: contexts.dealer_gex ?? dealerGex("STALE"),
    },
    frozen_first_knowledge: {
      state: "PRESERVED_OUTSIDE_TRADING_VIEW",
      available: true,
      rendered_as_current: false,
    },
  };
}

const nvdaAnomalies = [
  anomaly("n-r1", "RADAR_EVENT", "NVDA260904C00182500", { featured: true, featured_semantic: "PRIORITY_TO_INSPECT" }),
  anomaly("n-r2", "RADAR_EVENT", "NVDA260904C00185000", { strike: 185, premium_usd: 2_800_000, delta_oi: 7200 }),
  anomaly("n-r3", "RADAR_EVENT", "NVDA260911P00175000", { expiration: "2026-09-11", current_dte: 12, right: "P", strike: 175, premium_usd: 1_950_000 }),
  anomaly("n-r4", "RADAR_EVENT", "NVDA260911C00190000", { expiration: "2026-09-11", current_dte: 12, strike: 190, premium_usd: 1_700_000 }),
  anomaly("n-r5", "RADAR_EVENT", "NVDA260918C00195000", { expiration: "2026-09-18", current_dte: 19, strike: 195, premium_usd: 1_500_000 }),
  anomaly("n-a1", "EXPIRY_ACTIVITY", "2026-09-04", { featured: true, featured_semantic: "PRIORITY_TO_INSPECT" }),
  anomaly("n-a2", "EXPIRY_ACTIVITY", "2026-09-11", { expiration: "2026-09-11", current_dte: 12, same_day_activity_score: 81 }),
  anomaly("n-p1", "CONTRACT_PERSISTENCE", "NVDA260904C00180000", { strike: 180, qualifies_candidate: false }),
];

const payload = {
  generated_at: generatedAt,
  market_timezone: "America/New_York",
  candidate_population: {
    state: "AVAILABLE",
    freshness: "STALE",
    freshness_reason: "NO_ACCEPTED_CANDIDATE_FRESHNESS_RULE",
    market_date: "2026-08-28",
    scan_run_id: "90000000-0000-4000-8000-000000000001",
    started_at: "2026-08-28T20:30:00Z",
    completed_at: "2026-08-28T20:35:00Z",
    candidate_materialized_at: "2026-08-28T20:35:00Z",
    candidate_count: 4,
  },
  candidates: [
    candidate("10000000-0000-4000-8000-000000000001", "NVDA", nvdaAnomalies),
    candidate(
      "10000000-0000-4000-8000-000000000002",
      "MSFT",
      [anomaly("m-r1", "RADAR_EVENT", "MSFT260904C00520000", { featured: true, featured_semantic: "PRIORITY_TO_INSPECT", strike: 520 })],
      {
        price: price("CURRENT", { value_usd: 518.75, label: "Current Price", session: "PREMARKET" }),
        volatility: { freshness: "UNAVAILABLE", reason: "NO_PERSISTED_CURRENT_CONTEXT" },
        dealer_gex: { freshness: "UNAVAILABLE", reason: "NO_ELIGIBLE_PERSISTED_GEX_ARCHIVE" },
      },
    ),
    candidate(
      "10000000-0000-4000-8000-000000000003",
      "TSLA",
      [
        anomaly("t-r1", "RADAR_EVENT", "TSLA260904P00340000", { right: "P", strike: 340, featured: true, featured_semantic: "PRIORITY_TO_INSPECT" }),
        anomaly("t-a1", "EXPIRY_ACTIVITY", "2026-09-04", { featured: true, featured_semantic: "PRIORITY_TO_INSPECT" }),
        anomaly("t-p1", "CONTRACT_PERSISTENCE", "TSLA260911C00375000", { expiration: "2026-09-11", current_dte: 12, strike: 375 }),
        anomaly("t-p2", "CONTRACT_PERSISTENCE", "TSLA260918P00320000", { expiration: "2026-09-18", current_dte: 19, right: "P", strike: 320 }),
      ],
    ),
    candidate(
      "10000000-0000-4000-8000-000000000004",
      "AAPL",
      [],
      {
        price: { freshness: "UNAVAILABLE", reason: "NO_ELIGIBLE_PERSISTED_PRICE" },
        volatility: { freshness: "UNAVAILABLE", reason: "NO_PERSISTED_CURRENT_CONTEXT" },
        dealer_gex: { freshness: "UNAVAILABLE", reason: "NO_ELIGIBLE_PERSISTED_GEX_ARCHIVE" },
      },
    ),
  ],
  contracts: {
    vendor_requests_on_read: 0,
    frozen_first_knowledge_mutated: false,
    automatic_context_capture: false,
  },
};

function send(response, status, body) {
  response.writeHead(status, { "Content-Type": "application/json", "Cache-Control": "no-store" });
  response.end(JSON.stringify(body));
}

createServer((request, response) => {
  const url = new URL(request.url, `http://${request.headers.host}`);
  if (url.pathname === "/api/v1/dashboard/trading" && request.method === "GET") {
    return send(response, 200, payload);
  }
  return send(response, 404, { detail: "Fixture route not found" });
}).listen(port, "127.0.0.1", () => {
  process.stdout.write(`MOCK_TRADING_BACKEND=http://127.0.0.1:${port}\n`);
});
