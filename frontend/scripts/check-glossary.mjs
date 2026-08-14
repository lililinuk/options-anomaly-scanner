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
  "Latest Contract Events", "Persistent Positioning", "Unusual Expiry Activity",
  "Deep Dive / Research Candidates",
]) {
  if (!dashboard.includes(required)) throw new Error(`Required v1.3 dashboard view missing: ${required}`);
}
for (const forbidden of ["api.yehangshe.com", "NIGHTWATCH_API_KEY", "NEXT_PUBLIC_NIGHTWATCH"]) {
  if (dashboard.includes(forbidden)) throw new Error(`Browser code contains forbidden Nightwatch material: ${forbidden}`);
}
if (!dashboard.includes("Dealer/GEX：資料不可用")) {
  throw new Error("Dashboard must disclose unavailable Dealer/GEX context without showing zero");
}
if (!source.includes("UNAVAILABLE 與 ROW_UNAVAILABLE")) {
  throw new Error("Glossary must distinguish unavailable Dealer cell and row semantics");
}
console.log("Dashboard null-safety, Dealer/GEX unavailable state, and Phase 2A v1.3 coverage: passed");
