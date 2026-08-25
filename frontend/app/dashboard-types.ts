export type JsonRecord = Record<string, unknown>;

export type RunState =
  | "DB_OFFLINE"
  | "NOT_RUN"
  | "RUNNING"
  | "FAILED"
  | "SUCCESS_NO_CANDIDATE"
  | "SUCCESS_WITH_CANDIDATES";

export type ScanMetadata = {
  scan_run_id?: string;
  status: string;
  started_at?: string | null;
  completed_at?: string | null;
  consumed_quota_units: number;
  network_attempts: number;
  archive_status?: string | null;
  archive_completed_at?: string | null;
};

export type ProductCandidateTrigger = {
  id: string;
  evidence_family: "RADAR_EVENT" | "EXPIRY_ACTIVITY" | "CONTRACT_PERSISTENCE";
  anomaly_entity_type: "CONTRACT" | "EXPIRY";
  anomaly_identity: string;
  source_evidence_identity: string;
  qualifies_candidate: boolean;
  present_at_first_knowledge: boolean;
  event_date: string | null;
  trigger_first_knowledge_at: string | null;
  source_first_received_at: string | null;
  vendor_observed_at: string | null;
  local_captured_at: string | null;
  source_ids: JsonRecord;
  provenance: JsonRecord;
  specification_version: string;
};

export type ProductCandidate = {
  id: string;
  scan_run_id: string;
  ticker: string;
  candidate_first_knowledge_at: string;
  materialization_rule_version: string;
  materialization_rule_hash: string;
  lifecycle_state: string;
  created_at: string;
  triggers: ProductCandidateTrigger[];
};

export type CandidateContextDetail = {
  id: string;
  product_candidate_trigger_id: string;
  anomaly_entity_type: "CONTRACT" | "EXPIRY";
  anomaly_identity: string;
  event_date: string | null;
  expiry_anchor: string | null;
  source_first_received_at: string | null;
  vendor_observed_at: string | null;
  local_captured_at: string | null;
  quote_as_of: string | null;
  contract_snapshot: JsonRecord | null;
  expiry_activity_recap: JsonRecord | null;
  volatility_context: JsonRecord;
  dealer_gex_context: JsonRecord;
  deep_dive_references: JsonRecord;
  availability: JsonRecord;
  provenance: JsonRecord;
};

export type CandidateContext = {
  id: string;
  product_candidate_id: string;
  evaluation_kind: "FIRST_KNOWLEDGE_BASELINE" | "REFRESH";
  candidate_first_knowledge_at: string;
  context_evaluated_at: string;
  price_as_of: string | null;
  context_specification_version: string;
  context_config_version: string;
  context_config_hash: string;
  price_context: JsonRecord;
  volatility_context: JsonRecord;
  dealer_gex_context: JsonRecord;
  availability: JsonRecord;
  provenance: JsonRecord;
  details: CandidateContextDetail[];
};

export type CandidateContextHistory = {
  product_candidate: {
    id: string;
    ticker: string;
    candidate_first_knowledge_at: string;
    materialization_rule_version: string;
    materialization_rule_hash: string;
  };
  baseline_state: "AVAILABLE" | "NOT_YET_AVAILABLE";
  contexts: CandidateContext[];
};

export type ZeroDteStatus = {
  ticker: string;
  expiry: string;
  dte: number;
  score_basis: string | null;
  baseline_status: string | null;
  baseline_observation_count: number | null;
  baseline_required: number;
  baseline_method: string | null;
  current_snapshot_kind:
    | "PROVISIONAL_INTRADAY"
    | "CANONICAL_SESSION_COMPLETE"
    | "LEGACY_OR_AMBIGUOUS";
  canonical_history_maturity: "AVAILABLE" | "HISTORY_IMMATURE";
};

export type RadarEvent = {
  ticker: string;
  contract_symbol: string;
  expiration: string | null;
  dte: number | null;
  right: string | null;
  strike: number | null;
  premium_usd: number | null;
  oi_diff: number | null;
  vendor_observation_date: string | null;
  archive_match_status: string;
};

export type PersistentEvidence = {
  ticker: string;
  contract_symbol: string;
  expiration: string;
  dte: number;
  persistent_state: string | null;
  history_observation_count: number | null;
  window_first_observation_date: string | null;
  window_last_observation_date: string | null;
  current_trigger_eligible: boolean;
  current_trigger_freshness: { mode: string; state: string };
  quote_as_of: string | null;
};

export type ExpiryActivityEvidence = {
  ticker: string;
  expiry: string;
  dte: number;
  score_basis: string | null;
  baseline_status: string | null;
  baseline_observation_count: number | null;
};

export type ScanPayload = {
  run_state: RunState;
  scan: ScanMetadata | null;
  specification_version?: string;
  product_candidates_state?: "AVAILABLE" | "NOT_YET_AVAILABLE";
  product_candidates?: ProductCandidate[];
  zero_dte_status?: ZeroDteStatus[];
  all_material_contract_events?: RadarEvent[];
  persistent_positioning?: PersistentEvidence[];
  unusual_expiry_activity?: ExpiryActivityEvidence[];
  research_candidates?: JsonRecord[];
  detail?: string;
};

export type SystemStatus = {
  scanner_status: string;
  latest_scan_at: string | null;
  latest_scan_status: string | null;
  latest_scan_started_at: string | null;
  latest_scan_completed_at: string | null;
  latest_scan_consumed_quota_units: number | null;
  nightwatch_status: string;
  latest_capability_refresh_at: string | null;
  quota_limit: number | null;
  quota_remaining: number | null;
  rate_limit: number | null;
  rate_limit_remaining: number | null;
  latest_request_status: number | null;
  database_status: string;
  scheduling_enabled: boolean;
  daily_collection_last_success_at: string | null;
  daily_collection_market_date: string | null;
  dealer_archive_last_vendor_observed_at: string | null;
  dealer_archive_last_captured_at: string | null;
};
