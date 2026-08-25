"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import {
  authoritativeCandidates,
  defaultContext,
  qualifyingTriggers,
  runStateMessage,
  triggerPresentation,
  zeroDteConsequence,
} from "./dashboard-semantics";
import type {
  CandidateContext,
  CandidateContextDetail,
  CandidateContextHistory,
  JsonRecord,
  ProductCandidate,
  ProductCandidateTrigger,
  ScanPayload,
  ZeroDteStatus,
} from "./dashboard-types";
import { timestampDisplay, timestampText } from "./time-display";

const empty: ScanPayload = {
  run_state: "NOT_RUN",
  scan: null,
  product_candidates_state: "NOT_YET_AVAILABLE",
  product_candidates: [],
};

function record(value: unknown): JsonRecord {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as JsonRecord)
    : {};
}

function records(value: unknown): JsonRecord[] {
  return Array.isArray(value) ? value.map(record) : [];
}

function value(source: JsonRecord, key: string): unknown {
  return source[key];
}

function display(value: unknown): string {
  if (value == null || value === "") return "—";
  if (typeof value === "number") {
    return value.toLocaleString("en-US", { maximumFractionDigits: 4 });
  }
  if (typeof value === "boolean") return value ? "YES" : "NO";
  return typeof value === "string" ? value : "—";
}

function money(value: unknown): string {
  return typeof value === "number"
    ? new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
        maximumFractionDigits: 2,
      }).format(value)
    : "—";
}

function percent(value: unknown): string {
  return typeof value === "number" ? `${(value * 100).toFixed(2)}%` : "—";
}

function MarketTimestamp({
  identity,
  value,
}: {
  identity: string;
  value: string | null | undefined;
}) {
  const formatted = timestampDisplay(value);
  return (
    <div className="time-row">
      <dt>{identity}</dt>
      <dd>
        {formatted ? (
          <time dateTime={value ?? undefined} title={`UTC ${formatted.utc}`}>
            <span>{formatted.ny}</span>
            <small>UTC {formatted.utc}</small>
          </time>
        ) : (
          "—"
        )}
      </dd>
    </div>
  );
}

function AvailabilityBadge({ value }: { value: unknown }) {
  const state = typeof value === "string" ? value : "UNAVAILABLE";
  const tone = state === "AVAILABLE" ? "available" : state === "PARTIAL" ? "partial" : "missing";
  return <span className={`availability-badge ${tone}`}>{state}</span>;
}

