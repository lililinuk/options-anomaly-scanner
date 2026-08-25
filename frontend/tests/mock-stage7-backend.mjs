import { createServer } from "node:http";

const port = Number(process.env.MOCK_STAGE7_PORT ?? 8001);
const tickers = ["AAPL", "AMZN", "GOOGL", "META", "MSFT", "NVDA", "TSLA"];
const candidateId = (index) => `00000000-0000-4000-8000-${String(index + 1).padStart(12, "0")}`;
const triggerId = (candidateIndex, triggerIndex) =>
  `10000000-0000-4000-8000-${String(candidateIndex * 10 + triggerIndex + 1).padStart(12, "0")}`;

const candidates = tickers.map((ticker, index) => {
  const families = ticker === "NVDA"
    ? [
        ["RADAR_EVENT", "CONTRACT", "NVDA260821C00160000", true],
        ["EXPIRY_ACTIVITY", "EXPIRY", "2026-08-20", true],
        ["CONTRACT_PERSISTENCE", "CONTRACT", "NVDA260821C00155000", false],
      ]
    : [["EXPIRY_ACTIVITY", "EXPIRY", "2026-08-21", true]];
  return {
    id: candidateId(index),
    scan_run_id: "90000000-0000-4000-8000-000000000001",
    ticker,
    candidate_first_knowledge_at: "2026-08-19T20:30:00Z",
    materialization_rule_version: "phase2a_vnext_stage4b.product-candidate-materialization.v1",
    materialization_rule_hash: "fixture-hash",
    lifecycle_state: "MATERIALIZED",
    created_at: "2026-08-19T20:30:00Z",
    triggers: families.map(([family, entity, identity, qualifies], triggerIndex) => ({
      id: triggerId(index, triggerIndex),
      evidence_family: family,
      anomaly_entity_type: entity,
      anomaly_identity: identity,
      source_evidence_identity: `fixture:${ticker}:${family}`,
      qualifies_candidate: qualifies,
      present_at_first_knowledge: true,
      event_date: "2026-08-19",
      trigger_first_knowledge_at: "2026-08-19T20:29:00Z",
      source_first_received_at: "2026-08-19T20:28:00Z",
      vendor_observed_at: "2026-08-19T20:25:00Z",
      local_captured_at: "2026-08-19T20:28:00Z",
      source_ids: { fixture: true },
      provenance: { current_trigger_freshness: family === "CONTRACT_PERSISTENCE" ? "CALIBRATION_REQUIRED" : null },
      specification_version: "phase2a_vnext_stage4b",
    })),
  };
});

