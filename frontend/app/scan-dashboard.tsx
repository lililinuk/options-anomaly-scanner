"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

type Scan = {
  status: string;
  consumed_quota_units: number;
  network_attempts: number;
  archive_status?: string | null;
  archive_completed_at?: string | null;
};

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

type Payload = {
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

const empty: Payload = { scan: null };

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

  const load = useCallback(async () => {
    const response = await fetch("/api/mag7-scan", { cache: "no-store" });
    const payload = (await response.json()) as Payload;
    setData(payload);
    setMinPremium((current) => current ?? payload.radar_filters?.min_premium_usd ?? null);
    setMinOiDiff((current) => current ?? payload.radar_filters?.min_abs_oi_diff ?? null);
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

  return (
    <>
      <section className="scan-strip" aria-label="Latest scan status">
        <div><span>Specification</span><strong>{data.specification_version ?? "signal_spec_v1.3_phase2a"}</strong></div>
        <div><span>Scan status</span><strong>{data.scan?.status ?? "NOT_RUN"}</strong></div>
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
          <tbody>{events.length ? events.map((row) => <tr key={`${row.ticker}-${row.contract_symbol}-${row.vendor_observation_date}`}><td>{row.ticker}</td><td><details><summary>{row.contract_symbol}</summary><div className="event-detail">Prev / current OI: {display(row.previous_oi)} / {display(row.current_oi)}<br />Premium / trade: {money(row.premium_per_trade)} · Volume / trade: {display(row.volume_per_trade)}<br />Avg / bid / ask / fill: {display(row.avg_price_usd)} / {display(row.last_bid_usd)} / {display(row.last_ask_usd)} / {display(row.last_fill_usd)}<br />Vendor rank: {display(row.vendor_rank)} · Structure: {display(row.contract_structure_score)} · Persistent: {display(row.contract_persistent_score)}<br />Flags: {row.risk_flags.length ? row.risk_flags.join(", ") : "—"}</div></details></td><td>{row.expiration ? `${row.expiration} / ${display(row.dte)}` : "UNJOINED"}</td><td>{display(row.right)}</td><td>{display(row.strike)}</td><td>{money(row.premium_usd)}</td><td>{display(row.oi_diff)}</td><td>{percent(row.oi_change)}</td><td>{display(row.volume)}</td><td>{display(row.trades)}</td><td>{display(row.vendor_observation_date)}</td><td><span className="context-badge">{row.archive_match_status === "EXACT" ? row.archive_completeness : "UNJOINED"}</span>{row.radar_scope === "LONG_DTE_RADAR_WATCH" && <span className="context-badge">LONG_DTE_RADAR_WATCH</span>}</td></tr>) : <tr><td colSpan={12}><div className="empty-state"><h3>No qualifying Radar Material Events</h3><p>Absence from this vendor-ranked subset is missing evidence, not negative evidence.</p></div></td></tr>}</tbody>
        </table></div>
      </section>

      <section className="panel results-panel" aria-labelledby="persistent-title">
        <div className="panel-header"><div><span className="eyebrow">Route 2 · Multi-session OI</span><h2 id="persistent-title">Persistent Positioning</h2></div><small>Build and decline are descriptive; neither implies investor direction</small></div>
        <div className="table-wrap"><table><thead><tr><th>Ticker</th><th>Contract</th><th>Expiry / DTE</th><th>Right / Strike</th><th>3 / 5 / 10 session ΔOI</th><th>OI Growth</th><th>State</th><th>Score</th><th>Winning window</th><th>History</th></tr></thead>
          <tbody>{(data.persistent_positioning ?? []).length ? data.persistent_positioning?.map((row) => <tr key={row.contract_symbol}><td>{row.ticker}</td><td>{row.contract_symbol}</td><td>{row.expiration} / {row.dte}</td><td>{row.right} / {display(row.strike)}</td><td>{display(row.oi_change_3)} / {display(row.oi_change_5)} / {display(row.oi_change_10)}</td><td>{percent(row.oi_growth)}</td><td>{display(row.persistent_state)}</td><td>{display(row.persistent_score)}</td><td>{display(row.winning_window)}</td><td>{row.history_confidence === "INSUFFICIENT" ? `Persistent history: ${row.history_observation_count ?? 0} / ${row.history_required} minimum observations` : `${row.history_confidence} · ${row.history_observation_count ?? 0} sessions`}</td></tr>) : <tr><td colSpan={10}>Persistent history is still collecting; missing history is not zero.</td></tr>}</tbody>
        </table></div>
      </section>

      <section className="panel results-panel" aria-labelledby="activity-title">
        <div className="panel-header"><div><span className="eyebrow">Route 3 · Expiry concentration</span><h2 id="activity-title">Unusual Expiry Activity</h2></div><small>Accepted v1.2 Same-Day logic retained</small></div>
        <div className="table-wrap"><table><thead><tr><th>Ticker</th><th>Expiry / DTE</th><th>Activity Score</th><th>Volume Share</th><th>VS Points</th><th>Neighbor Ratio</th><th>Neighbor Points</th><th>Score Basis</th><th>Context</th><th>0DTE baseline</th></tr></thead>
          <tbody>{(data.unusual_expiry_activity ?? []).length ? data.unusual_expiry_activity?.map((row) => <tr key={`${row.ticker}-${row.expiry}`}><td>{row.ticker}</td><td>{row.expiry} / {row.dte}</td><td>{display(row.same_day_activity_score)}</td><td>{percent(row.volume_share)}</td><td>{display(row.volume_share_points)}</td><td>{display(row.neighbor_ratio)}</td><td>{display(row.neighbor_points)}</td><td>{display(row.score_basis)}</td><td>{row.standard_monthly_inferred ? <span className="context-badge" title="Calendar inferred; score weight 0">Monthly OPEX · INFERRED</span> : "—"}</td><td>{row.baseline_status ? `${row.baseline_status} · ${row.baseline_observation_count ?? 0}` : "—"}</td></tr>) : <tr><td colSpan={10}>No current expiry route candidate. Unavailable values remain unknown, not zero.</td></tr>}</tbody>
        </table></div>
      </section>

      <section className="panel results-panel" aria-labelledby="deep-title">
        <div className="panel-header"><div><span className="eyebrow">Research workspace</span><h2 id="deep-title">Deep Dive / Research Candidates</h2></div><small>No universal conviction score</small></div>
        <div className="table-wrap"><table><thead><tr><th>Ticker</th><th>Contract / Expiry</th><th>Trigger Sources</th><th>Radar Premium / ΔOI</th><th>Persistent</th><th>Expiry Activity</th><th>Structure</th><th>Archive</th><th>Flags</th></tr></thead>
          <tbody>{(data.research_candidates ?? []).length ? data.research_candidates?.map((row) => <tr key={`${row.ticker}-${row.contract_or_expiry}`}><td>{row.ticker}</td><td>{row.contract_or_expiry}</td><td>{row.trigger_sources.map((source) => <span className="route-badge" key={source}>{source}</span>)}</td><td>{money(row.radar_premium_usd)} / {display(row.radar_oi_diff)}</td><td>{display(row.persistent_score)}</td><td>{display(row.expiry_activity_score)}</td><td>{display(row.structure_score)}</td><td>{display(row.archive_completeness)}</td><td>{row.risk_flags.length ? row.risk_flags.join(", ") : "—"}</td></tr>) : <tr><td colSpan={9}>No route-qualified research candidate is available yet.</td></tr>}</tbody>
        </table></div>
      </section>
    </>
  );
}