export function ScanDashboard() {
  const [data, setData] = useState<ScanPayload>(empty);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [selectedCandidateId, setSelectedCandidateId] = useState<string | null>(null);
  const [history, setHistory] = useState<CandidateContextHistory | null>(null);
  const [selectedContextId, setSelectedContextId] = useState<string | null>(null);
  const [contextMessage, setContextMessage] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch("/api/mag7-scan", { cache: "no-store" });
      const payload = (await response.json()) as ScanPayload;
      if (!response.ok) throw new Error(payload.detail ?? "Latest scan data is unavailable.");
      setData(payload);
      setMessage(null);
    } catch (error) {
      setData({ ...empty, run_state: "FAILED" });
      setMessage(error instanceof Error ? error.message : "Latest scan data is unavailable.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const request = window.setTimeout(() => { void load(); }, 0);
    return () => window.clearTimeout(request);
  }, [load]);

  const candidates = useMemo(() => authoritativeCandidates(data), [data]);
  const selectedCandidate =
    candidates.find((candidate) => candidate.id === selectedCandidateId) ?? null;
  const selectedContext =
    history?.contexts.find((context) => context.id === selectedContextId) ??
    defaultContext(history?.contexts ?? []);

  async function runScan() {
    setRunning(true);
    setMessage(null);
    try {
      const response = await fetch("/api/mag7-scan", { method: "POST" });
      const body = (await response.json()) as { detail?: string };
      if (!response.ok) {
        throw new Error(
          response.status === 409
            ? "A scan is already running."
            : body.detail ?? "The scan did not complete.",
        );
      }
      setSelectedCandidateId(null);
      setHistory(null);
      await load();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "The scan did not complete.");
    } finally {
      setRunning(false);
    }
  }

  async function loadContext(candidate: ProductCandidate, preferredId?: string) {
    setSelectedCandidateId(candidate.id);
    setContextMessage("Loading persisted candidate context…");
    try {
      const response = await fetch(
        `/api/candidate-context?candidateId=${encodeURIComponent(candidate.id)}`,
        { cache: "no-store" },
      );
      const payload = (await response.json()) as CandidateContextHistory & { detail?: string };
      if (!response.ok) throw new Error(payload.detail ?? "Candidate context is unavailable.");
      setHistory(payload);
      const preferred = payload.contexts.find((context) => context.id === preferredId);
      setSelectedContextId((preferred ?? defaultContext(payload.contexts))?.id ?? null);
      setContextMessage(null);
    } catch (error) {
      setHistory(null);
      setSelectedContextId(null);
      setContextMessage(
        error instanceof Error ? error.message : "Candidate context is unavailable.",
      );
    }
  }

  async function refreshContext(candidate: ProductCandidate) {
    setRefreshing(true);
    setContextMessage("Running an explicit ticker-level context refresh…");
    try {
      const response = await fetch(
        `/api/candidate-context?candidateId=${encodeURIComponent(candidate.id)}`,
        { method: "POST" },
      );
      const payload = (await response.json()) as CandidateContext & { detail?: string };
      if (!response.ok) throw new Error(payload.detail ?? "Context refresh failed.");
      await loadContext(candidate, payload.id);
    } catch (error) {
      setContextMessage(error instanceof Error ? error.message : "Context refresh failed.");
    } finally {
      setRefreshing(false);
    }
  }

  const selectedZeroDte = (data.zero_dte_status ?? []).find(
    (row) => row.ticker === selectedCandidate?.ticker,
  );

  return (
    <>
      <section className="scan-strip" aria-label="Latest scan status and controls">
        <div><span>Run state</span><strong>{data.run_state}</strong></div>
        <div><span>Started</span><strong>{timestampText(data.scan?.started_at)}</strong></div>
        <div><span>Completed</span><strong>{timestampText(data.scan?.completed_at)}</strong></div>
        <div><span>Consumed units</span><strong>{data.scan?.consumed_quota_units ?? "—"}</strong></div>
        <div className="scan-cost"><span>Run MAG7 Scan scope</span><strong>~14 paid calls · interactive scan only</strong><small>Does not rebuild the Phase 2A daily Radar/OI archive or Dealer/GEX archive.</small></div>
        <button className="run-button" type="button" onClick={runScan} disabled={running}>
          {running ? "Scanning…" : "Run MAG7 Scan"}
        </button>
      </section>
      {message && <p className="scan-message" role="alert">{message}</p>}

      <section className="candidate-section" aria-labelledby="candidate-list-title">
        <div className="section-heading candidate-heading">
          <div><span className="eyebrow">Today&apos;s Product Candidates</span><h2 id="candidate-list-title">Every persisted qualifying ticker, without ranking or filler.</h2></div>
          <span className="candidate-count">{candidates.length} persisted</span>
        </div>
        {loading ? (
          <div className="honest-empty">Loading persisted Product Candidates…</div>
        ) : candidates.length ? (
          <div className="candidate-grid">
            {candidates.map((candidate) => (
              <CandidateCard
                key={candidate.id}
                candidate={candidate}
                selected={candidate.id === selectedCandidateId}
                onOpen={() => void loadContext(candidate)}
              />
            ))}
          </div>
        ) : (
          <div className="honest-empty" data-run-state={data.run_state}>
            <strong>{runStateMessage(data.run_state, data.product_candidates_state)}</strong>
            <span>The raw Radar evidence below is not a substitute for the persisted Product Candidate list.</span>
          </div>
        )}
      </section>

      {selectedCandidate && (
        <CandidateWorkspace
          candidate={selectedCandidate}
          history={history}
          context={selectedContext}
          contextMessage={contextMessage}
          zeroDte={selectedZeroDte}
          refreshing={refreshing}
          onSelectContext={setSelectedContextId}
          onRefresh={() => void refreshContext(selectedCandidate)}
        />
      )}

      <SupportingAudit data={data} />
    </>
  );
}

