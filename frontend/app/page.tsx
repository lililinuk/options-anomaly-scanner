const navigation = [
  { label: "Overview", glyph: "O", active: true },
  { label: "Candidates", glyph: "C" },
  { label: "Ticker Detail", glyph: "T" },
  { label: "Signal History", glyph: "H" },
  { label: "System / Data Status", glyph: "S" },
];

const candidateColumns = ["Ticker", "Structure", "Detected", "Lifecycle", "Tradeability"];

function Wordmark() {
  return (
    <div className="wordmark">
      <div className="mark" aria-hidden="true">
        <span />
        <span />
        <span />
      </div>
      <div>
        <p className="product-name">Options Anomaly</p>
        <p className="product-subtitle">Scanner</p>
      </div>
    </div>
  );
}

function Sidebar() {
  return (
    <aside className="sidebar">
      <Wordmark />
      <nav aria-label="Primary navigation">
        <p className="nav-heading">Research workspace</p>
        <ul>
          {navigation.map((item) => (
            <li key={item.label}>
              <a className={item.active ? "active" : ""} href="#" aria-current={item.active ? "page" : undefined}>
                <span className="nav-glyph" aria-hidden="true">{item.glyph}</span>
                {item.label}
                {!item.active && <span className="soon">Soon</span>}
              </a>
            </li>
          ))}
        </ul>
      </nav>
      <div className="sidebar-note">
        <span className="eyebrow">Phase 1</span>
        <p>Foundation mode</p>
        <small>Signal scoring is intentionally disabled.</small>
      </div>
    </aside>
  );
}

function MetricCard({ label, value, detail, tone }: { label: string; value: string; detail: string; tone?: string }) {
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

export default function Home() {
  return (
    <div className="app-shell">
      <Sidebar />
      <main>
        <header className="topbar">
          <div>
            <p className="breadcrumb">Research / Overview</p>
            <h1>Market intelligence, with evidence attached.</h1>
            <p className="lede">A traceable view of unusual options positioning across the full signal lifecycle.</p>
          </div>
          <div className="market-pill">
            <span className="status-dot amber" />
            Market session data pending
          </div>
        </header>

        <section className="metrics" aria-label="System status">
          <MetricCard label="System status" value="Ready" detail="API foundation available" tone="green" />
          <MetricCard label="Latest scan" value="Not run" detail="Scheduling disabled in Phase 1" />
          <MetricCard label="API quota" value="—" detail="No account metadata loaded" tone="amber" />
          <MetricCard label="Candidate set" value="0" detail="Signal engine not configured" />
        </section>

        <section className="workspace-grid">
          <article className="panel candidate-panel">
            <div className="panel-header">
              <div>
                <span className="eyebrow">Decision queue</span>
                <h2>Trade Candidates</h2>
              </div>
              <button type="button" disabled>Run manual scan</button>
            </div>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>{candidateColumns.map((column) => <th key={column}>{column}</th>)}</tr>
                </thead>
                <tbody>
                  <tr>
                    <td colSpan={candidateColumns.length}>
                      <div className="empty-state">
                        <div className="radar" aria-hidden="true"><span /></div>
                        <h3>No candidate analysis yet</h3>
                        <p>Future scan results will appear here only after evidence is normalized and lifecycle-aware checks are configured.</p>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </article>

          <aside className="panel readiness-panel">
            <div className="panel-header compact">
              <div>
                <span className="eyebrow">Pipeline</span>
                <h2>Data readiness</h2>
              </div>
            </div>
            <ol className="readiness-list">
              <li className="complete"><span>01</span><div><strong>Application API</strong><small>Service contract ready</small></div></li>
              <li><span>02</span><div><strong>Provider capability sync</strong><small>Awaiting authenticated discovery</small></div></li>
              <li><span>03</span><div><strong>First raw snapshot</strong><small>No vendor data requested</small></div></li>
              <li><span>04</span><div><strong>Signal configuration</strong><small>Not specified</small></div></li>
            </ol>
            <div className="integrity-note">
              <span aria-hidden="true">✓</span>
              <p><strong>Evidence-first storage</strong><br /><small>Raw inputs remain separate from normalized and derived records.</small></p>
            </div>
          </aside>
        </section>

        <footer>
          <p>Research system · Not investment advice</p>
          <p>Canonical time: UTC <span>•</span> Market time: America/New_York</p>
        </footer>
      </main>
    </div>
  );
}

