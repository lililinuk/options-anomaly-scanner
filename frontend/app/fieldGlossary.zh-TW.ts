export type GlossaryStatus = "ACTIVE" | "LEGACY_INACTIVE" | "WITHHELD";

export type GlossaryEntry = {
  狀態: GlossaryStatus;
  中文名稱: string;
  englishField: string;
  定義: string;
  計算方式: string;
  如何解讀: string;
  注意事項: string;
  更新頻率: string;
};

const entry = (
  狀態: GlossaryStatus,
  中文名稱: string,
  englishField: string,
  定義: string,
  計算方式: string,
  如何解讀: string,
  注意事項: string,
  更新頻率 = "依來源證據或明確評估更新",
): GlossaryEntry => ({ 狀態, 中文名稱, englishField, 定義, 計算方式, 如何解讀, 注意事項, 更新頻率 });

export const fieldGlossary = {
  product_candidate: entry("ACTIVE", "產品候選", "Product Candidate", "以 ticker／產品為單位的持久化研究物件；可連結多個合約或到期日異常。", "成功 Phase 2A materialization 將所有合格異常依 ticker 分組並保存一次。", "是今日研究清單的主體。", "Candidate 不是 contract，也不是排名、分數或交易建議。"),
  anomaly: entry("ACTIVE", "異常", "Anomaly", "Phase 2A 發現的精確合約或精確到期日證據。", "由 RADAR_EVENT、EXPIRY_ACTIVITY、CONTRACT_PERSISTENCE 其中一個 active family 產生。", "說明某個 Product Candidate 為何存在。", "Expiry anomaly 不需要也不可捏造 contract、right、strike 或 Greeks。"),
  why_found: entry("ACTIVE", "為何入選", "Why Found", "Product Candidate 的持久化 trigger 清單與各自的來源／時間證據。", "直接讀取 ProductCandidateTrigger；前端不重新計算 eligibility。", "分別查看每個 trigger 的 family、entity、qualification 與時間身分。", "Supporting Persistence 的 qualifies_candidate=false 不得顯示為合格 badge。"),
  deep_dive: entry("ACTIVE", "深度研究", "Deep Dive", "候選成立後才顯示的 Structure、Neighbor Strike within Structure 與 Cluster 背景。", "只呈現已接受／達門檻 Structure，以及 VALID_CLUSTER／STRONG_CLUSTER。", "補充異常附近的結構。", "不參與 Product Candidate qualification；INVALID_CLUSTER 與 subthreshold Structure 不可正面呈現。"),
  first_knowledge_baseline: entry("ACTIVE", "首次得知基準", "FIRST_KNOWLEDGE_BASELINE", "以不可變 candidate_first_knowledge_at 作 evidence cutoff 的凍結研究快照。", "只使用在首次得知 cutoff 前可證明已收到／觀察到的來源。", "是預設研究視圖，供未來 no-lookahead 研究使用。", "晚到資料不可回填；REFRESH 永遠不能覆蓋或冒充 baseline。", "每個 Product Candidate occurrence 最多一筆"),
  refresh: entry("ACTIVE", "內容更新", "REFRESH", "使用明確 context_evaluated_at cutoff 建立的追加式 ticker context。", "使用最多四個 ticker-level sources；每個 anomaly 零次額外 vendor call；Dealer/GEX 只讀 archive。", "用來查看較新的描述性市場背景。", "必須手動觸發並分開選取；不是 FIRST_KNOWLEDGE_BASELINE。", "使用者明確執行時"),
  same_day: entry("ACTIVE", "同日層", "SAME-DAY", "Expiry Activity 的證據時間層標籤。", "對應 EXPIRY_ACTIVITY trigger。", "表示同日到期日活動證據。", "不是交易方向，也不表示資料一定 session-complete。"),
  oi_confirmed: entry("ACTIVE", "OI 確認層", "OI-CONFIRMED", "Radar Event 的 OI publication／observation 時間層。", "對應 RADAR_EVENT trigger，保留 vendor observation 與 first receipt。", "表示 ranked changed-contract subset 中可追溯的 OI 變動證據。", "+ΔOI 不等於 bought-to-open；未出現在 Radar 不等於負面證據。"),
  multi_observation: entry("ACTIVE", "多觀測層", "MULTI-OBSERVATION", "Contract Persistence 的多個有效 OI observations 時間層。", "對應 CONTRACT_PERSISTENCE trigger，保留 window first／last dates。", "描述 build 或 decline 的持續性。", "PERSISTENT_BUILD／DECLINE 都不是交易方向。"),
  radar_event: entry("ACTIVE", "Radar 事件", "RADAR_EVENT", "vendor-ranked changed-contract subset 中符合已版本化門檻的精確合約事件。", "由已保存 threshold profile 重現 eligibility。", "是 contract anomaly family。", "不是單筆大單、機構行為或完整 option universe。"),
  expiry_activity: entry("ACTIVE", "到期日活動", "EXPIRY_ACTIVITY", "精確 expiry 的 same-day activity anomaly；0DTE 是其特殊校準方法。", "使用既有版本化 Phase 2A 規格。", "是 expiry anomaly family。", "不需要 contract；Call/Put volume 只描述側別活動。"),
  contract_persistence: entry("ACTIVE", "合約持續部位", "CONTRACT_PERSISTENCE", "完整 Daily OI Archive 上的 exact-contract multi-observation evidence。", "以既有 3／5／10 observation windows 與版本化 freshness policy 計算。", "是 contract anomaly family，也可作 supporting evidence。", "CURRENT_TRIGGER_FRESHNESS_MODE 仍為 CALIBRATION_REQUIRED；不得自行設定數值視窗。"),
  block_b1: entry("ACTIVE", "B1 標的價格", "B1 Underlying Price Context", "ticker 共用的 canonical close、1D／5D／20D、SMA20／50、ATR14 與選配 Trend State。", "只使用 canonical regular-session observations。", "描述價格環境。", "不輸出 Bullish／Bearish；missing 不補零。"),
  block_b2: entry("ACTIVE", "B2 波動率", "B2 Volatility Context", "ticker 共用 term payload 與 expiry-anchored IV；contract IV 留在 B4。", "每 ticker evaluation 共用一次 term structure，依 expiry 精確匹配。", "描述 candidate expiry 的 volatility environment。", "IV 不分 cheap／expensive，不參與候選資格。"),
  block_b3: entry("ACTIVE", "B3 Dealer／GEX", "B3 Dealer/GEX Context", "只讀 archive 的 spot、anchor expiry 與三個 raw GEX nodes。", "以 vendor_observed_at 與 captured_at 不晚於 cutoff 的 snapshot 查詢。", "描述結構位置與 raw net GEX sign。", "GEX sign 不等於方向；不產生 Dealer Bullish／Bearish。"),
  block_b4: entry("ACTIVE", "B4 異常明細", "B4 Anomaly Context", "每個 persisted trigger 一筆的 contract 或 expiry 專屬內容。", "Contract 顯示 identity／DTE／IV／Delta／bid／ask；Expiry 顯示 activity recap 與 expiry-anchored B2/B3。", "讓 anomaly 保持自己的 entity 邊界。", "Expiry view 不可捏造 contract 欄位；不含 execution score。"),
  block_b5: entry("ACTIVE", "B5 來源與可用性", "B5 Provenance / Availability", "候選與異常層的來源 ID、時間身分、規格／設定版本與每層 availability。", "每層獨立保存 AVAILABLE／PARTIAL／UNAVAILABLE／NOT_YET_AVAILABLE。", "用來判讀證據是否存在及其時間。", "不合成 readiness、conviction 或 quality score。"),
  availability: entry("ACTIVE", "資料可用狀態", "Availability", "每一資料層獨立的 AVAILABLE、PARTIAL、UNAVAILABLE、NOT_YET_AVAILABLE。", "由 backend source and normalized state 保存。", "缺一層不應隱藏其他可用層。", "missing ≠ zero；HISTORY_IMMATURE／STALE_DATA／FEATURE_UNAVAILABLE 必須如實顯示。"),
  candidate_first_knowledge_at: entry("ACTIVE", "候選首次得知時間", "candidate_first_knowledge_at", "系統首次具備足夠 admissible evidence 並 materialize Product Candidate 的不可變 UTC 時間。", "成功 scan transaction 截止點只設定一次。", "Forward Outcome 未來只能以此 anchor。", "不可用 event_date、created_at 或 refresh time 代替。"),
  context_evaluated_at: entry("ACTIVE", "內容評估時間", "context_evaluated_at", "Stage 6 context 實際計算時間。", "Baseline 與 Refresh 都明確保存。", "與 candidate first knowledge 分開閱讀。", "Baseline 的 evidence cutoff 仍是 candidate_first_knowledge_at。"),
  source_first_received_at: entry("ACTIVE", "來源首次收到時間", "source_first_received_at", "系統第一次收到某 source-evidence identity 的時間。", "append-only 保存。", "顯示系統何時實際知道證據。", "不能以 vendor date 或 local reprocess created_at 取代。"),
  vendor_observed_at: entry("ACTIVE", "供應商觀測時間", "vendor_observed_at", "供應商聲明的分析／資料觀測時間。", "來源沒有提供時保持 NULL。", "與 local capture 一起判讀 no-lookahead。", "不得默默 fallback 到 local time。"),
  local_captured_at: entry("ACTIVE", "本地擷取時間", "local_captured_at", "本系統傳輸層保存來源 payload 的 UTC 時間。", "由 ingestion capture 保存。", "說明本地何時取得資料。", "不代表 vendor 何時觀測。"),
  price_as_of: entry("ACTIVE", "價格資料時點", "price_as_of", "B1 使用的價格來源 as-of。", "由來源 provenance 明確保存。", "判讀價格資料年齡。", "不是 context evaluation time。"),
  quote_as_of: entry("ACTIVE", "報價資料時點", "quote_as_of", "B4 bid／ask／spread 使用的 quote timestamp。", "直接讀取 chain archive 的 quote time。", "說明 execution 描述的時間。", "不可用 capture time 冒充。"),
  iv_rank: entry("WITHHELD", "IV Rank 原值", "IV Rank — WITHHOLD_PENDING_PROVENANCE", "ticker-level vendor raw value；vendor window／scale semantics 尚未驗證。", "只保存 raw value、entity 與 provenance。", "若顯示，必須同時顯示 provenance warning。", "不可分類 LOW／MID／HIGH，不可用於 eligibility、score 或 cheap／expensive 判斷。"),
  zero_dte_status: entry("ACTIVE", "0DTE 證據身分", "0DTE Snapshot Kind", "PROVISIONAL_INTRADAY、CANONICAL_SESSION_COMPLETE、LEGACY_OR_AMBIGUOUS 三種明確身分。", "manual scan 保存 provisional；daily EOD 保存 canonical；舊資料無法證明時為 legacy/ambiguous。", "先看 current status，再看 canonical history x/y 與 basis。", "provisional／ambiguous 不得冒充 canonical research baseline。"),
  raw_radar_scope: entry("ACTIVE", "原始 Radar 範圍", "Raw / scoped Radar evidence view", "每 ticker 最新 eligible vendor date 的 ranked subset 稽核表。", "依既有 backend query 排序；UI 可限制顯示列數。", "只供支持與 audit。", "不是 Product Candidate list；scope、排序與 truncation 必須揭露。"),
  direction_unresolved: entry("ACTIVE", "方向未解析", "UNRESOLVED", "現有 evidence 無法辨識 long／short、opening／closing、spread 或 hedge 的經濟方向。", "不從 Call／Put、ΔOI、premium、price 或 GEX 推導。", "誠實保留方向未知。", "UNRESOLVED ≠ Neutral。"),
  evidence_breadth_legacy: entry("LEGACY_INACTIVE", "歷史證據廣度", "Evidence Breadth — legacy/inactive", "舊 Phase 2A／2B 的家族計數概念。", "vNext 不計算。", "只可用於歷史 audit。", "不得作為 candidate qualification、readiness 或 score。"),
  stabilization_bias_legacy: entry("LEGACY_INACTIVE", "歷史穩定化標籤", "STABILIZATION_BIAS — legacy/inactive", "舊 Dealer/GEX tautological label。", "vNext 不產生；只保留 raw nodes。", "只供歷史資料辨識。", "不得在 active dashboard 顯示為研究結論。"),
  downside_risk_legacy: entry("LEGACY_INACTIVE", "歷史下行放大標籤", "DOWNSIDE_ACCELERATION_RISK — legacy/inactive", "舊 Dealer/GEX conditional label。", "vNext 不產生；只保留 raw nodes。", "只供歷史資料辨識。", "不得在 active dashboard 顯示為方向／風險結論。"),
  composite_readiness_legacy: entry("LEGACY_INACTIVE", "歷史合成準備度", "Composite Research Readiness — legacy/inactive", "把多層 availability 合成單一狀態的舊概念。", "vNext 不計算。", "每層 availability 應獨立閱讀。", "不得變成 score 或候選排序。"),
  greeks_legacy_phase2b: entry("LEGACY_INACTIVE", "非 Phase 2B 核心 Greeks", "Gamma / Theta / Vega — not Phase 2B core", "仍可存在於原始 chain archive，但已離開 Phase 2B 顯示核心。", "vNext B4 只保留 Delta 作 moneyness/sensitivity descriptor。", "未來可能屬 Trade Expression input。", "Stage 7 不顯示為 Phase 2B core，也不建立 execution score。"),
} satisfies Record<string, GlossaryEntry>;

export const glossarySemantics = {
  candidateEntity: "TICKER_PRODUCT",
  anomalyEntities: ["CONTRACT", "EXPIRY"],
  expiryAnomalyRequiresContract: false,
  evidenceBreadthActive: false,
  stabilizationBiasActive: false,
  downsideAccelerationRiskActive: false,
  phase2bCoreGreeks: ["DELTA"],
  missingEqualsZero: false,
  unresolvedEqualsNeutral: false,
  callImpliesBullish: false,
  putImpliesBearish: false,
  positiveDeltaOiImpliesOpening: false,
  gexSignImpliesDirection: false,
} as const;

export type GlossaryKey = keyof typeof fieldGlossary;

export const visibleAnalyticalColumns = Object.keys(fieldGlossary) as GlossaryKey[];
