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
  "ticker", "strongest_bucket", "strongest_expiry", "expiry_anomaly_score",
  "strongest_call_cluster", "strongest_put_cluster", "call_cluster_score",
  "put_cluster_score", "positioning_structure", "oi_status", "last_scan",
] as const satisfies readonly GlossaryKey[];