function CandidateCard({
  candidate,
  selected,
  onOpen,
}: {
  candidate: ProductCandidate;
  selected: boolean;
  onOpen: () => void;
}) {
  const active = qualifyingTriggers(candidate);
  const supporting = candidate.triggers.filter((trigger) => !trigger.qualifies_candidate);
  return (
    <article className={`candidate-card ${selected ? "selected" : ""}`}>
      <div className="candidate-card-top"><div><span className="entity-label">Product Candidate</span><h3>{candidate.ticker}</h3></div><span>{candidate.triggers.length} anomalies</span></div>
      <dl><MarketTimestamp identity="Candidate first known" value={candidate.candidate_first_knowledge_at} /></dl>
      <div className="candidate-badges" aria-label="Qualifying Why Found triggers">
        {active.map((trigger) => {
          const presentation = triggerPresentation[trigger.evidence_family];
          return <span className="route-badge" key={trigger.id}>{presentation.timeLayer} · {presentation.label}</span>;
        })}
        {supporting.map((trigger) => (
          <span className="supporting-badge" key={trigger.id}>Supporting {triggerPresentation[trigger.evidence_family].label} · not qualifying</span>
        ))}
      </div>
      <button className="inspect-button" type="button" onClick={onOpen}>Inspect candidate evidence</button>
    </article>
  );
}

function CandidateWorkspace({
  candidate,
  history,
  context,
  contextMessage,
  zeroDte,
  refreshing,
  onSelectContext,
  onRefresh,
}: {
  candidate: ProductCandidate;
  history: CandidateContextHistory | null;
  context: CandidateContext | null;
  contextMessage: string | null;
  zeroDte: ZeroDteStatus | undefined;
  refreshing: boolean;
  onSelectContext: (id: string) => void;
  onRefresh: () => void;
}) {
  return (
    <section className="candidate-workspace" aria-labelledby="candidate-workspace-title">
      <header className="workspace-header">
        <div><span className="eyebrow">Candidate Header</span><h2 id="candidate-workspace-title">{candidate.ticker} research context</h2><p>Candidate = ticker/product. Anomaly = contract or expiry. Neither entity is a trade recommendation.</p></div>
        <div className="evaluation-controls">
          <label>Evaluation
            <select value={context?.id ?? ""} onChange={(event) => onSelectContext(event.target.value)} disabled={!history?.contexts.length}>
              {!history?.contexts.length && <option value="">No persisted context</option>}
              {history?.contexts.map((item) => (
                <option value={item.id} key={item.id}>{item.evaluation_kind === "FIRST_KNOWLEDGE_BASELINE" ? "Frozen baseline" : "Refresh"} · {timestampText(item.context_evaluated_at)}</option>
              ))}
            </select>
          </label>
        </div>
      </header>

      <div className="candidate-identity-grid">
        <dl><MarketTimestamp identity="Candidate first known" value={candidate.candidate_first_knowledge_at} /></dl>
        <dl><MarketTimestamp identity="Context evaluated" value={context?.context_evaluated_at} /></dl>
        <dl><MarketTimestamp identity="Price as-of" value={context?.price_as_of} /></dl>
        <div><span className="field-label">Evaluation kind</span><strong>{context?.evaluation_kind ?? "NOT_YET_AVAILABLE"}</strong></div>
      </div>

      {history?.baseline_state !== "AVAILABLE" && (
        <p className="integrity-warning">Frozen FIRST_KNOWLEDGE_BASELINE is not available. Any REFRESH remains separately labeled and is not presented as a replacement baseline.</p>
      )}
      {context?.evaluation_kind === "REFRESH" && (
        <p className="integrity-warning">Viewing REFRESH. The frozen baseline remains immutable and separately selectable.</p>
      )}
      {contextMessage && <p className="context-message" role="status">{contextMessage}</p>}

      <WhyFound candidate={candidate} />

      {context ? (
        <>
          <SharedContext context={context} />
          <AnomalyDetails context={context} candidate={candidate} />
          <DeepDive details={context.details} />
          {zeroDte && <ZeroDtePanel status={zeroDte} />}
          <ProvenanceAudit context={context} />
        </>
      ) : (
        <div className="honest-empty"><strong>Candidate context is not yet available.</strong><span>The persisted Why Found evidence above remains authoritative; no missing context is shown as zero.</span></div>
      )}

      <aside className="refresh-disclosure" aria-label="Stage 6 context refresh disclosure">
        <div><span className="eyebrow">Explicit Stage 6 context refresh</span><h3>Up to 4 ticker-level source calls</h3><p>0 per-anomaly calls · Dealer/GEX archive-only · REFRESH never replaces FIRST_KNOWLEDGE_BASELINE · no automatic refresh on page load.</p></div>
        <button type="button" onClick={onRefresh} disabled={refreshing}>{refreshing ? "Refreshing…" : "Refresh ticker context"}</button>
      </aside>
    </section>
  );
}

