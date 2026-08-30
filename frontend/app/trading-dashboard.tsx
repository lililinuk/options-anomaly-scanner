"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import styles from "./trading-dashboard.module.css";
import {
  familyLabels,
  familyOrder,
  featuredAnomalies,
  filterActiveAnomalies,
  formatGexMillions,
  formatIv,
  formatMoney,
  formatNumber,
  freshness,
  record,
} from "./trading-dashboard-semantics";
import type {
  AnomalyFamily,
  Freshness,
  JsonRecord,
  TradingAnomaly,
  TradingCandidate,
  TradingDashboardPayload,
} from "./trading-dashboard-types";
import { timestampText } from "./time-display";

const empty: TradingDashboardPayload = {
  generated_at: "",
  market_timezone: "America/New_York",
  candidate_population: {
    state: "UNAVAILABLE",
    freshness: "UNAVAILABLE",
    freshness_reason: "NOT_LOADED",
    market_date: null,
    scan_run_id: null,
    started_at: null,
    completed_at: null,
    candidate_materialized_at: null,
    candidate_count: 0,
  },
  candidates: [],
  contracts: {
    vendor_requests_on_read: 0,
    frozen_first_knowledge_mutated: false,
    automatic_context_capture: false,
  },
};

function StateBadge({ value }: { value: unknown }) {
  const state = freshness(value);
  const tone =
    state === "CURRENT"
      ? styles.current
      : state === "STALE"
        ? styles.stale
        : styles.unavailable;
  return <span className={`${styles.stateBadge} ${tone}`}>{state}</span>;
}

function text(value: unknown): string {
  return typeof value === "string" && value ? value : "UNAVAILABLE";
}

function familyCount(candidate: TradingCandidate, family: AnomalyFamily): number {
  return candidate.active_family_counts[family] ?? 0;
}

export function TradingDashboard() {
  const [data, setData] = useState<TradingDashboardPayload>(empty);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [families, setFamilies] = useState<Set<AnomalyFamily>>(new Set(familyOrder));
  const [featuredOnly, setFeaturedOnly] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch("/api/trading-dashboard", { cache: "no-store" });
      const payload = (await response.json()) as TradingDashboardPayload;
      if (!response.ok) throw new Error(payload.detail ?? "Trading context is unavailable.");
      setData(payload);
      setSelectedId((current) =>
        payload.candidates.some((candidate) => candidate.id === current)
          ? current
          : payload.candidates[0]?.id ?? null,
      );
      setMessage(null);
    } catch (error) {
      setData(empty);
      setMessage(error instanceof Error ? error.message : "Trading context is unavailable.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const request = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(request);
  }, [load]);

  const selected = useMemo(
    () => data.candidates.find((candidate) => candidate.id === selectedId) ?? null,
    [data.candidates, selectedId],
  );

  function toggleFamily(family: AnomalyFamily) {
    setFamilies((current) => {
      const next = new Set(current);
      if (next.has(family)) next.delete(family);
      else next.add(family);
      return next;
    });
  }

  return (
    <div className={styles.dashboard}>
      <PopulationBar data={data} />
      {message && <p className="scan-message" role="alert">{message}</p>}
      {loading ? (
        <div className={styles.empty}>Loading the latest successful Candidate population…</div>
      ) : data.candidate_population.state === "UNAVAILABLE" ? (
        <div className={styles.empty}>
          <strong>Candidate population unavailable</strong>
          <span>No successful materialized Candidate population is being inferred from historical rows.</span>
        </div>
      ) : data.candidates.length === 0 ? (
        <div className={styles.empty}>
          <strong>No Candidates in the latest successful population</strong>
          <span>Market date {data.candidate_population.market_date ?? "UNAVAILABLE"}. This is a successful empty result, not a failed scan.</span>
        </div>
      ) : (
        <div className={styles.candidateLayout}>
          <aside className={styles.candidateRail} aria-label="Latest Candidate population">
            <div className={styles.railHeading}>
              <span className="eyebrow">Latest Candidate Population</span>
              <h2>Relevant tickers</h2>
              <p>Counts include active, unexpired anomalies only.</p>
            </div>
            {data.candidates.map((candidate) => (
              <CandidateCard
                key={candidate.id}
                candidate={candidate}
                selected={candidate.id === selectedId}
                onSelect={() => setSelectedId(candidate.id)}
              />
            ))}
          </aside>
          {selected && (
            <CandidateWorkspace
              candidate={selected}
              families={families}
              featuredOnly={featuredOnly}
              onToggleFamily={toggleFamily}
              onToggleFeatured={() => setFeaturedOnly((value) => !value)}
            />
          )}
        </div>
      )}
    </div>
  );
}

