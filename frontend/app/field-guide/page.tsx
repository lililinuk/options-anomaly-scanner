import { fieldGlossary } from "../fieldGlossary.zh-TW";
import { Sidebar } from "../navigation";

const caveats = [
  "Product Candidate 是 ticker／產品；Anomaly 才是精確 contract 或 expiry。",
  "FIRST_KNOWLEDGE_BASELINE 以 candidate_first_knowledge_at 截止且不可變；REFRESH 永遠分開保存。",
  "SAME-DAY／OI-CONFIRMED／MULTI-OBSERVATION 是證據時間層，不是排名。",
  "missing 不等於 zero；UNRESOLVED 不等於 Neutral。",
  "大額 Call 不自動代表看多；大額 Put 不自動代表看空。",
  "+ΔOI 不等於 bought-to-open；GEX 正負不等於市場方向。",
  "Expiry anomaly 不需要 contract；不可捏造 right、strike、IV、Delta、bid 或 ask。",
  "Evidence Breadth、舊 GEX labels、composite readiness 與非核心 Greeks 均標示 legacy/inactive。",
  "本頁與 Candidate Dashboard 都不是投資建議。",
];

export default function FieldGuide() {
  return <div className="app-shell"><Sidebar active="/field-guide" /><main>
    <header className="topbar guide-header"><div><p className="breadcrumb">Research / vNext 欄位說明</p><h1>Candidate-first 欄位說明與解讀指南</h1><p className="lede">Product Candidate、Anomaly、B1–B5、時間身分與可用性狀態的繁體中文單一來源。</p></div></header>
    <section className="caveat-card"><span className="eyebrow">必讀限制</span><ul>{caveats.map((item) => <li key={item}>{item}</li>)}</ul></section>
    <section className="glossary-grid">{Object.entries(fieldGlossary).map(([key, item]) => <article className={`glossary-card glossary-${item.狀態.toLowerCase()}`} id={key} key={key}><div className="glossary-topline"><span className="field-code">{item.englishField}</span><span className="glossary-status">{item.狀態}</span></div><h2>{item.中文名稱}</h2><dl><div><dt>定義</dt><dd>{item.定義}</dd></div><div><dt>計算方式</dt><dd>{item.計算方式}</dd></div><div><dt>如何解讀</dt><dd>{item.如何解讀}</dd></div><div><dt>注意事項</dt><dd>{item.注意事項}</dd></div><div><dt>更新頻率／資料時點</dt><dd>{item.更新頻率}</dd></div></dl></article>)}</section>
    <footer><p>Nightwatch vNext · Candidate-first research only</p><p>Fixed market display: America/New_York · UTC detail</p></footer>
  </main></div>;
}