function WhyFound({ candidate }: { candidate: ProductCandidate }) {
  return (
    <section className="workspace-section" aria-labelledby="why-found-title">
      <div className="workspace-section-heading"><span className="eyebrow">Why Found</span><h3 id="why-found-title">Persisted trigger evidence</h3></div>
      <div className="trigger-list">
        {candidate.triggers.map((trigger) => {
          const presentation = triggerPresentation[trigger.evidence_family];
          return (
            <article key={trigger.id} className="trigger-card">
              <div className="trigger-title"><span className="route-badge">{presentation.timeLayer}</span><h4>{presentation.label}</h4><AvailabilityBadge value={trigger.qualifies_candidate ? "AVAILABLE" : "PARTIAL"} /></div>
              <p><strong>{trigger.anomaly_entity_type}</strong> · {trigger.anomaly_identity}</p>
              {!trigger.qualifies_candidate && <p className="supporting-note">Supporting Persistence only; <code>qualifies_candidate=false</code>.</p>}
              <dl className="audit-list">
                <div><dt>Qualifies candidate</dt><dd>{trigger.qualifies_candidate ? "YES" : "NO"}</dd></div>
                <div><dt>Present at first knowledge</dt><dd>{trigger.present_at_first_knowledge ? "YES" : "NO"}</dd></div>
                <div><dt>Event date</dt><dd>{display(trigger.event_date)}</dd></div>
                <MarketTimestamp identity="Source first received" value={trigger.source_first_received_at} />
                <MarketTimestamp identity="Vendor observed" value={trigger.vendor_observed_at} />
                <MarketTimestamp identity="Local captured" value={trigger.local_captured_at} />
                <MarketTimestamp identity="Trigger first known" value={trigger.trigger_first_knowledge_at} />
              </dl>
            </article>
          );
        })}
      </div>
    </section>
  );
}

function SharedContext({ context }: { context: CandidateContext }) {
  const price = record(context.price_context);
  const history = record(price.history);
  const stock = record(price.stock_state);
  const volatility = record(context.volatility_context);
  const ivRank = record(volatility.iv_rank);
  const expiryContexts = record(volatility.expiry_contexts);
  const dealer = record(context.dealer_gex_context);
  const dealerExpiries = record(dealer.expiry_contexts);
  return (
    <section className="workspace-section" aria-labelledby="shared-context-title">
      <div className="workspace-section-heading"><span className="eyebrow">Shared B1 / B2 / B3 Context</span><h3 id="shared-context-title">Rendered once for this ticker evaluation</h3></div>
      <div className="shared-context-grid">
        <article><div className="block-heading"><span>B1</span><h4>Underlying Price</h4><AvailabilityBadge value={context.availability.price} /></div><dl>
          <div><dt>Canonical close</dt><dd>{money(history.latest_regular_close_usd)}</dd></div>
          <div><dt>Latest trading date</dt><dd>{display(history.latest_trading_date)}</dd></div>
          <div><dt>1D / 5D / 20D</dt><dd>{percent(history.return_1d)} / {percent(history.return_5d)} / {percent(history.return_20d)}</dd></div>
          <div><dt>SMA20 / SMA50</dt><dd>{display(history.sma_20)} / {display(history.sma_50)}</dd></div>
          <div><dt>ATR14</dt><dd>{display(history.atr_14)}</dd></div>
          <div><dt>Distance to SMA20 / 50</dt><dd>{percent(history.distance_to_sma20_pct)} / {percent(history.distance_to_sma50_pct)}</dd></div>
          <div><dt>20-session high / low</dt><dd>{display(history.rolling_high_20)} / {display(history.rolling_low_20)}</dd></div>
          <div><dt>Trend State</dt><dd>{display(history.trend)}</dd></div>
          <div><dt>Current stock state</dt><dd>{display(stock.availability)} · {money(stock.current_price_usd)}</dd></div>
        </dl></article>
        <article><div className="block-heading"><span>B2</span><h4>Volatility</h4><AvailabilityBadge value={context.availability.volatility} /></div>
          <div className="data-warning"><strong>IV Rank provenance warning</strong><span>Raw ticker value only · vendor semantics {display(ivRank.vendor_semantics)} · core eligibility {display(ivRank.core_eligibility || "WITHHOLD_PENDING_PROVENANCE")} · no LOW/MID/HIGH classification.</span></div>
          <dl><div><dt>Raw IV Rank</dt><dd>{display(ivRank.value)}</dd></div><div><dt>IV Rank as-of</dt><dd>{display(ivRank.as_of)}</dd></div></dl>
          <div className="expiry-context-list">{Object.entries(expiryContexts).map(([expiry, raw]) => {
            const item = record(raw);
            const shorter = record(item.nearest_shorter_node);
            const longer = record(item.nearest_longer_node);
            return <div key={expiry}><strong>{expiry}</strong><span>Candidate IV {display(item.candidate_term_iv)} · {display(item.exact_match_status)}</span><small>Expanded: shorter {display(shorter.implied_vol_pct)} · longer {display(longer.implied_vol_pct)} · topology {display(item.topology)}</small></div>;
          })}</div>
        </article>
        <article className="dealer-shared"><div className="block-heading"><span>B3</span><h4>Dealer / GEX · archive-only</h4><AvailabilityBadge value={dealer.availability} /></div>
          <dl><div><dt>Source</dt><dd>{display(dealer.source)}</dd></div><MarketTimestamp identity="Vendor observed" value={typeof dealer.vendor_observed_at === "string" ? dealer.vendor_observed_at : null} /><MarketTimestamp identity="Local captured" value={typeof dealer.local_captured_at === "string" ? dealer.local_captured_at : null} /></dl>
          <div className="gex-grid">{Object.entries(dealerExpiries).map(([expiry, raw]) => <GexExpiry key={expiry} expiry={expiry} context={record(raw)} />)}</div>
        </article>
      </div>
    </section>
  );
}

