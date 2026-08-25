import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

import {
  fieldGlossary,
  glossarySemantics,
  visibleAnalyticalColumns,
} from "../app/fieldGlossary.zh-TW.ts";

assert.deepEqual(new Set(visibleAnalyticalColumns), new Set(Object.keys(fieldGlossary)));
for (const [key, item] of Object.entries(fieldGlossary)) {
  assert.ok(item.中文名稱 && item.englishField && item.定義 && item.注意事項, `${key} is incomplete`);
  assert.ok(["ACTIVE", "LEGACY_INACTIVE", "WITHHELD"].includes(item.狀態), `${key} has an invalid status`);
}

for (const key of [
  "product_candidate", "anomaly", "why_found", "deep_dive",
  "first_knowledge_baseline", "refresh", "same_day", "oi_confirmed",
  "multi_observation", "block_b1", "block_b2", "block_b3", "block_b4",
  "block_b5", "availability", "zero_dte_status",
]) {
  assert.equal(fieldGlossary[key].狀態, "ACTIVE", `${key} must be active`);
}
for (const key of [
  "evidence_breadth_legacy", "stabilization_bias_legacy",
  "downside_risk_legacy", "composite_readiness_legacy",
  "greeks_legacy_phase2b",
]) {
  assert.equal(fieldGlossary[key].狀態, "LEGACY_INACTIVE", `${key} must be inactive`);
}
assert.equal(fieldGlossary.iv_rank.狀態, "WITHHELD");
assert.equal(glossarySemantics.candidateEntity, "TICKER_PRODUCT");
assert.deepEqual(glossarySemantics.anomalyEntities, ["CONTRACT", "EXPIRY"]);
assert.equal(glossarySemantics.expiryAnomalyRequiresContract, false);
assert.equal(glossarySemantics.evidenceBreadthActive, false);
assert.equal(glossarySemantics.stabilizationBiasActive, false);
assert.equal(glossarySemantics.downsideAccelerationRiskActive, false);
assert.deepEqual(glossarySemantics.phase2bCoreGreeks, ["DELTA"]);
for (const rule of [
  "missingEqualsZero", "unresolvedEqualsNeutral", "callImpliesBullish",
  "putImpliesBearish", "positiveDeltaOiImpliesOpening", "gexSignImpliesDirection",
]) {
  assert.equal(glossarySemantics[rule], false, `${rule} must remain false`);
}

const dashboard = readFileSync(new URL("../app/scan-dashboard.tsx", import.meta.url), "utf8");
const order = [
  "Today&apos;s Product Candidates",
  "Candidate Header",
  "Why Found",
  "Shared B1 / B2 / B3 Context",
  "Anomaly Details · B4",
  "Deep Dive",
  "Supporting / Audit / Provenance",
];
let lastIndex = -1;
for (const heading of order) {
  const nextIndex = dashboard.indexOf(heading, lastIndex + 1);
  assert.ok(nextIndex > lastIndex, `${heading} is missing or out of candidate-first order`);
  lastIndex = nextIndex;
}
assert.ok(dashboard.includes('detail.anomaly_entity_type === "CONTRACT"'));
assert.ok(dashboard.includes("valid_clusters"));
assert.ok(dashboard.includes("qualifies_candidate=false"));
assert.ok(dashboard.includes("no automatic refresh on page load"));
assert.ok(dashboard.includes("Raw / scoped Radar evidence view"));
assert.ok(dashboard.includes("Not the Product Candidate list"));
assert.ok(dashboard.includes("WITHHOLD_PENDING_PROVENANCE"));
for (const forbidden of [
  "Evidence Breadth", "STABILIZATION_BIAS", "DOWNSIDE_ACCELERATION_RISK",
  "Dealer Bullish", "Dealer Bearish", "Gamma", "Theta", "Vega",
  "Execution Score", "Conviction Score", "Ticker Score",
]) {
  assert.equal(dashboard.includes(forbidden), false, `Inactive concept leaked into dashboard: ${forbidden}`);
}

console.log(`Glossary semantics: ${Object.keys(fieldGlossary).length} governed vNext concepts`);
console.log("Candidate-first order, expiry-only boundary, and inactive-term safety: passed");
