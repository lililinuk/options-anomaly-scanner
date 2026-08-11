import Link from "next/link";

const items = [
  { href: "/", label: "Overview", glyph: "O" },
  { href: "/field-guide", label: "欄位說明", glyph: "欄" },
];

export function Sidebar({ active }: { active: "/" | "/field-guide" }) {
  return (
    <aside className="sidebar">
      <Link className="wordmark" href="/">
        <span className="mark" aria-hidden="true"><span /><span /><span /></span>
        <span><span className="product-name">Options Anomaly</span><span className="product-subtitle">Scanner</span></span>
      </Link>
      <nav aria-label="Primary navigation">
        <p className="nav-heading">Research workspace</p>
        <ul>{items.map((item) => (
          <li key={item.href}>
            <Link className={active === item.href ? "active" : ""} href={item.href} aria-current={active === item.href ? "page" : undefined}>
              <span className="nav-glyph" aria-hidden="true">{item.glyph}</span>{item.label}
            </Link>
          </li>
        ))}</ul>
      </nav>
      <div className="sidebar-note"><span className="eyebrow">Phase 2A</span><p>Positioning research</p><small>No buy/sell or Tradeability inference.</small></div>
    </aside>
  );
}
