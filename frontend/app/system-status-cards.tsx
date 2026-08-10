"use client";

import { useEffect, useState } from "react";

type SystemStatus = {
  database_status: string;
  nightwatch_status: string;
  latest_capability_refresh_at: string | null;
  quota_limit: number | null;
  quota_remaining: number | null;
  rate_limit: number | null;
  rate_limit_remaining: number | null;
  latest_request_status: number | null;
};

const unavailable: SystemStatus = {
  database_status: "unknown",
  nightwatch_status: "unknown",
  latest_capability_refresh_at: null,
  quota_limit: null,
  quota_remaining: null,
  rate_limit: null,
  rate_limit_remaining: null,
  latest_request_status: null,
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
  tone?: string;
}) {
  return (
    <article className="metric-card">
      <div className="metric-topline">
        <p>{label}</p>
        <span className={`status-dot ${tone ?? "neutral"}`} />
      </div>
      <strong>{value}</strong>
      <small>{detail}</small>
    </article>
  );
}

function formatTimestamp(value: string | null): string {
  if (!value) return "Not run";
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export function SystemStatusCards() {
  const [status, setStatus] = useState<SystemStatus>(unavailable);

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/system-status", { cache: "no-store", signal: controller.signal })
      .then((response) => response.json())
      .then((payload: SystemStatus) => setStatus(payload))
      .catch(() => setStatus({ ...unavailable, database_status: "unavailable" }));
    return () => controller.abort();
  }, []);

  const databaseConnected = status.database_status === "connected";
  const providerConnected = status.nightwatch_status === "connected";
  const quota =
    status.quota_remaining == null
      ? "—"
      : status.quota_remaining.toLocaleString();
  const quotaDetail =
    status.quota_limit == null
      ? "No persisted quota observation"
      : `of ${status.quota_limit.toLocaleString()} · rate ${status.rate_limit_remaining ?? "—"}/${status.rate_limit ?? "—"}`;

  return (
    <>
      <MetricCard
        label="System / Data"
        value={databaseConnected ? "Database ready" : "Database offline"}
        detail={`Provider ${providerConnected ? "connected" : status.nightwatch_status}`}
        tone={databaseConnected ? "green" : "amber"}
      />
      <MetricCard
        label="Latest metadata"
        value={formatTimestamp(status.latest_capability_refresh_at)}
        detail={
          status.latest_request_status == null
            ? "No persisted request"
            : `Latest request HTTP ${status.latest_request_status}`
        }
        tone={providerConnected ? "green" : undefined}
      />
      <MetricCard
        label="API quota"
        value={quota}
        detail={quotaDetail}
        tone={status.quota_remaining == null ? "amber" : "green"}
      />
    </>
  );
}