function GexExpiry({ expiry, context }: { expiry: string; context: JsonRecord }) {
  const floor = record(context.primary_floor);
  const upper = record(context.primary_upper_positive_gex_node);
  const lower = record(context.immediate_below_floor_node);
  return <div className="gex-expiry"><strong>{expiry}</strong><span>Spot {money(context.spot_usd)} · {display(context.availability)}</span><dl>
    <div><dt>Primary Floor</dt><dd>{display(floor.strike_usd)} · raw net GEX {display(floor.net_dealer_gex_usd)} · {display(floor.sign)}</dd></div>
    <div><dt>Primary Upper Positive-GEX Node</dt><dd>{display(upper.strike_usd)} · raw net GEX {display(upper.net_dealer_gex_usd)} · {display(upper.sign)}</dd></div>
    <div><dt>Immediate Below-Floor Node</dt><dd>{display(lower.strike_usd)} · raw net GEX {display(lower.net_dealer_gex_usd)} · {display(lower.sign)}</dd></div>
  </dl></div>;
}

function AnomalyDetails({ context, candidate }: { context: CandidateContext; candidate: ProductCandidate }) {
  return (
    <section className="workspace-section" aria-labelledby="anomaly-details-title">
      <div className="workspace-section-heading"><span className="eyebrow">Anomaly Details · B4</span><h3 id="anomaly-details-title">One distinct detail per persisted trigger</h3></div>
      <div className="anomaly-list">{context.details.map((detail) => {
        const trigger = candidate.triggers.find((item) => item.id === detail.product_candidate_trigger_id);
        return <AnomalyDetail key={detail.id} detail={detail} trigger={trigger} />;
      })}</div>
    </section>
  );
}

