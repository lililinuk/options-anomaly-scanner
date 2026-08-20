import assert from "node:assert/strict";
import test from "node:test";

import { proxyCandidateContext } from "../app/api/candidate-context/proxy.ts";
import { proxySystemStatus } from "../app/api/system-status/proxy.ts";
import {
  authoritativeCandidates,
  defaultContext,
  runStateMessage,
  zeroDteConsequence,
} from "../app/dashboard-semantics.ts";
import { glossarySemantics } from "../app/fieldGlossary.zh-TW.ts";
import { timestampDisplay } from "../app/time-display.ts";

const candidateId = "11111111-1111-4111-8111-111111111111";

test("S7-A/B keeps all seven persisted candidates without Top-4 truncation", () => {
  const product_candidates = ["AAPL", "AMZN", "GOOGL", "META", "MSFT", "NVDA", "TSLA"]
    .map((ticker, index) => ({ id: String(index), ticker }));
  const result = authoritativeCandidates({
    run_state: "SUCCESS_WITH_CANDIDATES",
    scan: null,
    product_candidates,
  });
  assert.equal(result.length, 7);
  assert.deepEqual(result.map((candidate) => candidate.ticker), [
    "AAPL", "AMZN", "GOOGL", "META", "MSFT", "NVDA", "TSLA",
  ]);
});

test("S7-C all run states have truthful, distinguishable messages", () => {
  const states = [
    "DB_OFFLINE", "NOT_RUN", "RUNNING", "FAILED",
    "SUCCESS_NO_CANDIDATE", "SUCCESS_WITH_CANDIDATES",
  ];
  const messages = states.map((state) => runStateMessage(state, "AVAILABLE"));
  assert.equal(new Set(messages).size, states.length);
  assert.match(messages[4], /No qualifying Product Candidate today/);
  assert.doesNotMatch(messages[0], /No qualifying Product Candidate today/);
  assert.doesNotMatch(messages[3], /No qualifying Product Candidate today/);
});

test("S7-E frozen baseline remains the default even after later refreshes", () => {
  const refresh = { id: "refresh", evaluation_kind: "REFRESH" };
  const baseline = { id: "baseline", evaluation_kind: "FIRST_KNOWLEDGE_BASELINE" };
  assert.equal(defaultContext([refresh, baseline]).id, "baseline");
  assert.equal(defaultContext([refresh]).id, "refresh");
  assert.equal(defaultContext([]), null);
});

test("S7-F time formatting is fixed to New York with explicit UTC detail", () => {
  const result = timestampDisplay("2026-08-19T20:30:00Z");
  assert.ok(result);
  assert.match(result.ny, /EDT/);
  assert.equal(result.utc, "2026-08-19T20:30:00Z");
});

test("S7-M 0DTE identity determines the disclosed canonical consequence", () => {
  const base = {
    canonical_history_maturity: "HISTORY_IMMATURE",
  };
  assert.match(
    zeroDteConsequence({ ...base, current_snapshot_kind: "PROVISIONAL_INTRADAY" }),
    /excluded from the canonical research baseline/,
  );
  assert.match(
    zeroDteConsequence({ ...base, current_snapshot_kind: "LEGACY_OR_AMBIGUOUS" }),
    /excluded from the canonical research baseline/,
  );
});

test("S7-O/P candidate context proxy preserves non-2xx and uses candidate-id routes", async () => {
  const calls = [];
  const request = async (url, init) => {
    calls.push([url, init.method]);
    return new Response(JSON.stringify({ detail: "fixture conflict" }), {
      status: 409,
      headers: { "Content-Type": "application/json" },
    });
  };
  const read = await proxyCandidateContext("GET", "http://backend.invalid", candidateId, request);
  const refresh = await proxyCandidateContext("POST", "http://backend.invalid", candidateId, request);
  assert.equal(read.status, 409);
  assert.equal(refresh.status, 409);
  assert.deepEqual(calls, [
    [`http://backend.invalid/api/v1/product-candidates/${candidateId}/context`, "GET"],
    [`http://backend.invalid/api/v1/product-candidates/${candidateId}/context/refresh`, "POST"],
  ]);
});

test("S7-O system-status proxy does not mask backend failure as HTTP 200", async () => {
  const result = await proxySystemStatus(
    "http://backend.invalid",
    async () => new Response(JSON.stringify({ detail: "fixture failure" }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    }),
  );
  assert.equal(result.status, 500);
  assert.deepEqual(result.body, { detail: "fixture failure" });
});

test("S7-Q glossary semantics enforce entity and inactive-feature boundaries", () => {
  assert.equal(glossarySemantics.candidateEntity, "TICKER_PRODUCT");
  assert.deepEqual(glossarySemantics.anomalyEntities, ["CONTRACT", "EXPIRY"]);
  assert.equal(glossarySemantics.expiryAnomalyRequiresContract, false);
  assert.equal(glossarySemantics.evidenceBreadthActive, false);
  assert.equal(glossarySemantics.stabilizationBiasActive, false);
  assert.deepEqual(glossarySemantics.phase2bCoreGreeks, ["DELTA"]);
});
