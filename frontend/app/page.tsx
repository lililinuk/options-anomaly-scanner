import { ScanDashboard } from "./scan-dashboard";
import { Sidebar } from "./navigation";
import { SystemStatusCards } from "./system-status-cards";

export default function Home() {
  return (
    <div className="app-shell"><Sidebar active="/" /><main>
      <header className="topbar"><div><p className="breadcrumb">Research / MAG7 positioning</p><h1>Unusual positioning, with evidence attached.</h1><p className="lede">A budget-bounded same-day view of unusual expiries, contracts, and coherent Call/Put strike clusters. Structure is not direction.</p></div><div className="market-pill"><span className="status-dot amber" />Manual scans only</div></header>
      <section className="metrics" aria-label="System status"><SystemStatusCards /></section>
      <ScanDashboard />
      <footer><p>Research system · Not investment advice</p><p>Canonical time: UTC <span>·</span> Market time: America/New_York</p></footer>
    </main></div>
  );
}