function AnomalyDetail({ detail, trigger }: { detail: CandidateContextDetail; trigger?: ProductCandidateTrigger }) {
  const contract = record(detail.contract_snapshot);
  const expiry = record(detail.expiry_activity_recap);
  const location = record(contract.strike_location);
  return (
    <details className="anomaly-detail" open>
      <summary><span>{trigger ? triggerPresentation[trigger.evidence_family].timeLayer : "ANOMALY"}</span><strong>{detail.anomaly_entity_type} · {detail.anomaly_identity}</strong><AvailabilityBadge value={detail.availability.positioning_provenance} /></summary>
      <div className="anomaly-body">
        {detail.anomaly_entity_type === "CONTRACT" ? (
          <dl>
            <div><dt>Contract / expiry</dt><dd>{display(contract.contract_symbol)} / {display(contract.expiration)}</dd></div>
            <div><dt>Right / strike</dt><dd>{display(contract.right)} / {display(contract.strike)} <small>Call and Put are contract rights, not direction.</small></dd></div>
            <div><dt>DTE / anchor</dt><dd>{display(contract.dte_at_detection)} · {display(contract.dte_anchor_date)} · {display(contract.dte_anchor_type)}</dd></div>
            <div><dt>Strike vs spot</dt><dd>{display(location.strike_distance_usd)} USD · {percent(location.strike_distance_pct)} · {display(location.strike_distance_atr)} ATR</dd></div>
            <div><dt>Contract IV / Delta</dt><dd>{display(contract.contract_iv)} / {display(contract.delta)}</dd></div>
            <div><dt>Bid / ask / spread</dt><dd>{display(contract.bid)} / {display(contract.ask)} / {percent(contract.spread_pct)}</dd></div>
            <MarketTimestamp identity="Quote as-of" value={detail.quote_as_of} />
          </dl>
        ) : (
          <dl>
            <div><dt>Expiry identity</dt><dd>{display(expiry.expiration)}</dd></div>
            <div><dt>DTE / anchor</dt><dd>{display(expiry.dte_at_detection)} · {display(expiry.dte_anchor_date)}</dd></div>
            <div><dt>Call / Put volume</dt><dd>{display(expiry.call_volume)} / {display(expiry.put_volume)}</dd></div>
            <div><dt>Call / Put OI</dt><dd>{display(expiry.call_oi)} / {display(expiry.put_oi)}</dd></div>
            <div><dt>Expiry activity recap</dt><dd>{display(expiry.same_day_activity_score)} · basis {display(expiry.score_basis)}</dd></div>
            <div><dt>Expiry volatility / GEX</dt><dd>{display(detail.availability.volatility)} / {display(detail.availability.dealer_gex)}</dd></div>
          </dl>
        )}
        <dl className="detail-time-grid">
          <div><dt>Event date</dt><dd>{display(detail.event_date)}</dd></div>
          <MarketTimestamp identity="Source first received" value={detail.source_first_received_at} />
          <MarketTimestamp identity="Vendor observed" value={detail.vendor_observed_at} />
          <MarketTimestamp identity="Local captured" value={detail.local_captured_at} />
        </dl>
      </div>
    </details>
  );
}

function DeepDive({ details }: { details: CandidateContextDetail[] }) {
  const items = details.flatMap((detail) => {
    const deep = record(detail.deep_dive_references);
    const structure = record(deep.structure);
    const structures = records(deep.structures);
    const validClusters = records(deep.valid_clusters);
    return structure.classification || structures.length || validClusters.length
      ? [{ detail, structure, structures, validClusters }]
      : [];
  });
  return (
    <section className="workspace-section" aria-labelledby="deep-dive-title">
      <div className="workspace-section-heading"><span className="eyebrow">Deep Dive</span><h3 id="deep-dive-title">Valid-only Structure and Cluster context</h3></div>
      {items.length ? <div className="deep-dive-grid">{items.map(({ detail, structure, structures, validClusters }) => (
        <article key={detail.id}><h4>{detail.anomaly_identity}</h4>{structure.classification ? <p>Accepted Structure · {display(structure.classification)} · preserved score {display(structure.score)}</p> : null}{structures.map((item, index) => <p key={`s-${index}`}>Accepted Structure · {display(item.classification)} · preserved score {display(item.score)}</p>)}{validClusters.map((item, index) => <p key={`c-${index}`}>Valid Cluster · {display(item.classification)} · {display(item.right)} · strikes {display(item.min_strike)}–{display(item.max_strike)}</p>)}</article>
      ))}</div> : <div className="honest-empty"><strong>No accepted Deep Dive context is available.</strong><span>Invalid or subthreshold structures are not presented positively.</span></div>}
    </section>
  );
}

function ZeroDtePanel({ status }: { status: ZeroDteStatus }) {
  return (
    <section className="workspace-section zero-dte-panel" aria-labelledby="zero-dte-title">
      <div className="workspace-section-heading"><span className="eyebrow">0DTE · G29</span><h3 id="zero-dte-title">Session identity and canonical-history maturity</h3></div>
      <div className="zero-dte-grid">
        <div><span>Current status</span><strong>{status.current_snapshot_kind}</strong></div>
        <div><span>Canonical history</span><strong>{status.baseline_observation_count ?? 0}/{status.baseline_required} · {status.canonical_history_maturity}</strong></div>
        <div><span>Basis attribution</span><strong>{status.score_basis ?? status.baseline_method ?? "—"}</strong></div>
      </div>
      <p>{zeroDteConsequence(status)}</p>
    </section>
  );
}

