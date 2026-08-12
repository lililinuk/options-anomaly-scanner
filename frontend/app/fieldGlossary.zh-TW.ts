export type GlossaryEntry = {
  中文名稱: string;
  englishField: string;
  定義: string;
  計算方式: string;
  如何解讀: string;
  注意事項: string;
  更新頻率: string;
};

const entry = (
  中文名稱: string, englishField: string, 定義: string, 計算方式 = "由掃描器依版本化規格計算或由來源資料保留。",
  如何解讀 = "數值用來描述當日部位活動結構，必須連同資料完整度閱讀。",
  注意事項 = "Phase 2A 僅供研究，不是交易建議。", 更新頻率 = "每次手動掃描",
): GlossaryEntry => ({ 中文名稱, englishField, 定義, 計算方式, 如何解讀, 注意事項, 更新頻率 });

export const fieldGlossary = {
  same_day_activity_score: entry("同日活動分數", "Same-Day Activity Score", "今天／最新一期某 expiration 的成交活動是否異常集中。", "Expiry Volume Share（60）＋ Comparable-Expiry Volume Neighbor Ratio（40）；缺失證據不重縮放。", "只描述 expiry 層級的最新成交活動集中度。", "不包含每 expiry Call/Put Volume Skew，也不代表投資人方向。"),
  persistent_positioning_score: entry("持續部位分數", "Persistent Positioning Score", "跨多個有效 OI observation sessions 是否持續形成或下降。", "各自計算 3／5／10 個有效 observation windows，採可用視窗最高分。", "分數描述 OI positioning 的持續性。", "D 是有效 OI observation session，不是日曆日；少於三筆時 unavailable。", "每日 vendor OI observation date"),
  discovery_score: entry("探索分數", "Discovery Score", "Same-Day Activity Score 與 Persistent Positioning Score 的較高者。", "MAX(same_day_activity_score, persistent_positioning_score)。", "保留活動與歷史定位兩條獨立證據，不做平均。", "Cold-start flag 不會被偷偷混入此分數。"),
  discovery_source: entry("探索來源", "Discovery Source", "標示 qualifying evidence 來自 SAME_DAY、PERSISTENT 或 BOTH。", "依固定 eligibility threshold 判定。", "說明 expiry 為何進入 deep dive。"),
  oi_share: entry("OI 佔比", "OI Share", "某 expiry 的 OI 佔該 ticker 指定 0–180 DTE 範圍總 OI 的比例。", "expiry_total_oi / ticker_total_oi_in_scope。", "描述目前 OI surface 的集中程度。", "分母來自完整的 oi_per_expiry daily surface，不使用 ranked OI-change subset。", "每日 vendor OI observation date"),
  oi_share_change: entry("OI 佔比變化", "OI Share Change (pp)", "該 expiry 在整體 OI surface 中的重要性增加或下降多少 percentage points。", "current OI Share − historical OI Share；例如 8%→24% 為 +16pp。", "正值表示相對集中度增加。", "不是相對百分比成長；缺少指定 observation window 時 unavailable。", "3／5／10 個有效 OI observation sessions"),
  history_coverage: entry("歷史覆蓋", "History Coverage", "有效 OI observation 數量所對應的信心級別。", "<3 INSUFFICIENT；3–4 LOW；5–9 MEDIUM；10+ FULL。"),
  contract_structure_score: entry("合約部位結構分數", "Contract Positioning Structure Score", "衡量某張 option 在目前 expiry OI strike structure 中有多突出；不是當天成交異常分數。", "同側 expiry OI concentration（40）＋鄰近 strike OI anomaly（30）＋ liquidity（15）＋ delta（15）。", "適合比較同一 expiry、同一 right 的結構集中度。", "不使用 contract volume、premium、historical volume 或 intraday burst。", "最新完整 Daily OI Archive"),
  contract_persistent_score: entry("合約持續部位分數", "Contract Persistent Positioning Score", "衡量該 contract 的 OI 是否跨多個有效 observation sessions 持續累積或下降。", "OI growth、相對同側 expiry OI 的 absolute build share、directional persistence；取 3／5／10 視窗最高分。", "描述 persistent positioning，不推論買賣方向。", "第一次觀察不假設 prior OI 為零。", "每日 vendor OI observation date"),
  oi_change_radar_status: entry("OI 變動雷達", "OI Change Radar", "Nightwatch ranked changed-contract subset 的額外證據；未出現在 Radar 不代表沒有 OI 變動。", "只標示 OBSERVED／NOT_OBSERVED 並保留 subset 證據。", "可補充 ΔOI、premium、rank。", "不得當作完整 OI universe 或 OI Share 分母。"),
  ticker_call_put_volume: entry("Ticker Call／Put 成交量", "Ticker Call/Put Volume", "整個 ticker 的當日 Call/Put activity；不能直接歸因到某一 expiry。", "來自 options.options_volume ticker-day payload。"),
  intraday_activity_v11: entry("盤中活動", "Intraday Activity", "Phase 2A v1.1 不參與 scoring。", "Weight = 0；completed payload semantics 驗證前為 research-only。", "目前顯示 INTRADAY_PROFILE_UNAVAILABLE。"),
  archive_vendor_oi_date: entry("Archive OI 日期", "Archive Vendor OI Date", "目前結果所重用的 Nightwatch vendor OI observation date。", "由 vendor date/as_of 決定，不以 job 執行日製造日期。", "顯示 Daily OI Archive freshness。", "同 vendor date 重跑會 skip/reuse，不新增重複 snapshot。"),
  ticker: entry("股票代號", "Ticker", "美股標的代號。", "固定 MAG7 清單。"),
  dte: entry("距到期日天數", "DTE", "以紐約市場日期計算的日曆天數。", "到期日 − America/New_York 市場日期。"),
  bucket: entry("到期區間", "Bucket", "依 DTE 分組的期限區間。", "0–7、8–30、31–90、91–180 日。"),
  bucket_at_detection: entry("偵測時到期區間", "bucket_at_detection", "偵測當下固定保存的期限分組。", "依 dte_at_detection 計算。", "歷史欄位不可覆寫。"),
  current_bucket: entry("目前到期區間", "current_bucket", "隨市場日期動態重算的期限分組。"),
  volume: entry("成交量", "Volume", "當日合約成交張數。"),
  open_interest: entry("未平倉量", "Open Interest / OI", "最近可得結算未平倉張數。", "供應商回傳。", "OI 有結算延遲。"),
  volume_oi_ratio: entry("成交量／未平倉量", "Volume/OI", "成交量相對既有 OI 的比例。", "today_volume / max(previous_oi, 1)。", "高比率不證明是新開倉；低 OI 也不會自動使異動無效。"),
  oi_status: entry("OI 確認狀態", "OI Status", "隔日 OI 證據的確認狀態。", "僅 PENDING、CONFIRMED、NOT_CONFIRMED、INCONCLUSIVE。", "Day-0 可能維持待確認。", "結算資料更新後"),
  estimated_premium: entry("估算權利金", "Estimated Premium", "以最佳可得價格代理估算的成交名目金額。", "volume × 100 × price_proxy。", "僅為規模估計。", "可能不等於實際成交權利金。"),
  premium_estimation_quality: entry("權利金估算品質", "Premium Estimation Quality", "標示 VWAP、供應商彙總、Last 或 Midpoint 等代理方法。"),
  bid: entry("買價", "Bid", "最佳可得買方報價。"),
  ask: entry("賣價", "Ask", "最佳可得賣方報價。"),
  mid: entry("中間價", "Mid", "有效 Bid 與 Ask 的中點。", "(bid + ask) / 2。"),
  spread_pct: entry("價差百分比", "Spread %", "買賣價差相對中間價。", "(ask − bid) / mid。", "越低通常代表流動性越好。", "超過 50% 會硬性排除。"),
  delta: entry("Delta", "Delta", "供應商可得的選擇權 Delta。", "不自行推估。"),
  low_oi_base: entry("低 OI 基準", "LOW_OI_BASE", "previous_oi < 100 的風險旗標。", "布林旗標。", "提醒比例可能被小分母放大。", "不會自動排除異動。"),
  lotto_risk: entry("彩券型風險", "LOTTO_RISK", "abs(delta) < 0.10 的風險旗標。"),
  history_insufficient: entry("歷史不足", "HISTORY_INSUFFICIENT", "有效歷史觀測少於 10 筆。", "該分項不計入可用權重，而不是記零分。"),
  zero_dte: entry("零日到期", "ZERO_DTE", "DTE = 0 的額外風險旗標。"),
  intraday_burst: entry("盤中爆量", "Intraday Burst", "最強五分鐘量相對穩健盤中基準。", "max rolling 5m volume / robust baseline。"),
  contract_anomaly_score: entry("合約異常分數", "Contract Anomaly Score", "活動、權利金、歷史、盤中、流動性與價內外程度的可用分項正規化分數。", "earned / available maximum × 100。", "65 分且權重至少 60 才是 CONTRACT_CANDIDATE。"),
  score_basis_weight: entry("分數基礎權重", "Score Basis Weight", "實際可用分項的最高總權重。", "加總可用分項滿分。", "分數高但基礎權重低時可信度有限。"),
  call_volume: entry("Call 成交量", "Call Volume", "指定到期日的 Call 成交張數。", undefined, undefined, "大額 Call 不自動代表看多。"),
  put_volume: entry("Put 成交量", "Put Volume", "指定到期日的 Put 成交張數。", undefined, undefined, "大額 Put 不自動代表看空。"),
  call_oi: entry("Call 未平倉量", "Call OI", "指定到期日的 Call OI。"),
  put_oi: entry("Put 未平倉量", "Put OI", "指定到期日的 Put OI。"),
  volume_skew: entry("成交量偏斜", "Volume Skew", "Call 與 Put 成交量的對稱差。", "(call_volume − put_volume) / total_volume。", "正負描述活動側別，不代表投資人方向。"),
  oi_skew: entry("OI 偏斜", "OI Skew", "Call 與 Put OI 的對稱差。", "(call_oi − put_oi) / total_oi。"),
  expiry_volume_share: entry("到期日成交量占比", "Expiry Volume Share", "該到期日占標的 0–180 DTE 總成交量的比例。"),
  expiry_oi_share: entry("到期日 OI 占比", "Expiry OI Share", "該到期日占標的 0–180 DTE 總 OI 的比例。"),
  neighbor_ratio: entry("鄰近到期日比率", "Neighbor Ratio", "目前到期日 OI 相對同類鄰近到期日中位數。", "current OI / median comparable OI。", "同類鄰居不足時為 unavailable。"),
  expiry_anomaly_score: entry("到期日異常分數", "Expiry Anomaly Score", "OI、鄰近異常、成交量、偏斜與權利金集中度的正規化分數。"),
  cluster_range: entry("群集履約價範圍", "Cluster Range", "同側候選合約群集的最小至最大履約價。"),
  cluster_volume: entry("群集成交量", "Cluster Volume", "群集內合約成交量總和。"),
  cluster_premium: entry("群集估算權利金", "Cluster Premium", "群集內可估算權利金總和。"),
  cluster_premium_share: entry("群集權利金占比", "Cluster Premium Share", "群集占同到期同側估算權利金的比例。"),
  cluster_volume_share: entry("群集成交量占比", "Cluster Volume Share", "群集占同到期同側成交量的比例。"),
  positioning_center: entry("部位中心", "Premium-Weighted Strike / Positioning Center", "依估算權利金加權的群集履約價中心。", "sum(strike × premium) / sum(premium)。", "僅描述集中位置。", "不是價格目標。"),
  cluster_score: entry("群集分數", "Cluster Score", "合約強度、集中度、連貫性與流動性的正規化分數。"),
  cluster_shape: entry("群集形狀", "Cluster Shape", "TIGHT_CLUSTER、BROAD_CLUSTER 或 LADDER 的決定性形狀分類。"),
  call_dominant: entry("Call 活動主導", "CALL_DOMINANT", "有效 Call 結構強於 Put 結構。", undefined, undefined, "不等同看多。"),
  put_dominant: entry("Put 活動主導", "PUT_DOMINANT", "有效 Put 結構強於 Call 結構。", undefined, undefined, "不等同看空。"),
  two_sided: entry("雙側活動", "TWO_SIDED", "Call 與 Put 都有有效結構。"),
  no_strong_structure: entry("無強結構", "NO_STRONG_STRUCTURE", "尚未形成符合規格的有效群集。"),
  provisional_candidate: entry("暫定部位候選", "PROVISIONAL_POSITIONING_CANDIDATE", "有效群集配合候選到期日的 Day-0 狀態。", undefined, undefined, "不是交易建議，也不是最終 Trade Candidate。"),
  pending: entry("待確認", "PENDING", "等待結算後 OI 證據。"),
  confirmed: entry("已確認", "CONFIRMED", "後續 OI 證據支持部位增加。"),
  not_confirmed: entry("未確認", "NOT_CONFIRMED", "後續 OI 證據未支持部位增加。"),
  inconclusive: entry("無法判定", "INCONCLUSIVE", "資料不足以完成 OI 確認。"),
  scan_status: entry("掃描狀態", "Scan Status", "COMPLETE、PARTIAL、PARTIAL_BUDGET_LIMIT、DATA_PENDING 或 FAILED。"),
  api_consumed_units: entry("API 已消耗單位", "API Consumed Units", "本次掃描中成功 200 的付費資料請求數。"),
  network_attempts: entry("網路嘗試次數", "Network Attempts", "本次掃描實際對 Nightwatch 發出的 HTTP 嘗試數。"),
  strongest_bucket: entry("最強到期區間", "Strongest Bucket", "標的最高分結果所在 DTE bucket。"),
  strongest_expiry: entry("最強到期日", "Strongest Expiry", "標的最高異常分數所在到期日。"),
  strongest_call_cluster: entry("最強 Call 群集", "Strongest Call Cluster", "最高分 Call 履約價群集。"),
  strongest_put_cluster: entry("最強 Put 群集", "Strongest Put Cluster", "最高分 Put 履約價群集。"),
  call_cluster_score: entry("Call 群集分數", "Call Cluster Score", "最強 Call 群集的分數。"),
  put_cluster_score: entry("Put 群集分數", "Put Cluster Score", "最強 Put 群集的分數。"),
  positioning_structure: entry("部位活動結構", "Positioning Structure", "Phase 2A 的側別結構標籤。", undefined, undefined, "描述活動，不是方向或買賣建議。"),
  last_scan: entry("最近掃描", "Last Scan", "此列結果所屬掃描的完成或開始時間。"),
} satisfies Record<string, GlossaryEntry>;

export type GlossaryKey = keyof typeof fieldGlossary;

export const visibleAnalyticalColumns = [
  "ticker", "strongest_bucket", "strongest_expiry", "same_day_activity_score",
  "persistent_positioning_score", "discovery_score", "discovery_source",
  "oi_share", "oi_share_change", "oi_skew", "history_coverage",
  "contract_structure_score", "contract_persistent_score", "oi_change_radar_status",
  "call_cluster_score", "put_cluster_score", "archive_vendor_oi_date", "last_scan",
] as const satisfies readonly GlossaryKey[];
