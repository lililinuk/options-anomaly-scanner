"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

type Scan = {
  status: string;
  consumed_quota_units: number;
  network_attempts: number;
  archive_status?: string | null;
  archive_completed_at?: string | null;
};

type RunState =
  | "DB_OFFLINE"
  | "NOT_RUN"
  | "RUNNING"
  | "FAILED"
  | "SUCCESS_NO_CANDIDATE"
  | "SUCCESS_WITH_CANDIDATES";

type RadarEvent = {
  ticker: string;
  contract_symbol: string;
  expiration: string | null;
  dte: number | null;
  right: string | null;
  strike: number | null;
  premium_usd: number | null;
  oi_diff: number | null;
  oi_change: number | null;
  volume: number | null;
  trades: number | null;
  vendor_observation_date: string | null;
  archive_match_status: string;
  archive_completeness: string;
  radar_scope: string | null;
  previous_oi: number | null;
  current_oi: number | null;
  premium_per_trade: number | null;
  volume_per_trade: number | null;
  avg_price_usd: number | null;
  last_bid_usd: number | null;
  last_ask_usd: number | null;
  last_fill_usd: number | null;
  vendor_rank: number | null;
  contract_structure_score: number | null;
  contract_persistent_score: number | null;
  risk_flags: string[];
};

type Persistent = {
  ticker: string;
  contract_symbol: string;
  expiration: string;
  dte: number;
  right: string;
  strike: number;
  oi_change_3: number | null;
  oi_change_5: number | null;
  oi_change_10: number | null;
  oi_growth: number | null;
  persistent_state: string | null;
  persistent_score: number | null;
  winning_window: number | null;
  history_confidence: string;
  history_observation_count: number | null;
  history_required: number;
};

type ExpiryActivity = {
  ticker: string;
  expiry: string;
  dte: number;
  same_day_activity_score: number | null;
  volume_share: number | null;
  volume_share_points: number | null;
  neighbor_ratio: number | null;
  neighbor_points: number | null;
  score_basis: string | null;
  standard_monthly_inferred: boolean;
  monthly_context_source: string | null;
  baseline_status: string | null;
  baseline_observation_count: number | null;
};

type ResearchCandidate = {
  entity_type: "CONTRACT" | "EXPIRY_ONLY";
  ticker: string;
  contract_or_expiry: string;
  expiration: string | null;
  trigger_sources: string[];
  radar_premium_usd: number | null;
  radar_oi_diff: number | null;
  persistent_score: number | null;
  expiry_activity_score: number | null;
  structure_score: number | null;
  archive_completeness: string | null;
  risk_flags: string[];
};

type Phase2bContext = {
  candidate: { ticker: string; contract_symbol: string; expiration: string; dte: number | null;
    right: string; strike: number; trigger_sources: string[]; direction: string };
  phase2a: Record<string, unknown>;
  price: { stock_state: Record<string, unknown>; history: Record<string, unknown>;
    strike_location: Record<string, unknown> };
  volatility: { iv_rank: Record<string, unknown>; term: Record<string, unknown> };
  dealer: Record<string, unknown>;
  execution: Record<string, unknown>;
  data_quality: Record<string, unknown>;
  timestamps: Record<string, unknown>;
  specification_version: string;
  config_version: string;
  evaluated_at: string;
  v2_state: {
    positioning: Record<string, unknown>;
    price: Record<string, unknown>;
    volatility: Record<string, unknown>;
    dealer_gex: Record<string, unknown>;
    execution: Record<string, unknown>;
    research_readiness: Record<string, unknown>;
    phase2a_provenance: Record<string, unknown>;
    direction: string;
    specification_version: string;
  } | null;
  v3_research_workspace: {
    specification_version: string;
    contract_identity: Record<string, unknown>;
    opportunity_positioning: Record<string, unknown>;
    underlying_price: Record<string, unknown>;
    trade_structure: {
      volatility: Record<string, unknown>;
      dealer_gex: Record<string, unknown>;
      execution: Record<string, unknown>;
    };
    provenance: Record<string, unknown>;
    rule_versions: Record<string, unknown>;
    config_version: string;
    created_at: string;
  } | null;
};

