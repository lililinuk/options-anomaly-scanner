import { fieldGlossary } from "../fieldGlossary.zh-TW";
import { Sidebar } from "../navigation";

const caveats = [
  "高 Volume/OI 不證明是新開倉；低 OI 也不會自動使異動無效。",
  "大額 Call 不自動代表看多；大額 Put 不自動代表看空。",
  "Estimated Premium 可能不等於實際成交權利金。",
  "Premium-weighted strike 是部位集中中心，不是價格目標。",
  "OI 有結算延遲，Day-0 OI confirmation 可能維持 PENDING。",
  "Phase 2A Positioning Candidate 不是交易建議。",
];

export default function FieldGuide() {
  return <div className="app-shell"><Sidebar active="/field-guide" /><main>
    <header className="topbar guide-header"><div><p className="breadcrumb">Research / 欄位說明</p><h1>Scanner 欄位說明與解讀指南</h1><p className="lede">Phase 2A 分析欄位的繁體中文單一來源。所有標籤描述活動結構，不推論買賣方向。</p></div></header>
    <section className="caveat-card"><span className="eyebrow">必讀限制</span><ul>{caveats.map((item) => <li key={item}>{item}</li>)}</ul></section>
    <section className="glossary-grid">{Object.entries(fieldGlossary).map(([key, item]) => <article className="glossary-card" id={key} key={key}><span className="field-code">{item.englishField}</span><h2>{item.中文名稱}</h2><dl><div><dt>定義</dt><dd>{item.定義}</dd></div><div><dt>計算方式</dt><dd>{item.計算方式}</dd></div><div><dt>如何解讀</dt><dd>{item.如何解讀}</dd></div><div><dt>注意事項</dt><dd>{item.注意事項}</dd></div><div><dt>更新頻率／資料時點</dt><dd>{item.更新頻率}</dd></div></dl></article>)}</section>
    <footer><p>Phase 2A · Positioning research only</p><p>規格版本 signal_spec_v1.0_phase2a</p></footer>
  </main></div>;
}
