import { ScanDashboard } from "./scan-dashboard";
import { Sidebar } from "./navigation";
import { SystemStatusCards } from "./system-status-cards";

export default function Home() {
  return (
    <div className="app-shell"><Sidebar active="/" /><main>
      <header className="topbar"><div><p className="breadcrumb">Research / Candidate-first dashboard</p><h1>Today&apos;s product candidates, with the evidence clock intact.</h1><p className="lede">A non-directional research view of persisted ticker candidates, their qualifying anomalies, frozen first-knowledge context, and later refreshes.</p></div><div className="market-pill"><span className="status-dot amber" />Manual scan and explicit context refresh</div></header>
      <section aria-labelledby="system-health-title">
        <div className="section-heading"><span className="eyebrow">System / Data Health</span><h2 id="system-health-title">Know the data state before reading the candidates.</h2></div>
        <div className="metrics"><SystemStatusCards /></div>
      </section>
      <ScanDashboard />
      <footer><p>Research system · Not investment advice</p><p>Canonical time: UTC <span>·</span> Market time: America/New_York</p></footer>
    </main></div>
  );
}
