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
type Payload = { scan: Scan | null; results: Result[] };

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
  return display(value);
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
        <div className="panel-header"><div><span className="eyebrow">Dual discovery</span><h2>Phase 2A v1.1 Results</h2></div><small>Activity and OI structure · not a trade recommendation</small></div>
        <div className="table-wrap results-table"><table><thead><tr>{visibleAnalyticalColumns.map((key) => <th key={key} title={fieldGlossary[key].定義}>{fieldGlossary[key].englishField}</th>)}</tr></thead>
          <tbody>{data.results.length ? data.results.map((row) => <tr key={String(row.ticker)}>{visibleAnalyticalColumns.map((key) => <td key={key}>{displayField(key, row[key])}</td>)}</tr>) : <tr><td colSpan={visibleAnalyticalColumns.length}><div className="empty-state"><div className="radar" aria-hidden="true"><span /></div><h3>No Phase 2A scan yet</h3><p>Run the manual MAG7 scan to persist evidence-backed positioning results.</p></div></td></tr>}</tbody>
        </table></div>
      </section>
    </>
  );
}
