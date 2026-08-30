export type JsonRecord = Record<string, unknown>;

export type Freshness = "CURRENT" | "STALE" | "UNAVAILABLE";

export type AnomalyFamily =
  | "RADAR_EVENT"
  | "EXPIRY_ACTIVITY"
  | "CONTRACT_PERSISTENCE";

export type TradingAnomaly = {
  id: string;
  family: AnomalyFamily;
  family_label: string;
  entity_type: "CONTRACT" | "EXPIRY";
  identity: string;
  expiration: string;
  current_dte: number;
  detection_dte: number | null;
  detection_bucket: string | null;
  qualifies_candidate: boolean;
  right: string | null;
  strike: number | null;
  delta_oi: number | null;
  premium_usd: number | null;
  same_day_activity_score: number | null;
  same_day_score_basis: string | null;
  quote: JsonRecord;
  expiry_activity: JsonRecord | null;
  price_relationship: JsonRecord;
  featured?: boolean;
  featured_semantic?: "PRIORITY_TO_INSPECT";
};

export type TradingContext = {
  identity: JsonRecord;
  price: JsonRecord;
  volatility: JsonRecord;
  dealer_gex: JsonRecord;
};

export type TradingCandidate = {
  id: string;
  scan_run_id: string;
  ticker: string;
  candidate_first_knowledge_at: string;
  active_anomaly_count: number;
  active_family_counts: Record<AnomalyFamily, number>;
  featured_anomalies: TradingAnomaly[];
  active_anomalies: TradingAnomaly[];
  current_trading_context: TradingContext;
  frozen_first_knowledge: JsonRecord;
};

export type CandidatePopulation = {
  state: "AVAILABLE" | "UNAVAILABLE";
  freshness: Freshness;
  freshness_reason: string;
  market_date: string | null;
  scan_run_id: string | null;
  started_at: string | null;
  completed_at: string | null;
  candidate_materialized_at: string | null;
  candidate_count: number;
};

export type TradingDashboardPayload = {
  generated_at: string;
  market_timezone: "America/New_York";
  candidate_population: CandidatePopulation;
  candidates: TradingCandidate[];
  contracts: {
    vendor_requests_on_read: 0;
    frozen_first_knowledge_mutated: false;
    automatic_context_capture: false;
  };
  detail?: string;
};
