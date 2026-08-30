import { Sidebar } from "./navigation";
import { TradingDashboard } from "./trading-dashboard";

export default function Home() {
  return (
    <div className="app-shell">
      <Sidebar active="/" />
      <main>
        <header className="topbar">
          <div>
            <p className="breadcrumb">Trading / Current context</p>
            <h1>What is relevant to trading now?</h1>
            <p className="lede">The latest successful Candidate population, active anomalies, and truthful current-context freshness—kept cleanly separate from frozen research evidence.</p>
          </div>
          <div className="market-pill"><span className="status-dot amber" />Read-only persisted context</div>
        </header>
        <TradingDashboard />
        <footer><p>Trading decision support · Not investment advice</p><p>Persisted time: UTC <span>·</span> Market logic: America/New_York</p></footer>
      </main>
    </div>
  );
}
