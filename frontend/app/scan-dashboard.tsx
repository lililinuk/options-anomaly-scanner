"use client";

import { useCallback, useEffect, useState } from "react";
import { fieldGlossary, visibleAnalyticalColumns } from "./fieldGlossary.zh-TW";

type Scan = {
  scan_run_id: string; status: string; started_at: string; completed_at: string | null;
  consumed_quota_units: number; network_attempts: number; cache_hits: number;
  fresh_requests: number; tickers_scanned?: number;
  archive_status?: string | null; archive_completed_at?: string | null;
};
type Result = Record<(typeof visibleAnalyticalColumns)[number], string | number | null>;
type Distribution = Record<string, number>;
type ExpiryDiscovery = {
  ticker: string; expiry: string; dte: number; bucket: string;
  same_day_activity_score: number | null; persistent_positioning_score: number | null;
  discovery_score: number | null; discovery_source: string; discovery_evidence_breadth: number;
  current_volume_share: number | null; peer_count: number; peer_dtes: number[];
  peer_quality: string;
};
type ZeroDteStatus = ExpiryDiscovery & {
  current_expiry_volume: number; raw_neighbor_ratio_descriptive_only: number | null;
  baseline_status: string; baseline_observation_count: number; baseline_required: number;
  baseline_mean: number | null; baseline_median: number | null; baseline_mad: number | null;
  historical_percentile: number | null; robust_deviation: number | null; baseline_method: string;
};
type Payload = {
  scan: Scan | null; results: Result[]; distribution?: Distribution;
  top_expiries?: ExpiryDiscovery[]; zero_dte_status?: ZeroDteStatus[];
};

const empty: Payload = { scan: null, results: [] };

function display(value: string | number | null): string {
  if (value == null || value === "") return "—";
  if (typeof value === "number") return value.toFixed(1);
  if (/^\d{4}-\d{2}-\d{2}T/.test(value)) return new Date(value).toLocaleString();
  return value;
}

function displayField(
  key: (typeof visibleAnalyticalColumns)[number],
  value: string | number | null,
): string {
  if (key === "oi_share" && typeof value === "number") {
    return `${(value * 100).toFixed(1)}%`;
  }
  if ((key === "dte" || key === "discovery_evidence_breadth") && typeof value === "number") {
    return String(value);
  }
  return display(value);
}

function percent(value: number | null): string {
  return value == null ? "—" : `${(value * 100).toFixed(1)}%`;
}

