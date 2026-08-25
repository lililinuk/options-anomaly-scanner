import type {
  CandidateContext,
  ProductCandidate,
  ProductCandidateTrigger,
  RunState,
  ScanPayload,
  ZeroDteStatus,
} from "./dashboard-types";

export const triggerPresentation = {
  RADAR_EVENT: { label: "Radar", timeLayer: "OI-CONFIRMED" },
  EXPIRY_ACTIVITY: { label: "Expiry Activity", timeLayer: "SAME-DAY" },
  CONTRACT_PERSISTENCE: {
    label: "Contract Persistence",
    timeLayer: "MULTI-OBSERVATION",
  },
} as const;

export function authoritativeCandidates(payload: ScanPayload): ProductCandidate[] {
  return payload.product_candidates ?? [];
}

export function qualifyingTriggers(
  candidate: ProductCandidate,
): ProductCandidateTrigger[] {
  return candidate.triggers.filter((trigger) => trigger.qualifies_candidate);
}

export function defaultContext(
  contexts: CandidateContext[],
): CandidateContext | null {
  return (
    contexts.find(
      (context) => context.evaluation_kind === "FIRST_KNOWLEDGE_BASELINE",
    ) ??
    contexts[0] ??
    null
  );
}

export function runStateMessage(
  runState: RunState,
  productCandidatesState: ScanPayload["product_candidates_state"],
): string {
  switch (runState) {
    case "DB_OFFLINE":
      return "Database is offline. Candidate state is unavailable.";
    case "FAILED":
      return "The latest scan failed. No successful empty result is being inferred.";
    case "RUNNING":
      return "A scan is running. Candidate results are not final.";
    case "NOT_RUN":
      return "No MAG7 scan has run yet.";
    case "SUCCESS_NO_CANDIDATE":
      return productCandidatesState === "AVAILABLE"
        ? "No qualifying Product Candidate today."
        : "The scan completed, but persisted candidate materialization is unavailable.";
    case "SUCCESS_WITH_CANDIDATES":
      return productCandidatesState === "AVAILABLE"
        ? "Qualifying Product Candidates are available."
        : "The scan found candidates, but persisted Product Candidate records are unavailable for this run.";
  }
}

export function zeroDteConsequence(status: ZeroDteStatus): string {
  if (status.current_snapshot_kind === "PROVISIONAL_INTRADAY") {
    return "Provisional intraday evidence is excluded from the canonical research baseline.";
  }
  if (status.current_snapshot_kind === "LEGACY_OR_AMBIGUOUS") {
    return "Legacy or ambiguous evidence is excluded from the canonical research baseline.";
  }
  if (status.canonical_history_maturity === "HISTORY_IMMATURE") {
    return "The canonical session-complete history is still immature; the backend's existing withholding or fallback consequence remains in force.";
  }
  return "This session-complete observation has canonical identity; maturity is reported separately.";
}

