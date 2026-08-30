import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import { proxyTradingDashboard } from "../app/api/trading-dashboard/proxy.ts";
import {
  featuredAnomalies,
  filterActiveAnomalies,
  formatGexMillions,
  formatIv,
  freshness,
} from "../app/trading-dashboard-semantics.ts";

const anomaly = (id, family, overrides = {}) => ({
  id,
  family,
  family_label: family,
  entity_type: family === "EXPIRY_ACTIVITY" ? "EXPIRY" : "CONTRACT",
  identity: id,
  expiration: "2026-09-04",
  current_dte: 5,
  detection_dte: 7,
  detection_bucket: "DTE_7_14",
  qualifies_candidate: true,
  right: "C",
  strike: 180,
  delta_oi: null,
  premium_usd: null,
  same_day_activity_score: null,
  same_day_score_basis: null,
  quote: {},
  expiry_activity: null,
  price_relationship: {},
  ...overrides,
});

const candidate = {
  id: "candidate",
  scan_run_id: "scan",
  ticker: "NVDA",
  candidate_first_knowledge_at: "2026-08-28T20:00:00Z",
  active_anomaly_count: 5,
  active_family_counts: {
    RADAR_EVENT: 2,
    EXPIRY_ACTIVITY: 2,
    CONTRACT_PERSISTENCE: 1,
  },
  featured_anomalies: [
    anomaly("radar-1", "RADAR_EVENT", { featured: true, featured_semantic: "PRIORITY_TO_INSPECT" }),
    anomaly("radar-2", "RADAR_EVENT", { featured: true, featured_semantic: "PRIORITY_TO_INSPECT" }),
    anomaly("activity", "EXPIRY_ACTIVITY", { featured: true, featured_semantic: "PRIORITY_TO_INSPECT" }),
    anomaly("persistence", "CONTRACT_PERSISTENCE", { featured: true }),
  ],
  active_anomalies: [
    anomaly("radar-1", "RADAR_EVENT", { featured: true }),
    anomaly("radar-2", "RADAR_EVENT"),
    anomaly("activity-1", "EXPIRY_ACTIVITY", { featured: true }),
    anomaly("activity-2", "EXPIRY_ACTIVITY"),
    anomaly("persistence", "CONTRACT_PERSISTENCE"),
  ],
  current_trading_context: { identity: {}, price: {}, volatility: {}, dealer_gex: {} },
  frozen_first_knowledge: {},
};

test("Trading proxy reads the persisted Dashboard endpoint with GET only", async () => {
  const calls = [];
  const result = await proxyTradingDashboard("http://backend.invalid", async (url, init) => {
    calls.push([url, init.method]);
    return new Response(JSON.stringify({ candidates: [] }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  });
  assert.equal(result.status, 200);
  assert.deepEqual(calls, [["http://backend.invalid/api/v1/dashboard/trading", "GET"]]);
});

test("Featured display enforces maximum one per family and maximum three", () => {
  const result = featuredAnomalies(candidate);
  assert.deepEqual(result.map((item) => item.id), ["radar-1", "activity"]);
  assert.ok(result.length <= 3);
  assert.equal(new Set(result.map((item) => item.family)).size, result.length);
});

test("B4 family filters operate only on the supplied active anomaly list", () => {
  const radar = filterActiveAnomalies(candidate, new Set(["RADAR_EVENT"]), false);
  assert.deepEqual(radar.map((item) => item.id), ["radar-1", "radar-2"]);
  const featured = filterActiveAnomalies(
    candidate,
    new Set(["RADAR_EVENT", "EXPIRY_ACTIVITY", "CONTRACT_PERSISTENCE"]),
    true,
  );
  assert.deepEqual(featured.map((item) => item.id), ["radar-1", "activity-1"]);
});

test("IV and GEX use Trading-friendly presentation without direction semantics", () => {
  assert.equal(formatIv(0.331), "33.1%");
  assert.equal(formatIv(33.1), "33.1%");
  assert.equal(formatGexMillions(32_400_000), "+$32M");
  assert.equal(formatGexMillions(-8_100_000), "-$8M");
});

test("freshness never treats AVAILABLE as CURRENT", () => {
  assert.equal(freshness("CURRENT"), "CURRENT");
  assert.equal(freshness("STALE"), "STALE");
  assert.equal(freshness("UNAVAILABLE"), "UNAVAILABLE");
  assert.equal(freshness("AVAILABLE"), "UNAVAILABLE");
});

test("Trading source contains no historical trigger toggle, manual scan, or cross-family score", () => {
  const source = readFileSync(new URL("../app/trading-dashboard.tsx", import.meta.url), "utf8");
  const page = readFileSync(new URL("../app/page.tsx", import.meta.url), "utf8");
  assert.doesNotMatch(source, /Show Expired|Historical Triggers|Archived Triggers/i);
  assert.doesNotMatch(source, /Run MAG7 Scan|Refresh ticker context/i);
  assert.doesNotMatch(`${source}\n${page}`, /universal_score|cross_family_score/i);
  assert.doesNotMatch(page, /Today(?:'|&apos;)s (?:Product )?Candidates/i);
  assert.match(source, /Detection DTE \/ bucket/);
  assert.match(source, /Current DTE/);
});