type Payload = {
  run_state: RunState;
  scan: Scan | null;
  specification_version?: string;
  threshold_profile?: { profile_id: string; version: string };
  radar_filters?: { min_premium_usd: number; min_abs_oi_diff: number };
  latest_contract_events?: RadarEvent[];
  all_material_contract_events?: RadarEvent[];
  persistent_positioning?: Persistent[];
  unusual_expiry_activity?: ExpiryActivity[];
  research_candidates?: ResearchCandidate[];
};

const empty: Payload = { run_state: "NOT_RUN", scan: null };

function emptyMessage(runState: RunState, successfulEmptyMessage: string): string {
  if (runState === "FAILED" || runState === "DB_OFFLINE") {
    return "Latest scan data is unavailable; no successful empty result is being inferred.";
  }
  if (runState === "RUNNING") return "A scan is currently running; results are not final.";
  if (runState === "NOT_RUN") return "No MAG7 scan has run yet.";
  return successfulEmptyMessage;
}

function display(value: string | number | null): string {
  if (value == null || value === "") return "—";
  if (typeof value === "number") return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
  if (/^\d{4}-\d{2}-\d{2}T/.test(value)) return new Date(value).toLocaleString();
  return value;
}

function money(value: number | null): string {
  return value == null ? "—" : new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(value);
}

function percent(value: number | null): string {
  return value == null ? "—" : `${(value * 100).toFixed(1)}%`;
}

