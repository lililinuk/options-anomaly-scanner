import type {
  AnomalyFamily,
  Freshness,
  JsonRecord,
  TradingAnomaly,
  TradingCandidate,
} from "./trading-dashboard-types";

export const familyOrder: AnomalyFamily[] = [
  "RADAR_EVENT",
  "EXPIRY_ACTIVITY",
  "CONTRACT_PERSISTENCE",
];

export const familyLabels: Record<AnomalyFamily, string> = {
  RADAR_EVENT: "Radar",
  EXPIRY_ACTIVITY: "Expiry Activity",
  CONTRACT_PERSISTENCE: "Contract Persistence",
};

export function record(value: unknown): JsonRecord {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as JsonRecord)
    : {};
}

export function freshness(value: unknown): Freshness {
  return value === "CURRENT" || value === "STALE" ? value : "UNAVAILABLE";
}

export function featuredAnomalies(candidate: TradingCandidate): TradingAnomaly[] {
  const seen = new Set<AnomalyFamily>();
  return candidate.featured_anomalies.filter((item) => {
    if (seen.has(item.family) || seen.size >= 3) return false;
    seen.add(item.family);
    return item.featured_semantic === "PRIORITY_TO_INSPECT";
  });
}

export function filterActiveAnomalies(
  candidate: TradingCandidate,
  families: Set<AnomalyFamily>,
  featuredOnly: boolean,
): TradingAnomaly[] {
  return candidate.active_anomalies.filter(
    (item) => families.has(item.family) && (!featuredOnly || item.featured === true),
  );
}

export function formatIv(value: unknown): string {
  if (typeof value !== "number" || !Number.isFinite(value)) return "UNAVAILABLE";
  const percentage = Math.abs(value) <= 1 ? value * 100 : value;
  return `${percentage.toFixed(1)}%`;
}

export function formatGexMillions(value: unknown): string {
  if (typeof value !== "number" || !Number.isFinite(value)) return "UNAVAILABLE";
  const rounded = Math.round(value / 1_000_000);
  return `${rounded >= 0 ? "+" : "-"}$${Math.abs(rounded)}M`;
}

export function formatMoney(value: unknown, digits = 2): string {
  return typeof value === "number" && Number.isFinite(value)
    ? new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
        maximumFractionDigits: digits,
      }).format(value)
    : "UNAVAILABLE";
}

export function formatNumber(value: unknown): string {
  return typeof value === "number" && Number.isFinite(value)
    ? value.toLocaleString("en-US", { maximumFractionDigits: 4 })
    : "—";
}
