"use client";

import { useEffect, useState } from "react";

import type { SystemStatus } from "./dashboard-types";
import { timestampText } from "./time-display";

const unavailable: SystemStatus = {
  scanner_status: "unknown",
  latest_scan_at: null,
  latest_scan_status: null,
  latest_scan_started_at: null,
  latest_scan_completed_at: null,
  latest_scan_consumed_quota_units: null,
  nightwatch_status: "unknown",
  latest_capability_refresh_at: null,
  quota_limit: null,
  quota_remaining: null,
  rate_limit: null,
  rate_limit_remaining: null,
  latest_request_status: null,
  database_status: "unknown",
  scheduling_enabled: false,
  daily_collection_last_success_at: null,
  daily_collection_market_date: null,
  dealer_archive_last_vendor_observed_at: null,
  dealer_archive_last_captured_at: null,
};

function MetricCard({
  label,
  value,
  detail,
  tone,
}: {
  label: string;
  value: string;
  detail: string;
  tone?: "green" | "amber" | "neutral";
}) {
  return (
    <article className="metric-card">
      <div className="metric-topline">
        <p>{label}</p>
        <span className={`status-dot ${tone ?? "neutral"}`} aria-hidden="true" />
      </div>
      <strong>{value}</strong>
      <small>{detail}</small>
    </article>
  );
}

export function SystemStatusCards() {
  const [status, setStatus] = useState<SystemStatus>(unavailable);

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/system-status", { cache: "no-store", signal: controller.signal })
      .then(async (response) => {
        const payload = (await response.json()) as Partial<SystemStatus>;
        if (!response.ok) throw new Error("System health is unavailable");
        setStatus({ ...unavailable, ...payload });
      })
      .catch(() =>
        setStatus({ ...unavailable, database_status: "unavailable" }),
      );
    return () => controller.abort();
  }, []);

  const databaseConnected = status.database_status === "connected";
  const quota =
    status.quota_remaining == null
      ? "—"
      : status.quota_remaining.toLocaleString("en-US");

  return (
    <>
      <MetricCard
        label="Database"
        value={databaseConnected ? "Ready" : "Offline / unavailable"}
        detail={`Persisted provider state: ${status.nightwatch_status}`}
        tone={databaseConnected ? "green" : "amber"}
      />
      <MetricCard
        label="Last MAG7 scan"
        value={status.latest_scan_status ?? "NOT_RUN"}
        detail={`${timestampText(status.latest_scan_completed_at ?? status.latest_scan_started_at)} · ${status.latest_scan_consumed_quota_units ?? "—"} consumed units`}
        tone={status.latest_scan_status === "COMPLETE" ? "green" : "amber"}
      />
      <MetricCard
        label="Phase 2A daily collection"
        value={status.daily_collection_market_date ?? "No successful run"}
        detail={`Last success: ${timestampText(status.daily_collection_last_success_at)}`}
        tone={status.daily_collection_last_success_at ? "green" : "amber"}
      />
      <MetricCard
        label="Dealer / GEX archive"
        value={timestampText(status.dealer_archive_last_vendor_observed_at)}
        detail={`Vendor observed · local captured ${timestampText(status.dealer_archive_last_captured_at)}`}
        tone={status.dealer_archive_last_vendor_observed_at ? "green" : "amber"}
      />
      <MetricCard
        label="API quota"
        value={quota}
        detail={
          status.quota_limit == null
            ? "No persisted quota observation"
            : `of ${status.quota_limit.toLocaleString("en-US")} · rate ${status.rate_limit_remaining ?? "—"}/${status.rate_limit ?? "—"} · HTTP ${status.latest_request_status ?? "—"}`
        }
        tone={status.quota_remaining == null ? "amber" : "green"}
      />
    </>
  );
}