function PopulationBar({ data }: { data: TradingDashboardPayload }) {
  const population = data.candidate_population;
  return (
    <section className={styles.populationBar} aria-label="Candidate population identity">
      <div className={styles.populationLead}>
        <span>Candidate population</span>
        <strong>{population.market_date ?? "UNAVAILABLE"}</strong>
        <small>Latest successful materialized population · never inferred from the browser date</small>
      </div>
      <div className={styles.populationMetric}>
        <span>Freshness</span>
        <strong><StateBadge value={population.freshness} /></strong>
      </div>
      <div className={styles.populationMetric}>
        <span>Candidates</span>
        <strong>{population.candidate_count}</strong>
      </div>
      <div className={styles.populationMetric}>
        <span>Completed</span>
        <strong>{timestampText(population.completed_at)}</strong>
      </div>
    </section>
  );
}

function CandidateCard({
  candidate,
  selected,
  onSelect,
}: {
  candidate: TradingCandidate;
  selected: boolean;
  onSelect: () => void;
}) {
  const price = record(candidate.current_trading_context.price);
  return (
    <button
      type="button"
      className={`${styles.candidateCard} ${selected ? styles.candidateCardSelected : ""}`}
      onClick={onSelect}
      aria-pressed={selected}
    >
      <div className={styles.candidateTop}>
        <div><span className="entity-label">Candidate</span><h3>{candidate.ticker}</h3></div>
        <span className={styles.candidateCount}><strong>{candidate.active_anomaly_count}</strong> active</span>
      </div>
      <div className={styles.familySummary}>
        {familyOrder.map((family) => (
          <div className={styles.familyRow} key={family}>
            <span>{familyLabels[family]}</span><strong>{familyCount(candidate, family)}</strong>
          </div>
        ))}
      </div>
      <div className={styles.cardFreshness}>
        <small>{text(price.label)}</small><StateBadge value={price.freshness} />
      </div>
    </button>
  );
}

function CandidateWorkspace({
  candidate,
  families,
  featuredOnly,
  onToggleFamily,
  onToggleFeatured,
}: {
  candidate: TradingCandidate;
  families: Set<AnomalyFamily>;
  featuredOnly: boolean;
  onToggleFamily: (family: AnomalyFamily) => void;
  onToggleFeatured: () => void;
}) {
  const contextIdentity = record(candidate.current_trading_context.identity);
  const featured = featuredAnomalies(candidate);
  const visible = filterActiveAnomalies(candidate, families, featuredOnly);
  return (
    <article className={styles.workspace}>
      <header className={styles.workspaceHeader}>
        <div>
          <span className="eyebrow">Current Trading Context</span>
          <h2>{candidate.ticker}</h2>
          <p>Current decision support is rendered separately from immutable first-knowledge research evidence. Highlighting means priority to inspect—not direction or a trade recommendation.</p>
        </div>
        <div className={styles.workspaceIdentity}>
          <StateBadge value={currentContextFreshness(candidate)} />
          <small>Context {timestampText(typeof contextIdentity.evaluated_at === "string" ? contextIdentity.evaluated_at : null)}</small>
          <small>Refresh origin: not persisted</small>
        </div>
      </header>

      <section className={styles.section} aria-labelledby="why-found-title">
        <div className={styles.sectionHeading}>
          <div><span className="eyebrow">Why Found</span><h3 id="why-found-title">Active evidence, compactly</h3></div>
          <p>One Featured anomaly per accepted family, maximum three total. Contract Persistence is omitted from Featured because no accepted native ranking exists.</p>
        </div>
        <div className={styles.whyGrid}>
          <div className={styles.countPanel}>
            <div className={styles.activeTotal}><strong>{candidate.active_anomaly_count}</strong><span>Active anomalies</span></div>
            <div className={styles.familySummary}>
              {familyOrder.map((family) => (
                <div className={styles.familyRow} key={family}><span>{familyLabels[family]}</span><strong>{familyCount(candidate, family)}</strong></div>
              ))}
            </div>
          </div>
          <div className={styles.featuredGrid}>
            {featured.length ? featured.map((anomaly) => <FeaturedCard key={anomaly.id} anomaly={anomaly} />) : (
              <div className={styles.empty}>No Featured active evidence is available.</div>
            )}
            <p className={styles.featuredLegend}>Highlight = priority to inspect · not bullish, bearish, BUY, SELL, or cross-family strength.</p>
          </div>
        </div>
      </section>

      <section className={styles.section} aria-labelledby="current-context-title">
        <div className={styles.sectionHeading}>
          <div><span className="eyebrow">B1 / B2 / B3</span><h3 id="current-context-title">Current context blocks</h3></div>
          <p>Each source discloses its own as-of and freshness. AVAILABLE is never treated as CURRENT.</p>
        </div>
        <div className={styles.contextGrid}>
          <PriceBlock context={candidate.current_trading_context.price} />
          <VolatilityBlock context={candidate.current_trading_context.volatility} />
          <GexBlock context={candidate.current_trading_context.dealer_gex} />
        </div>
      </section>

      <section className={styles.section} aria-labelledby="active-details-title">
        <div className={styles.sectionHeading}>
          <div><span className="eyebrow">B4</span><h3 id="active-details-title">Active anomaly details</h3></div>
          <p>Current DTE is presentation-only. Immutable Detection DTE and bucket remain distinct and unchanged.</p>
        </div>
        <div className={styles.filterBar} aria-label="Active anomaly family filters">
          {familyOrder.map((family) => (
            <label className={styles.filterControl} key={family}>
              <input type="checkbox" checked={families.has(family)} onChange={() => onToggleFamily(family)} />
              <span>{familyLabels[family]}</span>
            </label>
          ))}
          <label className={styles.filterControl}>
            <input type="checkbox" checked={featuredOnly} onChange={onToggleFeatured} />
            <span>Featured only</span>
          </label>
        </div>
        <div className={styles.anomalyList}>
          {visible.length ? visible.map((anomaly) => <AnomalyCard key={anomaly.id} anomaly={anomaly} />) : (
            <div className={styles.empty}>No active anomalies match the selected families.</div>
          )}
        </div>
      </section>

      <section className={styles.section} aria-label="Frozen first-knowledge boundary">
        <div className={styles.boundaryNote}>
          <span className={styles.boundaryMark}>F</span>
          <div><strong>Frozen First-Knowledge is preserved outside Trading View</strong><p>The immutable no-lookahead baseline, expired triggers, historical contexts, and full provenance remain research/audit evidence. This page neither refreshes nor overwrites them.</p></div>
        </div>
      </section>
    </article>
  );
}