export function ScanDashboard() {
  const [data, setData] = useState<Payload>(empty);
  const [running, setRunning] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [ticker, setTicker] = useState("ALL");
  const [right, setRight] = useState("ALL");
  const [minPremium, setMinPremium] = useState<number | null>(null);
  const [minOiDiff, setMinOiDiff] = useState<number | null>(null);
  const [minDte, setMinDte] = useState(0);
  const [maxDte, setMaxDte] = useState(180);
  const [showAll, setShowAll] = useState(false);
  const [context, setContext] = useState<Phase2bContext | null>(null);
  const [contextMessage, setContextMessage] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const response = await fetch("/api/mag7-scan", { cache: "no-store" });
      const payload = (await response.json()) as Payload & { detail?: string };
      if (!response.ok) throw new Error(payload.detail ?? "Latest scan data is unavailable.");
      setData(payload);
      setMessage(null);
      setMinPremium((current) => current ?? payload.radar_filters?.min_premium_usd ?? null);
      setMinOiDiff((current) => current ?? payload.radar_filters?.min_abs_oi_diff ?? null);
    } catch (error) {
      setData({ run_state: "FAILED", scan: null });
      setMessage(error instanceof Error ? error.message : "Latest scan data is unavailable.");
    }
  }, []);

  useEffect(() => {
    const request = window.setTimeout(() => { void load(); }, 0);
    return () => window.clearTimeout(request);
  }, [load]);

  const events = useMemo(() => {
    const rows = data.all_material_contract_events ?? [];
    const filtered = rows.filter((row) =>
      (ticker === "ALL" || row.ticker === ticker)
      && (right === "ALL" || row.right === right)
      && (row.premium_usd ?? -1) >= (minPremium ?? 0)
      && Math.abs(row.oi_diff ?? 0) >= (minOiDiff ?? 0)
      && (row.dte == null || (row.dte >= minDte && row.dte <= maxDte))
    );
    return showAll ? filtered : filtered.slice(0, 15);
  }, [data, ticker, right, minPremium, minOiDiff, minDte, maxDte, showAll]);

  async function run() {
    setRunning(true);
    setMessage(null);
    try {
      const response = await fetch("/api/mag7-scan", { method: "POST" });
      if (!response.ok) throw new Error(response.status === 409 ? "已有掃描正在執行。" : "掃描未能完成。請查看後端狀態。");
      await load();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "掃描未能完成。");
    } finally {
      setRunning(false);
    }
  }

  async function openContext(contract: string) {
    if (!/^[A-Z0-9]{1,32}$/.test(contract)) return;
    setContextMessage("Loading persisted confirmation context…");
    const response = await fetch(`/api/candidate-context?contract=${encodeURIComponent(contract)}`, {
      cache: "no-store",
    });
    if (!response.ok) {
      setContext(null);
      setContextMessage(response.status === 404
        ? "Phase 2B context has not been captured for this candidate yet."
        : "Confirmation context is temporarily unavailable.");
      return;
    }
    setContext((await response.json()) as Phase2bContext);
    setContextMessage(null);
  }

  return (
    <>
      <section className="scan-strip" aria-label="Latest scan status">
        <div><span>Specification</span><strong>{data.specification_version ?? "signal_spec_v1.3_phase2a"}</strong></div>
        <div><span>Scan status</span><strong>{data.run_state}</strong></div>
        <div><span>Radar profile</span><strong>{data.threshold_profile ? `${data.threshold_profile.profile_id} · ${data.threshold_profile.version}` : "—"}</strong></div>
        <div><span>Archive freshness</span><strong>{data.scan?.archive_completed_at ? `${data.scan.archive_status} · ${display(data.scan.archive_completed_at)}` : "—"}</strong></div>
        <button className="run-button" type="button" onClick={run} disabled={running}>{running ? "Scanning…" : "Run MAG7 Scan"}</button>
      </section>
      {message && <p className="scan-message" role="alert">{message}</p>}

      <section className="panel results-panel" aria-labelledby="events-title">
        <div className="panel-header"><div><span className="eyebrow">Route 1 · Radar Event</span><h2 id="events-title">Latest Contract Events</h2></div><small>Aggregate contract activity evidence · not proof of one individual order</small></div>
        <div className="radar-filters" aria-label="Radar presentation filters">
          <label>Ticker<select value={ticker} onChange={(event) => setTicker(event.target.value)}><option>ALL</option>{["AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "TSLA"].map((item) => <option key={item}>{item}</option>)}</select></label>
          <label>Min Premium<input type="number" value={minPremium ?? ""} onChange={(event) => setMinPremium(event.target.value === "" ? null : Number(event.target.value))} /></label>
          <label>Min |ΔOI|<input type="number" value={minOiDiff ?? ""} onChange={(event) => setMinOiDiff(event.target.value === "" ? null : Number(event.target.value))} /></label>
          <label>DTE from<input type="number" value={minDte} onChange={(event) => setMinDte(Number(event.target.value))} /></label>
          <label>DTE to<input type="number" value={maxDte} onChange={(event) => setMaxDte(Number(event.target.value))} /></label>
          <label>Right<select value={right} onChange={(event) => setRight(event.target.value)}><option>ALL</option><option value="C">Call</option><option value="P">Put</option></select></label>
          <button className="secondary-button" type="button" onClick={() => setShowAll((value) => !value)}>{showAll ? "Top 15" : "Inspect all"}</button>
        </div>
        <div className="table-wrap"><table><thead><tr><th>Ticker</th><th>Contract</th><th>Expiry / DTE</th><th>Right</th><th>Strike</th><th>Premium</th><th>ΔOI</th><th>OI Change %</th><th>Volume</th><th>Trades</th><th>Vendor date</th><th>Archive</th></tr></thead>
          <tbody>{events.length ? events.map((row) => <tr key={`${row.ticker}-${row.contract_symbol}-${row.vendor_observation_date}`}><td>{row.ticker}</td><td><details><summary>{row.contract_symbol}</summary><div className="event-detail">Prev / current OI: {display(row.previous_oi)} / {display(row.current_oi)}<br />Premium / trade: {money(row.premium_per_trade)} · Volume / trade: {display(row.volume_per_trade)}<br />Avg / bid / ask / fill: {display(row.avg_price_usd)} / {display(row.last_bid_usd)} / {display(row.last_ask_usd)} / {display(row.last_fill_usd)}<br />Vendor rank: {display(row.vendor_rank)} · Structure: {display(row.contract_structure_score)} · Persistent: {display(row.contract_persistent_score)}<br />Flags: {row.risk_flags.length ? row.risk_flags.join(", ") : "—"}</div></details></td><td>{row.expiration ? `${row.expiration} / ${display(row.dte)}` : "UNJOINED"}</td><td>{display(row.right)}</td><td>{display(row.strike)}</td><td>{money(row.premium_usd)}</td><td>{display(row.oi_diff)}</td><td>{percent(row.oi_change)}</td><td>{display(row.volume)}</td><td>{display(row.trades)}</td><td>{display(row.vendor_observation_date)}</td><td><span className="context-badge">{row.archive_match_status === "EXACT" ? row.archive_completeness : "UNJOINED"}</span>{row.radar_scope === "LONG_DTE_RADAR_WATCH" && <span className="context-badge">LONG_DTE_RADAR_WATCH</span>}</td></tr>) : <tr><td colSpan={12}><div className="empty-state"><h3>{emptyMessage(data.run_state, "No qualifying Radar Material Events")}</h3><p>Absence from this vendor-ranked subset is missing evidence, not negative evidence.</p></div></td></tr>}</tbody>
        </table></div>
      </section>

      <section className="panel results-panel" aria-labelledby="persistent-title">
        <div className="panel-header"><div><span className="eyebrow">Route 2 · Multi-session OI</span><h2 id="persistent-title">Persistent Positioning</h2></div><small>Build and decline are descriptive; neither implies investor direction</small></div>
        <div className="table-wrap"><table><thead><tr><th>Ticker</th><th>Contract</th><th>Expiry / DTE</th><th>Right / Strike</th><th>3 / 5 / 10 session ΔOI</th><th>OI Growth</th><th>State</th><th>Score</th><th>Winning window</th><th>History</th></tr></thead>
          <tbody>{(data.persistent_positioning ?? []).length ? data.persistent_positioning?.map((row) => <tr key={row.contract_symbol}><td>{row.ticker}</td><td>{row.contract_symbol}</td><td>{row.expiration} / {row.dte}</td><td>{row.right} / {display(row.strike)}</td><td>{display(row.oi_change_3)} / {display(row.oi_change_5)} / {display(row.oi_change_10)}</td><td>{percent(row.oi_growth)}</td><td>{display(row.persistent_state)}</td><td>{display(row.persistent_score)}</td><td>{display(row.winning_window)}</td><td>{row.history_confidence === "INSUFFICIENT" ? `Persistent history: ${row.history_observation_count ?? 0} / ${row.history_required} minimum observations` : `${row.history_confidence} · ${row.history_observation_count ?? 0} sessions`}</td></tr>) : <tr><td colSpan={10}>{emptyMessage(data.run_state, "Persistent history is still collecting; missing history is not zero.")}</td></tr>}</tbody>
        </table></div>
      </section>

      <section className="panel results-panel" aria-labelledby="activity-title">
        <div className="panel-header"><div><span className="eyebrow">Route 3 · Expiry concentration</span><h2 id="activity-title">Unusual Expiry Activity</h2></div><small>Accepted v1.2 Same-Day logic retained</small></div>
        <div className="table-wrap"><table><thead><tr><th>Ticker</th><th>Expiry / DTE</th><th>Activity Score</th><th>Volume Share</th><th>VS Points</th><th>Neighbor Ratio</th><th>Neighbor Points</th><th>Score Basis</th><th>Context</th><th>0DTE baseline</th></tr></thead>
          <tbody>{(data.unusual_expiry_activity ?? []).length ? data.unusual_expiry_activity?.map((row) => <tr key={`${row.ticker}-${row.expiry}`}><td>{row.ticker}</td><td>{row.expiry} / {row.dte}</td><td>{display(row.same_day_activity_score)}</td><td>{percent(row.volume_share)}</td><td>{display(row.volume_share_points)}</td><td>{display(row.neighbor_ratio)}</td><td>{display(row.neighbor_points)}</td><td>{display(row.score_basis)}</td><td>{row.standard_monthly_inferred ? <span className="context-badge" title="Calendar inferred; score weight 0">Monthly OPEX · INFERRED</span> : "—"}</td><td>{row.baseline_status ? `${row.baseline_status} · ${row.baseline_observation_count ?? 0}` : "—"}</td></tr>) : <tr><td colSpan={10}>{emptyMessage(data.run_state, "No current expiry route candidate. Unavailable values remain unknown, not zero.")}</td></tr>}</tbody>
        </table></div>
      </section>

      <section className="panel results-panel" aria-labelledby="deep-title">
        <div className="panel-header"><div><span className="eyebrow">Research workspace</span><h2 id="deep-title">Deep Dive / Research Candidates</h2></div><small>No universal conviction score</small></div>
        <div className="table-wrap"><table><thead><tr><th>Ticker</th><th>Contract / Expiry</th><th>Trigger Sources</th><th>Radar Premium / ΔOI</th><th>Persistent</th><th>Expiry Activity</th><th>Structure</th><th>Archive</th><th>Flags</th></tr></thead>
          <tbody>{(data.research_candidates ?? []).length ? data.research_candidates?.map((row) => <tr key={`${row.ticker}-${row.contract_or_expiry}`}><td>{row.ticker}</td><td>{row.entity_type === "CONTRACT" ? <button className="context-link" type="button" onClick={() => void openContext(row.contract_or_expiry)}>{row.contract_or_expiry}</button> : row.contract_or_expiry}</td><td>{row.trigger_sources.map((source) => <span className="route-badge" key={source}>{source}</span>)}</td><td>{money(row.radar_premium_usd)} / {display(row.radar_oi_diff)}</td><td>{display(row.persistent_score)}</td><td>{display(row.expiry_activity_score)}</td><td>{display(row.structure_score)}</td><td>{display(row.archive_completeness)}</td><td>{row.risk_flags.length ? row.risk_flags.join(", ") : "—"}</td></tr>) : <tr><td colSpan={9}>{emptyMessage(data.run_state, "No route-qualified research candidate is available yet.")}</td></tr>}</tbody>
        </table></div>
        {contextMessage && <p className="context-message" role="status">{contextMessage}</p>}
        {context && <ConfirmationContext context={context} />}
      </section>
    </>
  );
}

function value(source: Record<string, unknown>, key: string): string {
  const item = source[key];
  if (typeof item === "boolean") return item ? "YES" : "NO";
  return display(typeof item === "number" || typeof item === "string" ? item : null);
}

function ConfirmationContext({ context }: { context: Phase2bContext }) {
  const workspace = context.v3_research_workspace;
  if (!workspace) {
    return <div className="confirmation-workspace" aria-label="Phase 2B confirmation context">
      <div className="confirmation-heading"><div><span className="eyebrow">Phase 2B · Preserved evidence</span><h3>{context.candidate.contract_symbol}</h3></div></div>
      <p className="context-message" role="status">The v3 research workspace has not been materialized for this exact contract. No contract-level evidence is fabricated.</p>
    </div>;
  }
  const identity = workspace.contract_identity;
  const opportunity = workspace.opportunity_positioning;
  const activity = (opportunity.contract_activity ?? {}) as Record<string, unknown>;
  const openInterest = (opportunity.open_interest ?? {}) as Record<string, unknown>;
  const positioning = (opportunity.positioning_evidence ?? {}) as Record<string, unknown>;
  const presence = (positioning.presence_states ?? {}) as Record<string, unknown>;
  const flow = (opportunity.observed_flow_direction ?? {}) as Record<string, unknown>;
  const price = workspace.underlying_price;
  const priceAudit = (price.audit ?? {}) as Record<string, unknown>;
  const priceAuditFields = (priceAudit.source_fields ?? {}) as Record<string, unknown>;
  const volatility = workspace.trade_structure.volatility;
  const dealer = workspace.trade_structure.dealer_gex;
  const execution = workspace.trade_structure.execution;
  const floor = (dealer.primary_floor ?? {}) as Record<string, unknown>;
  const upper = (dealer.primary_upper_positive_gex_node ?? {}) as Record<string, unknown>;
  const lower = (dealer.immediate_below_floor_node ?? {}) as Record<string, unknown>;
  const adjacent = (dealer.adjacent_expiry_context ?? {}) as Record<string, unknown>;
  const previous = (adjacent.previous ?? {}) as Record<string, unknown>;
  const anchor = (adjacent.anchor ?? {}) as Record<string, unknown>;
  const next = (adjacent.next ?? {}) as Record<string, unknown>;
  const audit = (dealer.audit ?? {}) as Record<string, unknown>;
  const sourceTimestamps = (workspace.provenance.source_timestamps ?? {}) as Record<string, unknown>;
  const rightLabel = value(identity, "right_label");
  const dealerUnavailable = dealer.availability !== "AVAILABLE";
  return <div className="confirmation-workspace" aria-label="Phase 2B confirmation context">
    <div className="confirmation-heading"><div><span className="eyebrow">Phase 2B v3 · Candidate research workspace</span><h3>{value(identity, "ticker")} {value(identity, "expiration")} ${value(identity, "strike")} {rightLabel}</h3><p className="contract-subheading">DTE at Detection: {value(identity, "dte_at_detection")} · Bucket: {value(identity, "bucket_at_detection")} · {value(identity, "contract_symbol")}</p></div></div>
    <div className="confirmation-grid">
      <article className="role-card"><span className="role-number">Role 1</span><h4>Why Found / Positioning</h4><p>Why this exact contract is worth investigating. This evidence does not establish underlying direction or buyer/seller initiation.</p></article>
      <ContextCard title="Contract Activity" rows={[["Premium Activity", money(typeof activity.premium_activity_usd === "number" ? activity.premium_activity_usd : null)], ["Volume", value(activity, "volume")], ["Trades", value(activity, "trades")], ["Radar observation", value(activity, "radar_observation_date")]]} />
      <ContextCard title="Open Interest" rows={[["ΔOI", value(openInterest, "delta_oi")], ["Relative OI change", percent(typeof openInterest.relative_oi_change === "number" ? openInterest.relative_oi_change : null)], ["Current OI", value(openInterest, "current_oi")], ["Radar observation", value(openInterest, "radar_observation_date")], ["Chain observation", value(openInterest, "chain_observation_date")]]} />
      <article><h4>Positioning Evidence</h4><dl><div><dt>Radar Event</dt><dd>{value(presence, "radar_event")}</dd></div><div><dt>Evidence Breadth</dt><dd>{value(positioning, "evidence_breadth")}</dd></div><div><dt>Contract Structure</dt><dd>{value(positioning, "structure_score")}</dd></div><div><dt>Contract Persistence</dt><dd>{value(presence, "contract_persistence")}</dd></div><div><dt>Expiry Persistence</dt><dd>{value(presence, "expiry_persistence")}</dd></div><div><dt>Cluster</dt><dd>{value(presence, "cluster")}</dd></div></dl></article>
      <article><h4>Observed Flow Direction</h4><p className="compact-state">{value(flow, "state")}</p><details><summary>Why?</summary><p>Current persisted evidence does not establish buyer/seller initiation, opening/closing intent, a spread, a hedge, or another multi-leg structure. UNRESOLVED is not Neutral.</p><small>{value(flow, "reason")}</small></details></article>
      <article className="role-card"><span className="role-number">Role 2</span><h4>Underlying Price</h4><p>Accepted factual price structure. It is market context, not a BUY/SELL or option recommendation.</p></article>
      <article><h4>Underlying Price</h4><dl><div><dt>Trend</dt><dd><strong>{value(price, "trend")}</strong></dd></div><div><dt>Latest Regular Close</dt><dd>{value(price, "latest_regular_close_usd")}</dd></div><div><dt>SMA20 / SMA50</dt><dd>{value(price, "sma_20")} / {value(price, "sma_50")}</dd></div><div><dt>1D / 5D / 20D</dt><dd>{percent(typeof price.return_1d === "number" ? price.return_1d : null)} / {percent(typeof price.return_5d === "number" ? price.return_5d : null)} / {percent(typeof price.return_20d === "number" ? price.return_20d : null)}</dd></div><div><dt>ATR14</dt><dd>{value(price, "atr_14")}</dd></div><div><dt>Price Quality</dt><dd>{value(price, "availability")} · {value(price, "coverage_quality")}</dd></div></dl><details><summary>View price audit</summary><p>Accepted state: {value(priceAudit, "accepted_state")}</p><p>Close &gt; SMA20: {value(priceAuditFields, "close_gt_sma20")} · SMA20 &gt; SMA50: {value(priceAuditFields, "sma20_gt_sma50")}</p><p>Rule: {value(priceAudit, "rule")}</p></details></article>
      <article className="role-card"><span className="role-number">Role 3</span><h4>Trade-Structure / Path Context</h4><p>Volatility, Dealer/GEX structure, and execution evidence describe environment and path—not trade direction.</p></article>
      <article><h4>Volatility</h4><dl><div><dt>IV Rank</dt><dd>{value(volatility, "iv_rank")}</dd></div><div><dt>Candidate IV</dt><dd>{percent(typeof volatility.candidate_iv === "number" ? volatility.candidate_iv : null)}</dd></div><div><dt>Term Structure</dt><dd>{value(volatility, "topology")}</dd></div><div><dt>Implied Move</dt><dd>{percent(typeof volatility.implied_move_pct === "number" ? volatility.implied_move_pct : null)} · {value(volatility, "implied_move_usd")}</dd></div><div><dt>Shorter / Longer IV</dt><dd>{percent(typeof volatility.shorter_iv === "number" ? volatility.shorter_iv : null)} / {percent(typeof volatility.longer_iv === "number" ? volatility.longer_iv : null)}</dd></div><div><dt>Term availability</dt><dd>{value(volatility, "term_availability")} · {value(volatility, "exact_match_status")}</dd></div></dl><details><summary>View volatility details</summary><p>Candidate minus shorter / longer / neighbor mean: {value(volatility, "candidate_iv_minus_shorter")} / {value(volatility, "candidate_iv_minus_longer")} / {value(volatility, "candidate_iv_minus_neighbor_mean")}</p><p>Term as-of: {value(volatility, "term_as_of")} · IV Rank as-of: {value(volatility, "iv_rank_as_of")}</p></details></article>
      <article className="dealer-structure-card"><h4>Dealer / GEX Structure</h4>{dealerUnavailable ? <><p className="context-message" role="status">Data unavailable</p><dl><div><dt>Source Quality</dt><dd>{value(dealer, "source_quality")}</dd></div><div><dt>Primary Floor</dt><dd>—</dd></div><div><dt>Primary Upper Node</dt><dd>—</dd></div><div><dt>Break Risk</dt><dd>UNAVAILABLE</dd></div><div><dt>Adjacent Expiry</dt><dd>UNAVAILABLE</dd></div></dl></> : <><dl><div><dt>Anchor Expiry</dt><dd>{value(dealer, "anchor_expiry")}</dd></div><div><dt>Spot</dt><dd>{value(dealer, "spot_usd")}</dd></div><div><dt>Primary Floor</dt><dd>{value(floor, "strike_usd")} · GEX {value(floor, "net_dealer_gex_usd")}</dd></div><div><dt>Primary Upper Positive-GEX Node</dt><dd>{value(upper, "strike_usd")} · GEX {value(upper, "net_dealer_gex_usd")}</dd></div><div><dt>Immediate Below-Floor Node</dt><dd>{value(lower, "strike_usd")} · GEX {value(lower, "net_dealer_gex_usd")}</dd></div><div><dt>If Floor Holds</dt><dd>{value(dealer, "floor_hold_condition")}</dd></div><div><dt>If Floor Breaks</dt><dd>{value(dealer, "floor_break_condition")}</dd></div><div><dt>Adjacent Expiry Context</dt><dd>{value(adjacent, "state")}</dd></div><div><dt>Source Quality</dt><dd>{value(dealer, "source_quality")}</dd></div></dl><details><summary>View GEX audit</summary><p>Previous / Anchor / Next: {value(previous, "expiration")} {value(previous, "net_dealer_gex_usd")} · {value(anchor, "expiration")} {value(anchor, "net_dealer_gex_usd")} · {value(next, "expiration")} {value(next, "net_dealer_gex_usd")}</p><p>Source timestamp: {value(dealer, "source_timestamp")}</p><p>Rule versions: {Object.values(workspace.rule_versions).join(" · ")}</p><pre>{JSON.stringify(audit, null, 2)}</pre></details></>}</article>
      <ContextCard title="Execution" rows={[["Bid / Ask / Mid", `${value(execution, "bid")} / ${value(execution, "ask")} / ${value(execution, "mid")}`], ["Spread USD / %", `${value(execution, "spread_usd")} / ${percent(typeof execution.spread_pct === "number" ? execution.spread_pct : null)}`], ["Open Interest", value(execution, "open_interest")], ["Delta / Gamma", `${value(execution, "delta")} / ${value(execution, "gamma")}`], ["Theta / Vega / Charm", `${value(execution, "theta")} / ${value(execution, "vega")} / ${value(execution, "charm")}`], ["Liquidity", value(execution, "accepted_liquidity_component")]]} />
      <article className="data-age-card"><h4>Data / Provenance</h4><dl>{Object.entries(sourceTimestamps).map(([key, item]) => <div key={key}><dt>{key}</dt><dd>{display(typeof item === "string" ? item : null)}</dd></div>)}</dl><small>{workspace.specification_version} · config {workspace.config_version} · built {display(workspace.created_at)}</small></article>
    </div>
  </div>;
}

function ContextCard({ title, rows }: { title: string; rows: [string, string][] }) {
  return <article><h4>{title}</h4><dl>{rows.map(([label, item]) => <div key={label}><dt>{label}</dt><dd>{item}</dd></div>)}</dl></article>;
}
