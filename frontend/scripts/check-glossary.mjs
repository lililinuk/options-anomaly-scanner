import { readFileSync } from "node:fs";

const source = readFileSync(new URL("../app/fieldGlossary.zh-TW.ts", import.meta.url), "utf8");
const glossaryBlock = source.match(/export const fieldGlossary = \{([\s\S]*?)\n\} satisfies/);
const columnsBlock = source.match(/export const visibleAnalyticalColumns = \[([\s\S]*?)\] as const/);
if (!glossaryBlock || !columnsBlock) throw new Error("Glossary registry structure is missing");
const keys = new Set([...glossaryBlock[1].matchAll(/^\s{2}([a-z0-9_]+):/gm)].map((match) => match[1]));
const columns = [...columnsBlock[1].matchAll(/"([a-z0-9_]+)"/g)].map((match) => match[1]);
const missing = columns.filter((column) => !keys.has(column));
if (missing.length) throw new Error(`Missing zh-TW glossary definitions: ${missing.join(", ")}`);
console.log(`Glossary completeness: ${columns.length} visible analytical columns, ${keys.size} documented fields`);

const dashboard = readFileSync(new URL("../app/scan-dashboard.tsx", import.meta.url), "utf8");
if (!dashboard.includes('if (value == null || value === "") return "—"')) {
  throw new Error("Dashboard must render unavailable analytical values as an em dash");
}
for (const required of [
  "same_day_activity_score", "persistent_positioning_score", "discovery_score",
  "oi_share", "oi_share_change", "contract_structure_score",
  "contract_persistent_score", "oi_change_radar_status", "archive_vendor_oi_date",
  "discovery_evidence_breadth", "dte",
]) {
  if (!columns.includes(required)) throw new Error(`Required v1.2 dashboard field missing: ${required}`);
}
for (const required of [
  "0DTE Baseline", "Rolling Mean", "Rolling Median + MAD", "Historical Percentile",
  "Evidence Breadth", "Cold Start",
]) {
  if (!source.includes(required)) throw new Error(`Required v1.2 glossary concept missing: ${required}`);
}
for (const required of ["Cross-MAG7 Expiry Selectivity", "Top Expiry Discoveries", "Previous-20 Baseline Status"]) {
  if (!dashboard.includes(required)) throw new Error(`Required v1.2 dashboard view missing: ${required}`);
}
console.log("Dashboard null-safety and Phase 2A v1.2 visible-field/distribution coverage: passed");
