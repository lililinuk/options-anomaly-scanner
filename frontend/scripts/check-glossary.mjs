import { readFileSync } from "node:fs";

const source = readFileSync(new URL("../app/fieldGlossary.zh-TW.ts", import.meta.url), "utf8");
const glossaryBlock = source.match(/export const fieldGlossary = \{([\s\S]*?)\n\} satisfies/);
const columnsBlock = source.match(/export const visibleAnalyticalColumns = \[([\s\S]*?)\] as const/);
if (!glossaryBlock || !columnsBlock) throw new Error("Glossary registry structure is missing");
const keys = new Set([...glossaryBlock[1].matchAll(/^\s{2}([a-z0-9_]+):/gm)].map((match) => match[1]));
const columns = [...columnsBlock[1].matchAll(/"([a-z0-9_]+)"/g)].map((match) => match[1]);
const missing = columns.filter((column) => !keys.has(column));
if (missing.length) throw new Error(`Missing zh-TW glossary definitions: ${missing.join(", ")}`);
console.log(`Glossary completeness: ${columns.length} legacy columns, ${keys.size} documented fields`);

const dashboard = readFileSync(new URL("../app/scan-dashboard.tsx", import.meta.url), "utf8");
if (!dashboard.includes('if (value == null || value === "") return "—"')) {
  throw new Error("Dashboard must render unavailable analytical values as an em dash");
}
for (const required of [
  "Radar Material Event", "Premium", "ΔOI", "OI Change %", "Persistent Positioning",
  "Expiry Activity", "Monthly OPEX", "Score Basis", "Trigger Sources",
  "Radar Archive Match", "Radar Threshold Profile",
]) {
  if (!source.includes(required)) throw new Error(`Required v1.3 glossary concept missing: ${required}`);
}
for (const required of [
  "Research State", "Positioning Evidence Breadth", "Candidate Term Topology",
  "Candidate Net GEX Sign", "Research Readiness", "Direction UNRESOLVED",
  "Expiry-only Research Row",
]) {
  if (!source.includes(required)) throw new Error(`Required Phase 2B v2 glossary concept missing: ${required}`);
}
for (const required of [
  "Why Found / Positioning", "Premium Activity", "Observed Flow Direction",
  "Underlying Price", "Volatility", "Dealer / GEX Structure", "Primary Floor",
  "Primary Upper Positive-GEX Node", "Immediate Below-Floor Node", "Execution",
]) {
  if (!dashboard.includes(required)) throw new Error(`Required Phase 2B v3 workspace state missing: ${required}`);
}
for (const required of [
  "Contract Premium Activity", "Exact-contract ΔOI", "Observed Flow Direction",
  "Underlying Price Trend", "Anchor Expiry", "Primary Floor",
  "Primary Upper Positive-GEX Node", "Immediate Below-Floor Node",
  "Stabilization Bias", "Downside Acceleration Risk", "Adjacent Expiry Context",
  "Dealer Source Quality",
]) {
  if (!source.includes(required)) throw new Error(`Required Phase 2B v3 glossary concept missing: ${required}`);
}
for (const required of [
  "Latest Contract Events", "Persistent Positioning", "Unusual Expiry Activity",
  "Product Candidates / Anomalies", "All qualifying anomalies retained",
]) {
  if (!dashboard.includes(required)) throw new Error(`Required Phase 2A vNext view missing: ${required}`);
}
const serverOnlyKeyName = ["NIGHTWATCH", "API", "KEY"].join("_");
const publicKeyPrefix = ["NEXT", "PUBLIC", "NIGHTWATCH"].join("_");
const vendorHost = ["api", "yehangshe", "com"].join(".");
for (const forbidden of [vendorHost, serverOnlyKeyName, publicKeyPrefix]) {
  if (dashboard.includes(forbidden)) throw new Error(`Browser code contains forbidden Nightwatch material: ${forbidden}`);
}
if (!dashboard.includes("Data unavailable")) {
  throw new Error("Dashboard must disclose unavailable Dealer/GEX context without showing zero");
}
if (!source.includes("UNAVAILABLE 與 ROW_UNAVAILABLE")) {
  throw new Error("Glossary must distinguish unavailable Dealer cell and row semantics");
}
for (const forbidden of ["Volatility Direction", "Dealer GEX Direction", "MODEL BULLISH", "TRADE BULLISH"]) {
  if (dashboard.includes(forbidden)) throw new Error(`Superseded directional UI remains: ${forbidden}`);
}
if (!dashboard.includes('anomaly.anomaly_entity === "CONTRACT"')) {
  throw new Error("Expiry-only rows must not open a fabricated exact-contract workspace");
}
for (const required of [
  "RADAR_EVENT", "EXPIRY_ACTIVITY", "CONTRACT_PERSISTENCE",
  "PRODUCT_CANDIDATE_PROJECTION", "CALIBRATION_REQUIRED",
]) {
  if (!dashboard.includes(required) && !source.includes(required)) {
    throw new Error(`Required Phase 2A vNext semantic missing: ${required}`);
  }
}
console.log("Dashboard null-safety, Phase 2A vNext projection, and expiry-only safety: passed");