export function ScanDashboard() {
  const [data, setData] = useState<Payload>(empty);
  const [running, setRunning] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const load = useCallback(() => fetch("/api/mag7-scan", { cache: "no-store" }).then((response) => response.json()).then(setData), []);
  useEffect(() => { void load(); }, [load]);

  async function run() {
    setRunning(true); setMessage(null);
    try {
      const response = await fetch("/api/mag7-scan", { method: "POST" });
      if (!response.ok) throw new Error(response.status === 409 ? "已有掃描正在執行。" : "掃描未能完成。請查看後端狀態。" );
      await load();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "掃描未能完成。");
    } finally { setRunning(false); }
  }

  return (
    <>
      <section className="scan-strip" aria-label="Latest scan status">
        <div><span>Scan status</span><strong>{data.scan?.status ?? "NOT_RUN"}</strong></div>
        <div><span>API consumed</span><strong>{data.scan?.consumed_quota_units ?? 0} / 75</strong></div>
        <div><span>Network attempts</span><strong>{data.scan?.network_attempts ?? 0} / 100</strong></div>
        <div><span>Archive freshness</span><strong>{data.scan?.archive_completed_at ? `${data.scan.archive_status} · ${display(data.scan.archive_completed_at)}` : "—"}</strong></div>
        <button className="run-button" type="button" onClick={run} disabled={running}>{running ? "Scanning…" : "Run MAG7 Scan"}</button>
      </section>
      {message && <p className="scan-message" role="alert">{message}</p>}
      <section className="panel results-panel">
        <div className="panel-header"><div><span className="eyebrow">Calibrated discovery</span><h2>Phase 2A v1.2 Ticker Summary</h2></div><small>Eligible expiry maxima · not the full distribution</small></div>
        <div className="table-wrap results-table"><table><thead><tr>{visibleAnalyticalColumns.map((key) => <th key={key} title={fieldGlossary[key].定義}>{fieldGlossary[key].englishField}</th>)}</tr></thead>
          <tbody>{data.results.length ? data.results.map((row) => <tr key={String(row.ticker)}>{visibleAnalyticalColumns.map((key) => <td key={key}>{displayField(key, row[key])}</td>)}</tr>) : <tr><td colSpan={visibleAnalyticalColumns.length}><div className="empty-state"><div className="radar" aria-hidden="true"><span /></div><h3>No Phase 2A scan yet</h3><p>Run the manual MAG7 scan to persist evidence-backed positioning results.</p></div></td></tr>}</tbody>
        </table></div>
      </section>
      <section className="panel results-panel" aria-label="Discovery score distribution">
        <div className="panel-header"><div><span className="eyebrow">Distribution</span><h2>Cross-MAG7 Expiry Selectivity</h2></div><small>All 0–90 DTE expiries</small></div>
        <div className="scan-strip">
          <div><span>Scored / total</span><strong>{data.distribution?.scored_expiries ?? 0} / {data.distribution?.total_expiries ?? 0}</strong></div>
          <div><span>≥90</span><strong>{data.distribution?.discovery_90_plus ?? 0}</strong></div>
          <div><span>80–89</span><strong>{data.distribution?.discovery_80_89 ?? 0}</strong></div>
          <div><span>65–79</span><strong>{data.distribution?.discovery_65_79 ?? 0}</strong></div>
          <div><span>40–64</span><strong>{data.distribution?.discovery_40_64 ?? 0}</strong></div>
          <div><span>&lt;40</span><strong>{data.distribution?.discovery_below_40 ?? 0}</strong></div>
          <div><span>Unavailable / cold</span><strong>{data.distribution?.unavailable ?? 0} / {data.distribution?.cold_start ?? 0}</strong></div>
        </div>
      </section>
      <section className="panel results-panel" aria-label="Top expiry discoveries">
        <div className="panel-header"><div><span className="eyebrow">Ranked expiries</span><h2>Top Expiry Discoveries</h2></div><small>Normal eligibility precedes ranking</small></div>
        <div className="table-wrap"><table><thead><tr><th>Ticker</th><th>Expiry</th><th>DTE</th><th>Same-Day</th><th>Persistent</th><th>Discovery</th><th>Source</th><th>Evidence Breadth</th><th>Volume Share</th><th>Peer Quality</th></tr></thead>
          <tbody>{(data.top_expiries ?? []).map((row) => <tr key={`${row.ticker}-${row.expiry}`}><td>{row.ticker}</td><td>{row.expiry}</td><td>{row.dte}</td><td>{display(row.same_day_activity_score)}</td><td>{display(row.persistent_positioning_score)}</td><td>{display(row.discovery_score)}</td><td>{row.discovery_source}</td><td>{row.discovery_evidence_breadth}</td><td>{percent(row.current_volume_share)}</td><td>{row.peer_quality} · {row.peer_count} peers</td></tr>)}</tbody>
        </table></div>
      </section>
      <section className="panel results-panel" aria-label="0DTE calibration status">
        <div className="panel-header"><div><span className="eyebrow">0DTE calibration</span><h2>Previous-20 Baseline Status</h2></div><small>Raw neighbor ratio is descriptive only</small></div>
        <div className="table-wrap"><table><thead><tr><th>Ticker</th><th>Expiry</th><th>Volume Share</th><th>Prior-20 Mean</th><th>Median</th><th>MAD</th><th>Percentile</th><th>Coverage</th><th>Same-Day</th><th>Raw Neighbor</th></tr></thead>
          <tbody>{(data.zero_dte_status ?? []).length ? (data.zero_dte_status ?? []).map((row) => <tr key={`${row.ticker}-${row.expiry}`}><td>{row.ticker}</td><td>{row.expiry}</td><td>{percent(row.current_volume_share)}</td><td>{percent(row.baseline_mean)}</td><td>{percent(row.baseline_median)}</td><td>{percent(row.baseline_mad)}</td><td>{percent(row.historical_percentile)}</td><td>{row.baseline_observation_count} / {row.baseline_required}</td><td>{display(row.same_day_activity_score)}</td><td>{display(row.raw_neighbor_ratio_descriptive_only)} · weight 0</td></tr>) : <tr><td colSpan={10}>No valid DTE-0 observation in the current vendor session.</td></tr>}</tbody>
        </table></div>
      </section>
    </>
  );
}
