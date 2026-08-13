import { fieldGlossary } from "../fieldGlossary.zh-TW";
import { Sidebar } from "../navigation";

const caveats = [
  "Phase 2A v1.3 以 Radar、Persistent、Expiry Activity 三條獨立路由探索，不建立跨路由總分。",
  "0DTE Same-Day 必須有同 ticker 前 20 個有效 0DTE sessions；不足時顯示 unavailable。",
  "0DTE raw cross-expiry Neighbor Ratio 僅供診斷，scoring weight 為零。",
  "Discovery confirmation bonus 不可繞過 Same-Day／Persistent 原始 eligibility thresholds。",
  "大額 Call 不自動代表看多；大額 Put 不自動代表看空。",
  "OI Change Radar 是 ranked subset；未出現不是負面證據。",
  "OI Share Change 的 D 是有效 OI observation session，不是日曆日。",
  "Ticker Call/Put Volume 不可歸因到單一 expiry。",
  "Phase 2A Positioning Candidate 不是交易建議。",
];

export default function FieldGuide() {
  return <div className="app-shell"><Sidebar active="/field-guide" /><main>
    <header className="topbar guide-header"><div><p className="breadcrumb">Research / 欄位說明</p><h1>Scanner 欄位說明與解讀指南</h1><p className="lede">Phase 2A 分析欄位的繁體中文單一來源。所有標籤描述活動結構，不推論買賣方向。</p></div></header>
    <section className="caveat-card"><span className="eyebrow">必讀限制</span><ul>{caveats.map((item) => <li key={item}>{item}</li>)}</ul></section>
    <section className="glossary-grid">{Object.entries(fieldGlossary).map(([key, item]) => <article className="glossary-card" id={key} key={key}><span className="field-code">{item.englishField}</span><h2>{item.中文名稱}</h2><dl><div><dt>定義</dt><dd>{item.定義}</dd></div><div><dt>計算方式</dt><dd>{item.計算方式}</dd></div><div><dt>如何解讀</dt><dd>{item.如何解讀}</dd></div><div><dt>注意事項</dt><dd>{item.注意事項}</dd></div><div><dt>更新頻率／資料時點</dt><dd>{item.更新頻率}</dd></div></dl></article>)}</section>
    <footer><p>Phase 2A v1.3 · Positioning research only</p><p>規格版本 signal_spec_v1.3_phase2a</p></footer>
  </main></div>;
}