function ProvenanceAudit({ context }: { context: CandidateContext }) {
  return (
    <section className="workspace-section" aria-labelledby="provenance-title">
      <div className="workspace-section-heading"><span className="eyebrow">Supporting / Audit / Provenance</span><h3 id="provenance-title">Immutable identity and raw trace</h3></div>
      <details className="json-audit"><summary>Inspect candidate context provenance</summary><pre>{JSON.stringify(context.provenance, null, 2)}</pre></details>
      <p className="audit-version">{context.context_specification_version} · {context.context_config_version} · config hash {context.context_config_hash}</p>
    </section>
  );
}

function SupportingAudit({ data }: { data: ScanPayload }) {
  const radar = (data.all_material_contract_events ?? []).slice(0, 15);
  return (
    <section className="supporting-audit" aria-labelledby="supporting-audit-title">
      <div className="section-heading"><span className="eyebrow">Supporting / Raw Evidence</span><h2 id="supporting-audit-title">Engine tables follow the Product Candidate decision layer.</h2></div>
      <details className="raw-panel"><summary>Raw / scoped Radar evidence view</summary><div className="scope-disclosure"><strong>Not the Product Candidate list.</strong> Latest eligible vendor date per ticker; sorted by premium and absolute ΔOI; this view displays the first 15 rows.</div><div className="table-wrap"><table><thead><tr><th>Ticker</th><th>Contract</th><th>Expiry / DTE</th><th>Right / Strike</th><th>Premium</th><th>ΔOI</th><th>Vendor event date</th><th>Archive</th></tr></thead><tbody>{radar.map((row) => <tr key={`${row.ticker}-${row.contract_symbol}-${row.vendor_observation_date}`}><td>{row.ticker}</td><td>{row.contract_symbol}</td><td>{display(row.expiration)} / {display(row.dte)}</td><td>{display(row.right)} / {display(row.strike)}</td><td>{money(row.premium_usd)}</td><td>{display(row.oi_diff)}</td><td>{display(row.vendor_observation_date)}</td><td>{display(row.archive_match_status)}</td></tr>)}</tbody></table></div></details>
      <details className="raw-panel"><summary>Multi-observation Contract Persistence evidence</summary><div className="table-wrap"><table><thead><tr><th>Ticker</th><th>Contract</th><th>Expiry / DTE</th><th>State</th><th>Observation window</th><th>Current trigger</th><th>Quote as-of</th></tr></thead><tbody>{(data.persistent_positioning ?? []).map((row) => <tr key={row.contract_symbol}><td>{row.ticker}</td><td>{row.contract_symbol}</td><td>{row.expiration} / {row.dte}</td><td>{display(row.persistent_state)}</td><td>{display(row.window_first_observation_date)} → {display(row.window_last_observation_date)} · {display(row.history_observation_count)} observations</td><td>{row.current_trigger_eligible ? "QUALIFYING" : `SUPPORTING · ${row.current_trigger_freshness.state}`}</td><td>{display(row.quote_as_of)}</td></tr>)}</tbody></table></div></details>
      <details className="raw-panel"><summary>Same-day Expiry Activity evidence</summary><div className="table-wrap"><table><thead><tr><th>Ticker</th><th>Expiry / DTE</th><th>Basis</th><th>0DTE baseline</th></tr></thead><tbody>{(data.unusual_expiry_activity ?? []).map((row) => <tr key={`${row.ticker}-${row.expiry}`}><td>{row.ticker}</td><td>{row.expiry} / {row.dte}</td><td>{display(row.score_basis)}</td><td>{display(row.baseline_status)} · {display(row.baseline_observation_count)}</td></tr>)}</tbody></table></div></details>
      <details className="raw-panel"><summary>Legacy/non-authoritative Product Candidate projection audit</summary><div className="scope-disclosure">Supporting audit only. Persisted Product Candidate cards above are authoritative for candidate existence.</div><pre>{JSON.stringify(data.research_candidates ?? [], null, 2)}</pre></details>
    </section>
  );
}