const baseContext = {
  id: "20000000-0000-4000-8000-000000000001",
  product_candidate_id: candidateId(5),
  evaluation_kind: "FIRST_KNOWLEDGE_BASELINE",
  candidate_first_knowledge_at: "2026-08-19T20:30:00Z",
  context_evaluated_at: "2026-08-19T20:32:00Z",
  price_as_of: "2026-08-19T20:00:00Z",
  context_specification_version: "phase2b_vnext_stage6",
  context_config_version: "phase2b_vnext_stage6_balanced_v1",
  context_config_hash: "fixture-context-hash",
  price_context: {
    history: {
      latest_regular_close_usd: 181.4,
      latest_trading_date: "2026-08-19",
      return_1d: 0.012,
      return_5d: -0.021,
      return_20d: 0.084,
      sma_20: 176.2,
      sma_50: 169.8,
      atr_14: 6.1,
      distance_to_sma20_pct: 0.0295,
      distance_to_sma50_pct: 0.0683,
      rolling_high_20: 186.5,
      rolling_low_20: 159.2,
      trend: "UPTREND",
    },
    stock_state: { availability: "AVAILABLE", current_price_usd: 182.1 },
  },
  volatility_context: {
    iv_rank: {
      availability: "PARTIAL",
      value: 47,
      vendor_semantics: "UNVERIFIED",
      core_eligibility: "WITHHOLD_PENDING_PROVENANCE",
      as_of: "2026-08-19T19:55:00Z",
    },
    expiry_contexts: {
      "2026-08-20": {
        availability: "AVAILABLE",
        candidate_term_iv: 0.52,
        exact_match_status: "EXACT_MATCH",
        nearest_shorter_node: null,
        nearest_longer_node: { implied_vol_pct: 0.48 },
        topology: "INCOMPLETE",
      },
      "2026-08-21": {
        availability: "AVAILABLE",
        candidate_term_iv: 0.49,
        exact_match_status: "EXACT_MATCH",
        nearest_shorter_node: { implied_vol_pct: 0.52 },
        nearest_longer_node: { implied_vol_pct: 0.46 },
        topology: "FALLING",
      },
    },
  },
  dealer_gex_context: {
    source: "ARCHIVE_ONLY",
    availability: "PARTIAL",
    vendor_observed_at: "2026-08-19T19:30:00Z",
    local_captured_at: "2026-08-19T19:31:00Z",
    expiry_contexts: {
      "2026-08-20": {
        availability: "AVAILABLE",
        spot_usd: 181.8,
        primary_floor: { strike_usd: 175, net_dealer_gex_usd: 1250000, sign: "POSITIVE" },
        primary_upper_positive_gex_node: { strike_usd: 185, net_dealer_gex_usd: 980000, sign: "POSITIVE" },
        immediate_below_floor_node: { strike_usd: 170, net_dealer_gex_usd: -420000, sign: "NEGATIVE" },
      },
    },
  },
  availability: {
    price: "AVAILABLE",
    stock_state: "AVAILABLE",
    volatility: "AVAILABLE",
    dealer_gex: "PARTIAL",
    iv_rank: "PARTIAL",
  },
  provenance: {
    evidence_cutoff_at: "2026-08-19T20:30:00Z",
    source_contract: ["daily_ohlc", "stock_state", "iv_rank", "term_structure"],
  },
  details: [
    {
      id: "30000000-0000-4000-8000-000000000001",
      product_candidate_trigger_id: triggerId(5, 0),
      anomaly_entity_type: "CONTRACT",
      anomaly_identity: "NVDA260821C00160000",
      event_date: "2026-08-19",
      expiry_anchor: "2026-08-21",
      source_first_received_at: "2026-08-19T20:28:00Z",
      vendor_observed_at: "2026-08-19T20:25:00Z",
      local_captured_at: "2026-08-19T20:28:00Z",
      quote_as_of: "2026-08-19T20:20:00Z",
      contract_snapshot: {
        contract_symbol: "NVDA260821C00160000",
        expiration: "2026-08-21",
        right: "C",
        strike: 160,
        dte_at_detection: 2,
        dte_anchor_date: "2026-08-19",
        dte_anchor_type: "TRIGGER_EVENT_DATE",
        strike_location: { strike_distance_usd: -22.1, strike_distance_pct: -0.1214, strike_distance_atr: -3.62 },
        contract_iv: 0.51,
        delta: 0.82,
        bid: 21.3,
        ask: 22.1,
        spread_pct: 0.0369,
      },
      expiry_activity_recap: null,
      volatility_context: { contract_iv: 0.51 },
      dealer_gex_context: { availability: "AVAILABLE" },
      deep_dive_references: { structure: { classification: "STRONG_STRUCTURE", score: 78 } },
      availability: { positioning_provenance: "AVAILABLE", volatility: "AVAILABLE", dealer_gex: "AVAILABLE" },
      provenance: { fixture: true },
    },
    {
      id: "30000000-0000-4000-8000-000000000002",
      product_candidate_trigger_id: triggerId(5, 1),
      anomaly_entity_type: "EXPIRY",
      anomaly_identity: "2026-08-20",
      event_date: "2026-08-19",
      expiry_anchor: "2026-08-20",
      source_first_received_at: "2026-08-19T20:28:00Z",
      vendor_observed_at: "2026-08-19T20:25:00Z",
      local_captured_at: "2026-08-19T20:28:00Z",
      quote_as_of: null,
      contract_snapshot: null,
      expiry_activity_recap: {
        expiration: "2026-08-20",
        dte_at_detection: 0,
        dte_anchor_date: "2026-08-19",
        call_volume: 125000,
        put_volume: 98000,
        call_oi: 550000,
        put_oi: 490000,
        same_day_activity_score: 82,
        score_basis: "HISTORY_IMMATURE",
      },
      volatility_context: { shared_expiry_key: "2026-08-20" },
      dealer_gex_context: { availability: "AVAILABLE" },
      deep_dive_references: {
        structures: [{ classification: "STRUCTURAL_CANDIDATE", score: 71 }],
        valid_clusters: [{ classification: "VALID_CLUSTER", right: "C", min_strike: 175, max_strike: 185 }],
      },
      availability: { positioning_provenance: "AVAILABLE", volatility: "AVAILABLE", dealer_gex: "AVAILABLE" },
      provenance: { fixture: true },
    },
  ],
};

const refreshContext = {
  ...baseContext,
  id: "20000000-0000-4000-8000-000000000002",
  evaluation_kind: "REFRESH",
  context_evaluated_at: "2026-08-20T14:05:00Z",
};

