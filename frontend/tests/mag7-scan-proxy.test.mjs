import assert from "node:assert/strict";
import test from "node:test";

import { proxyScanRequest } from "../app/api/mag7-scan/proxy.ts";

const backendBaseUrl = "http://backend.invalid";

test("G1-A preserves backend failure as a non-success response", async () => {
  const request = async () => new Response(
    JSON.stringify({ detail: "fixture database unavailable" }),
    { status: 500, headers: { "Content-Type": "application/json" } },
  );

  const result = await proxyScanRequest("GET", backendBaseUrl, request);

  assert.equal(result.status, 500);
  assert.deepEqual(result.body, {
    detail: "fixture database unavailable",
    run_state: "FAILED",
  });
});

test("G1-A maps transport failure to generic FAILED without inventing DB_OFFLINE", async () => {
  const request = async () => {
    throw new TypeError("fixture connection refused");
  };

  const result = await proxyScanRequest("GET", backendBaseUrl, request);

  assert.equal(result.status, 503);
  assert.deepEqual(result.body, { detail: "Backend unavailable", run_state: "FAILED" });
});

for (const [name, payload] of [
  ["G1-B successful empty scan", { run_state: "SUCCESS_NO_CANDIDATE", scan: { status: "COMPLETE" }, research_candidates: [] }],
  ["G1-C successful populated scan", { run_state: "SUCCESS_WITH_CANDIDATES", scan: { status: "COMPLETE" }, research_candidates: [{ ticker: "NVDA" }] }],
  ["G1-D no scan run", { run_state: "NOT_RUN", scan: null, research_candidates: [] }],
]) {
  test(`${name} remains a successful, distinguishable response`, async () => {
    const request = async () => new Response(
      JSON.stringify(payload),
      { status: 200, headers: { "Content-Type": "application/json" } },
    );

    const result = await proxyScanRequest("GET", backendBaseUrl, request);

    assert.equal(result.status, 200);
    assert.deepEqual(result.body, payload);
  });
}