function currentContextFreshness(candidate: TradingCandidate): Freshness {
  const blocks = [
    freshness(candidate.current_trading_context.price.freshness),
    freshness(candidate.current_trading_context.volatility.freshness),
    freshness(candidate.current_trading_context.dealer_gex.freshness),
  ];
  if (blocks.includes("STALE")) return "STALE";
  if (blocks.every((value) => value === "CURRENT")) return "CURRENT";
  if (blocks.includes("CURRENT")) return "STALE";
  return "UNAVAILABLE";
}

function FeaturedCard({ anomaly }: { anomaly: TradingAnomaly }) {
  const basis = anomaly.family === "RADAR_EVENT"
    ? `${formatMoney(anomaly.premium_usd, 0)} premium · ΔOI ${formatNumber(anomaly.delta_oi)}`
    : `Same-Day Activity Score ${formatNumber(anomaly.same_day_activity_score)}`;
  return (
    <article className={styles.featuredCard}>
      <span className={styles.featuredEyebrow}>{anomaly.family_label} · priority to inspect</span>
      <h4>{anomaly.identity}</h4>
      <p>{basis} · expires {anomaly.expiration}</p>
    </article>
  );
}

function PriceBlock({ context }: { context: JsonRecord }) {
  return (
    <article className={styles.contextBlock}>
      <div className={styles.blockHeading}><span className={styles.blockNumber}>B1</span><h4>Price</h4><StateBadge value={context.freshness} /></div>
      <div className={styles.heroValue}>{formatMoney(context.value_usd)}</div>
      <div className={styles.heroLabel}>{text(context.label)}</div>
      <div className={styles.blockMeta}>
        <span>Source</span><strong>{text(context.source)}</strong>
        <span>As of</span><strong>{timestampText(typeof context.as_of === "string" ? context.as_of : null)}</strong>
        <span>Session</span><strong>{text(context.session)}</strong>
      </div>
    </article>
  );
}