const scanPayload = {
  run_state: "SUCCESS_WITH_CANDIDATES",
  scan: {
    scan_run_id: "90000000-0000-4000-8000-000000000001",
    status: "COMPLETE",
    started_at: "2026-08-19T20:20:00Z",
    completed_at: "2026-08-19T20:30:00Z",
    consumed_quota_units: 14,
    network_attempts: 14,
  },
  product_candidates_state: "AVAILABLE",
  product_candidates: candidates,
  zero_dte_status: [{
    ticker: "NVDA",
    expiry: "2026-08-20",
    dte: 0,
    score_basis: "HISTORY_IMMATURE",
    baseline_status: "INSUFFICIENT",
    baseline_observation_count: 8,
    baseline_required: 20,
    baseline_method: "CANONICAL_PRIOR_SESSIONS",
    current_snapshot_kind: "PROVISIONAL_INTRADAY",
    canonical_history_maturity: "HISTORY_IMMATURE",
  }],
  all_material_contract_events: [{
    ticker: "NVDA",
    contract_symbol: "NVDA260821C00160000",
    expiration: "2026-08-21",
    dte: 2,
    right: "C",
    strike: 160,
    premium_usd: 2850000,
    oi_diff: 4200,
    vendor_observation_date: "2026-08-19",
    archive_match_status: "EXACT",
  }],
  persistent_positioning: [{
    ticker: "NVDA",
    contract_symbol: "NVDA260821C00155000",
    expiration: "2026-08-21",
    dte: 2,
    persistent_state: "PERSISTENT_BUILD",
    history_observation_count: 5,
    window_first_observation_date: "2026-08-13",
    window_last_observation_date: "2026-08-19",
    current_trigger_eligible: false,
    current_trigger_freshness: { mode: "CALIBRATION_REQUIRED", state: "CALIBRATION_REQUIRED" },
    quote_as_of: "2026-08-19T20:20:00Z",
  }],
  unusual_expiry_activity: [{
    ticker: "NVDA",
    expiry: "2026-08-20",
    dte: 0,
    score_basis: "HISTORY_IMMATURE",
    baseline_status: "INSUFFICIENT",
    baseline_observation_count: 8,
  }],
  research_candidates: [{ ticker: "NVDA", legacy_projection: true }],
};

const systemStatus = {
  scanner_status: "COMPLETE",
  latest_scan_at: "2026-08-19T20:30:00Z",
  latest_scan_status: "COMPLETE",
  latest_scan_started_at: "2026-08-19T20:20:00Z",
  latest_scan_completed_at: "2026-08-19T20:30:00Z",
  latest_scan_consumed_quota_units: 14,
  nightwatch_status: "connected",
  latest_capability_refresh_at: "2026-08-19T20:10:00Z",
  quota_limit: 100000,
  quota_remaining: 98765,
  rate_limit: 60,
  rate_limit_remaining: 58,
  latest_request_status: 200,
  database_status: "connected",
  scheduling_enabled: false,
  daily_collection_last_success_at: "2026-08-19T21:10:00Z",
  daily_collection_market_date: "2026-08-19",
  dealer_archive_last_vendor_observed_at: "2026-08-19T19:30:00Z",
  dealer_archive_last_captured_at: "2026-08-19T19:31:00Z",
};

function send(response, status, payload) {
  response.writeHead(status, { "Content-Type": "application/json", "Cache-Control": "no-store" });
  response.end(JSON.stringify(payload));
}

createServer((request, response) => {
  const url = new URL(request.url, `http://${request.headers.host}`);
  if (url.pathname === "/api/v1/system/status") return send(response, 200, systemStatus);
  if (url.pathname === "/api/v1/scans/mag7/latest") return send(response, 200, scanPayload);
  if (url.pathname === "/api/v1/scans/mag7" && request.method === "POST") {
    return send(response, 200, { scan_run_id: scanPayload.scan.scan_run_id, status: "COMPLETE" });
  }
  const contextMatch = url.pathname.match(/^\/api\/v1\/product-candidates\/([^/]+)\/context$/);
  if (contextMatch) {
    const candidate = candidates.find((item) => item.id === contextMatch[1]);
    if (!candidate) return send(response, 404, { detail: "ProductCandidate not found" });
    const contexts = candidate.ticker === "NVDA" ? [baseContext, refreshContext] : [];
    return send(response, 200, {
      product_candidate: candidate,
      baseline_state: contexts.length ? "AVAILABLE" : "NOT_YET_AVAILABLE",
      contexts,
    });
  }
  const refreshMatch = url.pathname.match(/^\/api\/v1\/product-candidates\/([^/]+)\/context\/refresh$/);
  if (refreshMatch && request.method === "POST") return send(response, 200, refreshContext);
  return send(response, 404, { detail: "Fixture route not found" });
}).listen(port, "127.0.0.1", () => {
  process.stdout.write(`MOCK_STAGE7_BACKEND=http://127.0.0.1:${port}\n`);
});