function VolatilityBlock({ context }: { context: JsonRecord }) {
  const ivRank = record(context.iv_rank);
  const terms = record(context.active_expiry_terms);
  return (
    <article className={styles.contextBlock}>
      <div className={styles.blockHeading}><span className={styles.blockNumber}>B2</span><h4>Volatility</h4><StateBadge value={context.freshness} /></div>
      <div className={styles.heroValue}>{typeof ivRank.value === "number" ? formatNumber(ivRank.value) : "UNAVAILABLE"}</div>
      <div className={styles.heroLabel}>Raw IV Rank <StateBadge value={ivRank.freshness} /></div>
      <div className={styles.termList}>
        {Object.entries(terms).slice(0, 3).map(([expiry, raw]) => {
          const item = record(raw);
          return <div className={styles.termRow} key={expiry}><strong>{expiry}</strong><span>Active-expiry IV {formatIv(item.candidate_term_iv)} · {text(item.topology)}</span></div>;
        })}
      </div>
      <div className={styles.provenanceWarning}>IV Rank vendor semantics remain unverified. No LOW/MID/HIGH classification and no Candidate scoring use.</div>
    </article>
  );
}

function GexBlock({ context }: { context: JsonRecord }) {
  const expiries = record(context.active_expiry_contexts);
  return (
    <article className={styles.contextBlock}>
      <div className={styles.blockHeading}><span className={styles.blockNumber}>B3</span><h4>Dealer / GEX</h4><StateBadge value={context.freshness} /></div>
      <div className={styles.heroValue}>{Object.keys(expiries).length}</div>
      <div className={styles.heroLabel}>active expiries · archive-only</div>
      <div className={styles.gexList}>
        {Object.entries(expiries).slice(0, 3).map(([expiry, raw]) => <GexExpiry key={expiry} expiry={expiry} value={record(raw)} />)}
      </div>
      <div className={styles.blockMeta}>
        <span>As of</span><strong>{timestampText(typeof context.as_of === "string" ? context.as_of : null)}</strong>
        <span>Relative to</span><strong>{text(context.relative_price_context_label)}</strong>
      </div>
      <p className={styles.gexDisclosure}>{text(context.sign_disclosure)}</p>
    </article>
  );
}

function GexExpiry({ expiry, value }: { expiry: string; value: JsonRecord }) {
  const nodes = [
    ["Floor", record(value.primary_floor)],
    ["Upper", record(value.primary_upper_positive_gex_node)],
    ["Below floor", record(value.immediate_below_floor_node)],
  ] as const;
  return (
    <div className={styles.gexRow}>
      <strong>{expiry}</strong>
      {nodes.map(([label, node]) => {
        const net = node.net_dealer_gex_usd;
        const tone = typeof net === "number" && net < 0 ? styles.gexNegative : styles.gexPositive;
        return <span key={label}>{label} {formatNumber(node.strike_usd)} · <b className={tone}>Net GEX {formatGexMillions(net)}</b></span>;
      })}
    </div>
  );
}

function AnomalyCard({ anomaly }: { anomaly: TradingAnomaly }) {
  const quote = record(anomaly.quote);
  return (
    <article className={`${styles.anomalyCard} ${anomaly.featured ? styles.anomalyCardFeatured : ""}`}>
      <div className={styles.anomalyTitle}>
        <span className={styles.familyPill}>{anomaly.family_label}</span>
        <h4>{anomaly.identity}</h4>
        {anomaly.featured && <span className={`${styles.stateBadge} ${styles.current}`}>INSPECT</span>}
      </div>
      <div className={styles.anomalyFields}>
        <div><span>Expiry / Current DTE</span><strong>{anomaly.expiration} / {anomaly.current_dte}</strong></div>
        <div><span>Detection DTE / bucket</span><strong>{anomaly.detection_dte ?? "—"} / {anomaly.detection_bucket ?? "—"}</strong></div>
        <div><span>Right / strike</span><strong>{anomaly.right ?? "—"} / {formatNumber(anomaly.strike)}</strong></div>
        <div><span>ΔOI / premium</span><strong>{formatNumber(anomaly.delta_oi)} / {formatMoney(anomaly.premium_usd, 0)}</strong></div>
        <div><span>IV / delta</span><strong>{formatIv(quote.iv)} / {formatNumber(quote.delta)}</strong></div>
        <div><span>Bid / ask</span><strong>{formatMoney(quote.bid_usd)} / {formatMoney(quote.ask_usd)}</strong></div>
        <div><span>Spread</span><strong>{formatIv(quote.spread_pct)}</strong></div>
        <div><span>Quote as-of</span><strong>{timestampText(typeof quote.as_of === "string" ? quote.as_of : null)}</strong></div>
        <div><span>Price context</span><strong>{text(record(anomaly.price_relationship).price_context_label)} · {freshness(record(anomaly.price_relationship).price_context_freshness)}</strong></div>
      </div>
    </article>
  );
}
