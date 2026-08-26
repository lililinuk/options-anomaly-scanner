# Nightwatch Options Anomaly Scanner — Phase 2B Fresh Independent Architecture Review

**審查日期:** 2026-08-17
**審查性質:** 唯讀(read-only)。未修改任何程式碼、未寫入任何資料庫、未觸發任何付費 Nightwatch 呼叫。
**授權文件:** `PHASE2B_FRESH_REVIEW_MASTER_BRIEF_20260817.md`(本報告依其 §16 交付 A–K 全部成果)
**文件權威層級(依 Master Brief §2):**

```text
A. 2026-08-15 Handoff            = 已實作基線 / 歷史技術參考
B. 2026-08-17 Independent Audit  = 程式碼實證的缺陷/風險清單(證據,非教條)
C. Phase 2A vNext Decision       = 現行規範性產品決策(Phase 2A 部分為最終權威)
```

**程式碼重驗證範圍:** 本審查另行讀取了現行工作樹(staged 2026-08-17,HEAD 1e29c92 之後、含 0817 rollover 實驗檔)之 `app/confirmation/{config,domain,service,state_v2,workspace_v3}.py`、`app/api/routes/scans.py`、`app/scanner/{v11,v13}.py`、`app/cli.py`、`app/db/models.py`、`app/dealer_archive/repository.py`、`app/nightwatch/client.py`、`frontend/app/scan-dashboard.tsx`,關鍵行號皆以此副本為準。本報告引用 Audit 發現時均已對照現行程式碼確認仍然成立,並新增數項 Audit 未涵蓋的程式碼實證發現(標記 N1–N5)。

**獨立性聲明(依 Master Brief §17):** 本審查不重開 Founder 已批准的 Phase 2A vNext 決策。審查過程中**未發現任何 critical technical incompatibility** 需要重開 vNext;發現的是數項「vNext 落地時 Phase 2B 必須同步處理的整合需求」,列於 §L(單獨陳報,非重新設計 Phase 2A)。

---

# 總覽判定

```text
PHASE 2B v3.1 內容(欄位/語意)         MOSTLY SOUND
PHASE 2B v3.1 結構(層疊/實體/入口)     OVERCOMPLICATED
PHASE 2B v3.1 與 vNext 候選模型相容性    MISALIGNED(contract-only,無法直接承接 Product Candidate)
建議路徑                                 REDESIGN THE FRAME, KEEP MOST CONTENT
建議架構                                 Model B(5 個概念區塊,詳 §D)
```

一句話總結:Phase 2B v3.1 收集的**事實**大多值得保留,但它把這些事實包在三層堆疊規格(v1.2 context → v2.0 state → v3.1 workspace)、以 exact contract 為唯一入口、且只服務 Radar 觸發合約的框架裡;vNext 的 Candidate = Product/Ticker 模型正好提供一次把框架砍平的機會——**一層 evaluation、兩級實體(ticker 共享 + anomaly 明細)、五個概念區塊**。

---

# A. Phase 2B v3.1 現況重建(Current-State Reconstruction)

## A.1 三層堆疊的持久化結構(程式碼實證)

Phase 2B 目前不是一個規格,而是**三個互相堆疊、各自持久化、各自帶版本的規格層**:

| 層 | 規格常數 | 資料表 | 建立方式 | 內容 |
|---|---|---|---|---|
| L1 Context + Evaluation | `signal_spec_v1.2_phase2b`(`confirmation/config.py:11`) | `Phase2bTickerContextSnapshot` + `Phase2bCandidateEvaluation` | CLI `refresh-phase2b-context --contract`(付費) | 每 ticker 5 個付費端點 + 每合約一筆 evaluation(joins 既有 DB 證據) |
| L2 State | `signal_spec_v2.0_phase2b`(`state_v2.py:21`) | `Phase2bCandidateState` | CLI `build-phase2b-v2-states`(純 DB) | positioning presence/廣度、price/volatility/dealer/execution 六維狀態、Research Readiness |
| L3 Workspace | `signal_spec_v3.1_phase2b`(`workspace_v3.py:23`) | `Phase2bV3ResearchWorkspace` | CLI `build-phase2b-v3-workspaces`(純 DB) | 三 Role 卡的最終呈現物 + Dealer/GEX 結構(floor/upper/below/adjacent)+ provenance |

讀取路徑:`GET /candidates/{contract_symbol}/confirmation`(`scans.py:250-259`)回傳 L1 evaluation + 內嵌 `v2_state` + `v3_research_workspace`(`service.py:456-493`);404 時 UI 是死路(Audit 已證,現行碼未變)。

## A.2 L1 的付費呼叫形狀(每 ticker 5 個端點)

`Phase2bContextService.ENDPOINTS`(`service.py:65-71`):

```text
daily_ohlc       /v1/stocks/ohlc/{ticker}?candle_size=1d
stock_state      /v1/stocks/stock-state/{ticker}
iv_rank          /v1/volatility/iv-rank/{ticker}
term_structure   /v1/volatility/term-structure/{ticker}
dealer_heatmap   /v1/derived/heatmap/{ticker}/snapshot?format=full   ← 見 N1
```

Ticker context 以 `created_at >= now - min(五個 freshness 設定)` 判斷可重用(`service.py:139-152`);同 ticker 多合約共享一份 context——**ticker 級共享的雛形其實已經存在**,這是 vNext 重構可直接繼承的正資產。

## A.3 每合約 evaluation 的組裝

`_evaluation`(`service.py:318-453`)對每個合約 join:最新 radar 列(依 observation_date)、最新 chain 快照、最新 contract scan 觀測、最新 expiry 觀測、該 ticker+expiration 的**全部** clusters 取分數前 5(**不過濾 INVALID_CLUSTER**,`service.py:351-356, 412-416`)。輸出含 phase2a_evidence、strike_location(vs spot、ATR 正規化)、volatility_context(term topology)、dealer_context(evaluate_heatmap)、execution_context(bid/ask/spread/Greeks/OI)、`direction="UNRESOLVED"`、`evaluated_at=utc_now()`。

## A.4 新增程式碼實證發現(Audit 未涵蓋,N1–N5)

### N1 — Phase 2B 的 dealer_heatmap 呼叫仍使用已被證實無效的 `format=full`

`service.py:70` 對 `/v1/derived/heatmap/{ticker}/snapshot` 送出 `{"format": "full"}`。Handoff §70 已記錄同一端點帶 `format=full` 會收到 `HTTP 400 VALIDATION_ERROR`,dealer archive 已於 2026-08-14 改為 `params=None`,**但 Phase 2B context 這條路徑從未跟著修**。推論(需唯讀證明,見 §G):每次 fresh ticker context 的第 5 個付費呼叫大概率固定失敗 → `context.dealer_heatmap` UNAVAILABLE → L1 `dealer_context` 與 L2 dealer state 的 sign 為 UNKNOWN → v3 workspace 之所以還有 GEX 結構,是因為 `best_archived_surface_at_or_before` 的 archive 回退(`workspace_v3.py:565-570`)。**驗證方式零成本:** 查 DB `endpoint_statuses['dealer_heatmap']` 的 status/availability 即可,毋須任何付費呼叫。

含義:(a) 每 ticker 每次 refresh 浪費一次網路嘗試;(b) v3.1 的 Dealer/GEX 實際上已經是 archive-only——**把 Phase 2B 的 heatmap 呼叫正式移除、改為明文 archive-only,是零資訊損失的簡化**。

### N2 — Phase 2B 目前只服務 Radar 觸發的合約

`_candidate_source`(`service.py:116-137`)要求該合約同時存在 `deep_dive_eligible=True` 的 radar 觀測**與** chain 快照,否則靜默回傳 None。因此:CONTRACT_PERSISTENCE 單獨觸發的合約(無 radar 列)與 EXPIRY_ONLY 候選**完全進不了 Phase 2B**。在 vNext 的 Product Candidate 模型下,這從「已知缺口」升級為**結構性不相容**:一個 ticker 候選的 Why Found 可能全部來自 Expiry Activity 與 Persistence,而現行 Phase 2B 對它無話可說。此為 §L 整合需求之一。

### N3 — 同一組證據被三層重述三次

phase2a 證據在 L1 `phase2a_evidence` → L2 `positioning_state` → L3 `opportunity_positioning` 各存一份重新包裝;price/volatility/execution 亦同。三層各自帶 spec/config version+hash。可追溯性是優點,但**每加一個欄位要改三層、看一個候選要對三層**,是目前 Phase 2B 維護與理解成本的主要來源。

### N4 — Audit 關鍵發現逐條對現行碼確認仍成立

- detection 欄位重綁至最新 radar 事件:`service.py:117-124, 329-333` ✔
- vendor/local 時間戳混鍵 `generated_at or capture_timestamp`:`service.py:206, 310`、`workspace_v3.py:215` ✔
- reprocess 以新 `created_at` 洗新舊 vendor 資料:`service.py:162-220` + 新鮮度檢查 `service.py:139-152` ✔
- STRUCTURE/CLUSTER presence 無門檻計入 MULTI_EVIDENCE:`state_v2.py:204-217` ✔
- STABILIZATION_BIAS 恆真(floor 定義已保證 strike<spot):`workspace_v3.py:246-258, 308-310` ✔
- DOWNSIDE_ACCELERATION_RISK 無量級門檻:`workspace_v3.py:276-280` ✔
- 相鄰 expiry 浮點精確等值比對:`workspace_v3.py:163` ✔
- `evaluate_heatmap.nearest()` 缺 strike 列視為距離 0:`domain.py:430-437` ✔
- INVALID_CLUSTER 渲染為 CALL/PUT_STRUCTURE:`scans.py:584-593` ✔

### N5 — Research Readiness 的 execution 層把 Greeks 當必要條件

`state_v2.py:332-337` 要求 bid+ask+delta 齊備才 READY。Greeks 主要是 Trade Expression 輸入(§E),把它作為「研究脈絡完整度」的必要條件,使 readiness 偏向懲罰與研究無關的缺失。

## A.5 現況小結

v3.1 做對的事:ticker context 共享、append-only + 全鏈版本化、provenance 含 source ids/request ids/time-eligible、archive 優先 + no-lookahead 的 dealer 查詢(`repository.py:219-231`)、語意防護字串系統、`direction=UNRESOLVED` 紀律。做錯的事集中在:三層堆疊、contract-only 入口、時間身份混疊、恆真標籤、以及一條早已死亡卻仍在付費的 heatmap 呼叫。

---

# B. Phase 2B 複雜度判定(Complexity Verdict)

```text
內容層(收集哪些事實)      JUSTIFIED — 絕大多數欄位有存在理由,少數屬 Trade Expression 越位
結構層(如何組織與持久化)  OVERCOMPLICATED — 三層規格堆疊 + 三次重述 + 三個 CLI 步驟
實體層(掛在什麼上)        MISALIGNED — exact contract 唯一入口,與 Candidate=Ticker 不相容
時間層(何時知道什麼)      UNRELIABLE — 重綁/混鍵/洗新三缺陷使「當時知道什麼」不可信
綜合                        SOMEWHAT OVERCOMPLICATED, STRUCTURALLY MISALIGNED
```

與 Phase 2A 的診斷同構:問題不是資料太多,而是**框架把三件不同的事(ticker 環境、anomaly 明細、資料品質/時間)壓進一個 contract 掛鉤的三層物件**。

---

# C. Phase 2B 的一句話工作(One-sentence Purpose)

> **Phase 2B 的唯一工作:對每一個 Phase 2A 產出的 Product/Ticker Candidate,補上可追溯、非方向性、最小充分的「這個標的現在處於什麼市場環境」事實脈絡(ticker 級共享)與「這些 anomaly 所在的合約/到期日長什麼樣」明細(anomaly 級),讓研究者與未來的 Forward Outcome 研究能在無前視、無語意歧義下理解候選——不判斷可行動性,不建議交易。**

它嚴格停在 Master Brief §6 的邊界內:Candidate Context ≠ Actionability Evidence ≠ Trade Expression Inputs。

---

# D. 建議 Phase 2B 架構(≤5 個概念區塊)+ 三個備選模型

## D.1 兩級實體原則

```text
PRODUCT CANDIDATE (= ticker)
├── SHARED TICKER CONTEXT      每 ticker 取一次、存一次、顯示一次
└── ANOMALY DETAILS            每個 anomaly(contract 或 expiry)一份,只放該實體特有的事實
```

任何在 anomaly 之間重複的 ticker 級資料(價格、IV rank、GEX surface)一律上移共享;任何只對單一合約/到期日有意義的資料(strike location、term 節點、報價)留在 anomaly 級。

## D.2 五個概念區塊(Model B,建議採納)

```text
B1  TICKER PRICE BASELINE            [ticker 級,共享]
    latest regular close、1D/5D/20D、SMA20/50(+距離)、ATR14、
    20 日高低、trend state(UPTREND/DOWNTREND/MIXED/UNKNOWN)
    來源:daily_ohlc + stock_state(每 ticker 各 1 次付費呼叫)

B2  TICKER VOLATILITY BASELINE       [ticker 級,共享;expiry 錨定在 anomaly 級衍生]
    vendor IV Rank(raw 值,不分類)、term structure 節點全表
    anomaly 級衍生:candidate/shorter/longer expiry IV、threshold-free topology、
    contract IV vs expiry node、implied move(vendor 值)
    來源:iv_rank + term_structure(每 ticker 各 1 次付費呼叫;衍生零成本)

B3  DEALER/GEX STRUCTURE             [ticker 級 surface,anomaly-expiry 錨定;ARCHIVE-ONLY]
    來源:既有每日 Dealer/GEX archive(零新增付費呼叫;移除 Phase 2B 自己的 heatmap 端點)
    每個 anomaly expiry 錨定:Primary Floor / Upper Node / Below-Floor Node(數值 + 符號)、
    adjacent expiry 同 strike 對照(修浮點比對)
    呈現為描述性數值;STABILIZATION_BIAS / DOWNSIDE_ACCELERATION_RISK 字樣移除(§E)

B4  ANOMALY OPTION DETAIL            [anomaly 級]
    contract anomaly:strike location(vs spot、ATR 正規化)、contract IV、
      execution 快照(bid/ask/spread/OI,標注 quote as-of;描述性,非 gate)、
      Phase 2A Deep Dive 的 Structure/Cluster 脈絡(僅 VALID/STRONG 呈現)
    expiry anomaly:expiry 活動證據回放 + 該 expiry 的 B2/B3 錨定視圖(不假造合約級資料)

B5  PROVENANCE / TIME / DATA QUALITY  [candidate 級 + anomaly 級]
    §12 七個時間身份的顯式分離(event_date / source_first_received_at /
    candidate_first_knowledge_at / context_evaluated_at / price_as_of /
    vendor_observed_at / local_captured_at)
    各區塊 availability 狀態(缺=NULL,不減分、不合成單一 readiness 等級)
    raw payload ids / request ids / spec+config version(沿用現行 provenance 設計)
```

持久化上收斂為**單一 evaluation 層**(candidate 級一筆 + anomaly 級明細),取代 v1.2/v2.0/v3.1 三層;舊三層資料表按 append-only 原則原樣保留、只讀。

## D.3 三個備選模型

| | Model A — Minimal | Model B — Balanced(建議) | Model C — Extended |
|---|---|---|---|
| Ticker 共享 | B1 價格基線 + B5 時間/品質 | B1+B2+B3+B5 | 同 B,另加 IV-RV、skew、event risk、GEX Evolution 標籤 |
| Anomaly 級 | Why Found 回放 + strike location | B4 全部 | B4 + 完整 GEX surface 互動探索 |
| 每 ticker 付費呼叫 | 2(ohlc、stock_state) | 4(+iv_rank、term_structure;heatmap 改 archive) | ≥5 |
| 損失/風險 | 丟掉 IV 與 GEX 脈絡——這兩者是「合約貴不貴、價格路徑結構如何」僅有的非重複資訊,且資料已在收 | — | 全部新增項未經校準,違反 §15 empirical boundary;GEX Evolution 需 ≥10 觀測/ticker,現僅 2 |
| 判定 | 過度削減 | **採納** | 全數列為 VALIDATE-FIRST / 後續研究,不進入 vNext Phase 2B |

**推薦 Model B,理由:** (1) 相對 v3.1 呼叫成本下降(5→4/ticker)且移除一條死呼叫;(2) 內容上只刪冗餘與恆真標籤,無單一材料性資訊損失(逐項見 §E);(3) 結構上一層取代三層、兩級實體對齊 vNext 候選模型;(4) 在 50–100 tickers 下成本線性且僅對「合格候選 ticker」發生,非全宇宙(§F)。不建立任何綜合 100 分制 Phase 2B 分數。

---

# E. 元件裁決表(Component Decision Table)

裁決詞彙依 Master Brief §8:KEEP / SIMPLIFY / MOVE / MERGE / OPTIONAL / REMOVE / VALIDATE-FIRST。凡 REMOVE 均註明損失了什麼材料性資訊。

## E.1 Price

| 元件 | 裁決 | 說明 |
|---|---|---|
| latest regular close | **KEEP**(B1) | canonical regular session 語意保留(`domain.py:35-61`品質良好) |
| 1D/5D/20D returns | **KEEP**(B1) | 最小充分的多尺度回報 |
| SMA20/SMA50 | **KEEP**(B1) | trend state 的定義基礎 |
| distance to SMA | **SIMPLIFY** | 保留為顯示層衍生值(close 與 SMA 已存,毋須獨立持久化決策地位) |
| recent high/low(rolling 20) | **KEEP-OPTIONAL** | 同 payload 零成本;描述性 |
| ATR14 | **KEEP**(B1) | strike distance 的 ATR 正規化是跨 ticker 可比的唯一機制,材料性高 |
| trend state | **KEEP**(B1) | threshold-free、事實性;維持「不得與 Call/Put 合成方向」紅線 |

## E.2 Volatility / Option Context

| 元件 | 裁決 | 說明 |
|---|---|---|
| contract IV | **MOVE → B4** | 合約級事實,掛 anomaly 不掛 ticker |
| IV Rank | **KEEP**(B2) | raw 值;不得加 LOW/MID/HIGH(維持 handoff §58) |
| shorter/candidate/longer expiry IV | **KEEP**(B2 衍生) | 同一 term payload 對多個 anomaly expiry 各自錨定,零額外成本 |
| IV term topology(六態) | **KEEP/SIMPLIFY** | threshold-free 分類,保留;呈現降為輔助說明而非狀態徽章 |
| implied move | **KEEP-OPTIONAL** | vendor 提供值,不自算、不衍生預期區間判定 |

## E.3 Contract Characteristics

| 元件 | 裁決 | 說明 |
|---|---|---|
| Delta | **KEEP**(B4,描述性) | moneyness 脈絡;Phase 2A Structure 已用其分量 |
| Gamma / Theta / Vega | **MOVE → Trade Expression** | 損失評估:對「理解候選環境」無增量;它們回答的是「怎麼交易」。資料照舊隨 chain 快照封存,未來 Trade Expression 直接可用——**移出顯示層,不停止收集** |
| bid / ask | **KEEP**(B4,描述性) | 必須標注 quote as-of(新加坡正午快照語意,Audit §13) |
| spread / liquidity / execution quality | **雙層裁決** | 描述性快照 = KEEP(B4);作為 gate = **MOVE → Actionability**(VALIDATE-FIRST)。回答 §7 Q12:兩個抽象層各留一半 |

## E.4 Positioning(vNext 已裁定,此處確認 Phase 2B 側的承接)

| 元件 | 裁決 | 說明 |
|---|---|---|
| Contract Structure | **MOVE → Phase 2A Deep Dive**(vNext 既定);Phase 2B 僅引用 | B4 呈現時 **VALID 門檻過濾**(score≥65 且無 hard reject) |
| Neighbor Strike | **MERGE → Structure 分量**(vNext 既定) | 不再是獨立詞彙 |
| Cluster | **MOVE → Phase 2A Deep Dive**(vNext 既定);Phase 2B 僅引用 | 僅 VALID/STRONG 呈現;INVALID_CLUSTER 永不作為正面證據(修 `service.py:351-356` 的無過濾 top-5 與 `scans.py:584-593`) |

## E.5 Dealer / GEX

| 元件 | 裁決 | 說明 |
|---|---|---|
| Primary Floor | **KEEP**(B3) | 描述性節點(strike + net GEX 數值 + 距 spot) |
| Upper Positive-GEX Node | **KEEP**(B3) | 同上 |
| Below-Floor Node | **KEEP**(B3) | 呈現數值與符號;不冠風險字樣 |
| Adjacent Expiry Context | **KEEP/SIMPLIFY**(B3) | 事實性同 strike 對照;修浮點等值比對;「單一可用且為負」與「兩者皆負」分開標示 |
| `STABILIZATION_BIAS` | **REMOVE(as label)** | 損失評估:**零**。恆真標籤(floor 存在 ⇒ 必然成立,`workspace_v3.py:308-310`),其全部資訊已由「floor 存在 + spot 位置」承載。改為描述句;任何 BIAS 字樣須經 forward-outcome 校準(VALIDATE-FIRST) |
| `DOWNSIDE_ACCELERATION_RISK` | **REMOVE(as label)** | 損失評估:**零**。無量級門檻(−$1 也觸發),資訊已由 below-floor node 的符號+數值承載。同上 VALIDATE-FIRST |
| full GEX surface | **KEEP-ARCHIVE / REMOVE from per-candidate display** | 每日封存照常(GEX Evolution 前置);Phase 2B 顯示僅 anchor±1;Phase 2B 自己的 heatmap 付費呼叫**移除**(N1,archive-only) |

## E.6 v2/v3 結構性元件(§8 未列,但必須裁決)

| 元件 | 裁決 | 說明 |
|---|---|---|
| Evidence Breadth / MULTI_EVIDENCE | **REMOVE**(vNext 既定) | 由 threshold-filtered 家族狀態列表取代(PRESENT/ABSENT/NOT_YET_AVAILABLE) |
| Research Readiness(COMPLETE/PARTIAL/LIMITED) | **SIMPLIFY → B5** | 保留各層 availability 事實;取消三態合成等級與「execution 需 Greeks」條件(N5)。損失評估:合成等級是可從各層狀態即時推出的顯示便利,無獨立資訊 |
| 三層 spec 堆疊(v1.2/v2.0/v3.1) | **MERGE → 單層 evaluation** | 舊表只讀保留;新層 additive |
| `direction=UNRESOLVED` 欄位 | **KEEP** | 紅線紀律的載體 |
| provenance 設計(raw ids/request ids/time-eligible) | **KEEP** | 全案最強資產之一,原樣搬入新層 |

---

# F. Entity / Time / API 矩陣

「共享」= 每 ticker 每 session 至多一次;「衍生」= 零 API 成本。時間層:SAME-DAY(當日活動)/ DELAYED(vendor OI 確認,T+lag)/ MULTI-DAY(跨觀測)/ CURRENT(取用當下)。

| 資料 | 實體 | 時間層 | 來源 | 取得方式 | 50–100 tickers 擴展性 |
|---|---|---|---|---|---|
| OHLC 價格基線 | ticker | CURRENT(價格 as-of) | `/v1/stocks/ohlc` 1d | 共享,1 call/ticker | 線性;僅對合格候選 ticker 呼叫 |
| Stock state(spot) | ticker | CURRENT | `/v1/stocks/stock-state` | 共享,1 call/ticker | 線性 |
| IV Rank | ticker | CURRENT(vendor date) | `/v1/volatility/iv-rank` | 共享,1 call/ticker | 線性 |
| Term structure 節點 | ticker(expiry 錨定衍生) | CURRENT(vendor date) | `/v1/volatility/term-structure` | 共享,1 call/ticker;每 anomaly expiry 衍生 | 線性;anomaly 數不增呼叫 |
| Dealer/GEX surface | ticker(expiry 錨定衍生) | DELAYED(15:30 ET 封存,vendor generated_at) | 既有每日 archive | **零新增呼叫**(N1 廢除 Phase 2B 端點) | 排程呼叫 = 宇宙大小,與候選數無關;需獨立評估 quota |
| Radar 事件 | contract | DELAYED(vendor obs date 區間) | 每日收集(`oi_change`) | Phase 2A 既有,Phase 2B 只讀 | 由 daily pipeline 承擔 |
| Expiry activity | expiry | SAME-DAY | 掃描時 `expiry_breakdown`+`options_volume` | Phase 2A 既有 | 掃描成本已知 ~2 calls/ticker |
| Contract persistence 歷史 | contract | MULTI-DAY | 自建 OI archive | Phase 2A 既有,Phase 2B 只讀 | 由 daily pipeline 承擔 |
| Chain 快照(quote/Greeks/IV) | contract | CURRENT-STALE(quote as-of 需標注) | Phase 2A deep dive 時已存 | Phase 2B 只讀 | 不新增 |
| Structure / Cluster | contract/expiry | DELAYED(OI surface) | Phase 2A deep dive | Phase 2B 只讀(VALID-gated) | 不新增 |

回答 §7 Q14:v3.1 的五端點中四個本已 ticker 級共享;唯一應改變的是 dealer_heatmap(改 archive、零呼叫)。anomaly 級**不存在任何需要新增的 per-anomaly 付費呼叫**。

Phase 2B 成本公式(Model B):`4 × 當日合格候選 ticker 數`。MAG7 最壞 28 calls;100-ticker 宇宙若日均 10–20 個候選 = 40–80 calls,仍遠低於全宇宙掃描本身的成本增長;真正的擴展瓶頸在 daily pipeline 與 dealer archive(= 宇宙大小),應在 Universe Expansion Design Gate 一併評估,不屬 Phase 2B 範圍。

---

# G. 缺陷對賬矩陣(Defect Reconciliation Matrix)

分類詞彙依 Master Brief §11。「歷史可修?」= 歷史資料能否被權威性修復(不能者依紅線保持 NULL/UNRESOLVED,不回寫)。凡與 Audit P0/P1 標籤不同者為本審查在新架構下的重新分級。

| # | 缺陷(證據) | 分類 | 為何重要 / 新架構下是否存活 | 最小安全修法 | 遷移? | 歷史可修? |
|---|---|---|---|---|---|---|
| G1 | 空狀態五態同貌;proxy 失敗回 200(`route.ts:11`) | **FIX_BEFORE_VNEXT_IMPLEMENTATION** | 每天都在違反 missing≠zero 第一原則;與架構無關,存活 | 表格接收 availability 狀態機;proxy 傳真實錯誤 | 否 | N/A |
| G2 | Radar backfill 改寫歷史 `captured_at/ny_market_date`(`daily.py:596-597`) | **FIX_BEFORE_VNEXT_IMPLEMENTATION** | 每多跑一天,不可修復的血緣汙染就多一天;存活 | 停止就地改寫;重評估寫新版本列/新欄位 | 輕(加欄位/表) | **否**——已被覆寫的原始 captured_at 永久遺失,標記 UNRESOLVED,不回填 |
| G3 | Phase 2B「at detection」重綁最新 radar 事件(`service.py:117-124,329-333`) | **FIX_WITH_PHASE2B_REDESIGN**(且為 FIX_BEFORE_FORWARD_OUTCOME 硬條件) | 偵測錨漂移直接毒化 T+N 研究;存活 | 新層寫入 `candidate_first_knowledge_at`,重評估永不改寫 | 是(新層 schema) | **部分**——append-only 的 evaluation/radar 歷史列可重建最早綁定;重建結果標注 RECONSTRUCTED |
| G4 | vendor/local 時間混鍵 `generated_at or capture_timestamp`(`service.py:206,310`;`workspace_v3.py:215`) | **FIX_WITH_PHASE2B_REDESIGN** | §12 要求 vendor 時間不得靜默回退;存活 | 新 schema 兩欄分離 + 顯示標注時間種類 | 是 | 部分——raw payload 尚存者可重解析 |
| G5 | Reprocess 以新 `created_at` 洗新舊 vendor 資料(`service.py:162-220`) | **FIX_WITH_PHASE2B_REDESIGN** | 新鮮度快取語意錯誤;存活 | 快取鍵改用 vendor as-of;reprocess 列顯式標記 | 是 | 可識別(endpoint_statuses 有 PRESERVED_RAW_PAYLOAD 標記) |
| G6 | 瀏覽器本地時區渲染無標示(`scan-dashboard.tsx:152`) | **FIX_WITH_PHASE2B_REDESIGN**(Dashboard IA) | 台北使用者讀到錯位時間;存活 | 固定 ET + 時間種類標注 | 否 | N/A |
| G7 | 本地時鐘日期偽裝市場日;無交易日檢查;雙 DTE 身份(`core/time.py:24`;`v11.py:486`) | **FIX_WITH_PHASE2A_VNEXT** | 影響掃描身份與 DTE bucket;存活 | market_date 加交易日校驗;DTE 註明基準日 | 輕 | 部分——可由 vendor 日期重標 |
| G8 | CONTRACT_PERSISTENCE 無限歷史回溯(`v13.py:284-299`) | **FIX_WITH_PHASE2A_VNEXT**(vNext STEP 3 既定) | 陳年部位持續觸發「今日」候選;存活 | 顯式、可配置、版本化 freshness 規則;**不現在挑 5/7/10/20**(校準後定) | 否 | N/A(觸發語意向前生效) |
| G9 | Persistence 視窗可含比分析日新的快照(前視,`v11.py:414-428`) | **FIX_WITH_PHASE2A_VNEXT**(且 FIX_BEFORE_FORWARD_OUTCOME) | no-lookahead 紅線;存活 | 查詢加 `vendor_oi_date <= 分析日` 上界 | 否 | 歷史分數可判定是否受影響;受影響者標記,不回寫 |
| G10 | 視窗無日曆連續性資訊(`history.py:45`) | **FIX_WITH_PHASE2A_VNEXT** | 「3 視窗」可能橫跨數週而不可見;存活 | 持久化並顯示視窗首末 vendor 日期;**不**發明 gap 門檻(VALIDATE-FIRST) | 輕 | 可回填(觀測列俱在) |
| G11 | 0DTE Score Basis 顯示 BALANCED/0/0(`v13.py:126-137`) | **FIX_WITH_PHASE2A_VNEXT** | 0DTE 仍是 Expiry Activity 校準法;主動錯誤歸因,存活 | 0DTE 專屬 basis 標籤;VS/Neighbor 對 0DTE 存 NULL | 否 | N/A |
| G12 | 0DTE 基準被盤中 first-writer 快照汙染(`v12.py:277-284,351-357`) | **FIX_WITH_DAILY_PIPELINE** | 統計基準完整性;存活 | 快照標記 session 完整度;基準只收 EOD/標準時點 | 輕 | **部分**——現有快照無 session 時點標記者無法權威區分,只能標 SUSPECT,不刪除 |
| G13 | Neighbor Ratio 顯示值≠計分值;comparable 比率未持久化;詞彙表誤植 OI | **FIX_WITH_PHASE2A_VNEXT** | 使用者反推必矛盾;存活 | 持久化 comparable 比率或改名 raw/diagnostic;修詞彙表 | 輕 | 舊列無 comparable 值,保持 NULL |
| G14 | INVALID_CLUSTER 渲染為 CALL/PUT_STRUCTURE(`scans.py:584-593`) | **FIX_WITH_PHASE2A_VNEXT**(Deep Dive 呈現) | vNext 明定 invalid 不得作正面證據;存活 | 顯示端 VALID/STRONG 過濾 | 否 | N/A |
| G15 | STRUCTURE/CLUSTER presence 無門檻 → MULTI_EVIDENCE 膨脹(`state_v2.py:204-217`) | **OBSOLETED_BY_NEW_ARCHITECTURE**(Breadth 已移除)+ 殘餘轉 G14 | 廣度計數消失,但「無效證據不得正面呈現」轉移至 B4 門檻 | 隨新層自然消失 | — | N/A |
| G16 | Phase 2B evaluation 無過濾收前 5 clusters(`service.py:351-356`) | **FIX_WITH_PHASE2B_REDESIGN** | 同 G14 的後端源頭;存活 | 新層只引用 VALID/STRONG | 是 | N/A |
| G17 | STABILIZATION_BIAS 恆真 / DOWNSIDE 無量級(`workspace_v3.py:276-314`) | **FIX_WITH_PHASE2B_REDESIGN**(§E 已裁決 REMOVE as label) | 訊號含量被高估;存活 | 描述性數值取代標籤;任何 BIAS/RISK 字樣 VALIDATE-FIRST | 否 | N/A |
| G18 | 相鄰 expiry 浮點精確等值(`workspace_v3.py:163`);nearest() 缺 strike 距離 0(`domain.py:430-437`) | **FIX_WITH_PHASE2B_REDESIGN** | 資料品質守衛;存活 | tolerance 比對;缺 strike 列排除 | 否 | N/A |
| G19 | 每日收集無排程器(`.github/workflows/` 僅 2 檔) | **FIX_WITH_DAILY_PIPELINE**(vNext STEP 4 既定,最高操作優先) | Persistence/Radar 資料供給繫於手動紀律;存活 | 比照 dealer-gex workflow;供應商時序另行驗證,不盲抄 15:30 | 否 | 缺日=永久缺口,保持 missing |
| G20 | 掃描條無上次掃描/消耗/quota 時齡;Run Scan 不刷新 Radar 未說明 | **FIX_WITH_PHASE2B_REDESIGN**(Dashboard IA 健康列) | 操作信任;存活 | payload 已有欄位,補渲染 + 按鈕行為說明 | 否 | N/A |
| G21 | v1.2 legacy discovery score 仍主導 `/mag7/latest` 部分區塊;靜默回退 v1.2(`scans.py:74-81,99-106,214-216`) | **OBSOLETED_BY_NEW_ARCHITECTURE**(candidate-first payload 重建時整區移除)+ 過渡期顯式標記 legacy | 與「無 universal score」矛盾的洩漏面 | 新 API 不再輸出;過渡期加 legacy 標記 | 是(API 重建) | 歷史 run 保留 |
| G22 | Phase 2B heatmap 呼叫 `format=full` 已死(N1,`service.py:70`) | **NEEDS_READ_ONLY_PROOF → FIX_WITH_PHASE2B_REDESIGN** | 每 ticker 每次 refresh 一次註定失敗的網路嘗試(是否計費未驗證);dealer 脈絡實際 archive-only | 先查 DB endpoint_statuses 證實;新層正式 archive-only | 是 | N/A |
| G23 | Phase 2B 只服務 Radar 觸發合約(N2,`service.py:116-137`) | **FIX_WITH_PHASE2B_REDESIGN** | vNext 候選模型下成為結構缺口;存活且升級 | 新層入口改為 Product Candidate + anomaly 清單 | 是 | N/A |
| G24 | EXPIRY_ONLY 死路;context 擷取 CLI 死路(404 無入口) | **FIX_WITH_PHASE2B_REDESIGN** | Candidate→2B 工作流斷裂;存活 | expiry 級明細視圖;UI 內觸發 context 擷取(帶成本說明) | 是 | N/A |
| G25 | Chain 的 `open_interest_as_of` 解析後丟棄;合約 OI 繼承 expiry 面日期(`parsers.py:401`;`archive.py:264-291`) | **FIX_WITH_DAILY_PIPELINE** | 合約級 vendor 日期是借來的;存活 | 保存合約級 as-of;不一致時標記 | 輕 | 舊列不可考,保持現狀+標記 |
| G26 | Cluster 缺失分項以 0 計(`clusters.py:238-246`);全缺報價可過 hard-reject;隔夜報價驅動流動性分 | **FIX_WITH_PHASE2A_VNEXT**(對齊 NULL 紀律)+ 報價時點標注 | 與全案最強紀律相反;存活 | 缺失即省略;quote as-of 標注;錨點不動(VALIDATE-FIRST) | 否 | 分數不回寫 |
| G27 | 詞彙表 STALE/MISLEADING 條目群;check-glossary 僅驗存在性 | **FIX_WITH_PHASE2B_REDESIGN**(隨新 IA 重建詞彙表) | 單一語意來源含錯;存活 | 清理 + 語意抽查;legacy 條目標注「現行 NULL」 | 否 | N/A |
| G28 | `BACKEND_BASE_URL/INTERNAL_URL` 不一致;POST 掃描無驗證 | **DEFER**(公開部署前必辦清單) | 本機使用可接受 | 統一 env 名;部署清單加驗證 | 否 | N/A |
| G29 | 0DTE `zero_dte_status` 後端完整、前端無面板;READY_PERCENTILE_FALLBACK 30<40 永不入路由未向使用者說明 | **FIX_WITH_PHASE2B_REDESIGN**(呈現)/ 門檻本身 **VALIDATE-FIRST** | 呈現缺口 + 設計後果未揭露;存活 | 渲染既有欄位;fallback 後果寫入說明;40 門檻不動直到有 outcome 證據 | 否 | N/A |
| G30 | Dashboard 以引擎管線而非候選排序;同日 vs 延遲 OI 證據無視覺分層;候選/工作區埋頁底 | **FIX_WITH_PHASE2B_REDESIGN**(§I 全章即其修法) | vNext candidate-first 產品定義的直接呈現面;存活且被 vNext 放大 | candidate-first 首屏 + 時間層徽章(SAME-DAY / OI-CONFIRMED / MULTI-DAY) | 否 | N/A |

**排序原則(非機械複製 Audit P0/P1):** 先擋「每天都在累積不可逆汙染」者(G1、G2),再修「決定未來研究可行性」者(G3、G9,必須在 Forward Outcome 開始前完成),再隨 vNext / Phase 2B / Pipeline 三條實作線各自吸收其餘項目。

---

# H. 目標端到端架構(Target End-to-End Architecture)

```text
                    UNIVERSE(MAG7 → 未來 50–100,configured)
                              ↓
        ┌─────────────────────────────────────────┐
        │ DAILY DATA PIPELINE(排程,vNext STEP 4)│
        │ contract OI archive / Radar / 0DTE EOD  │
        │ Dealer GEX archive(既有,15:30 ET)     │
        └─────────────────────────────────────────┘
                              ↓
        ┌─────────────────────────────────────────┐
        │ PHASE 2A vNext DISCOVERY                │
        │ RADAR_EVENT(contract)                  │
        │ EXPIRY_ACTIVITY(expiry;0DTE 校準法)  │
        │ CONTRACT_PERSISTENCE(confirmation +    │
        │   slow-burn;freshness-bounded)         │
        └─────────────────────────────────────────┘
                              ↓
                  ALL QUALIFYING ANOMALIES(全數保存)
                              ↓
                      GROUP BY TICKER
                              ↓
              PRODUCT CANDIDATE(= ticker,user-facing)
                              ↓
        ┌─────────────────────────────────────────┐
        │ PHASE 2A DEEP DIVE(per anomaly)        │
        │ Structure(含 Neighbor Strike)/ Cluster│
        │ 僅 VALID/STRONG 作正面呈現              │
        └─────────────────────────────────────────┘
                              ↓
        ┌─────────────────────────────────────────┐
        │ PHASE 2B(本報告 Model B;單層 spec)   │
        │ B1 Ticker Price Baseline    [共享]      │
        │ B2 Ticker Volatility Baseline [共享]    │
        │ B3 Dealer/GEX Structure   [archive-only]│
        │ B4 Anomaly Option Detail  [per anomaly] │
        │ B5 Provenance / Time / Quality          │
        └─────────────────────────────────────────┘
                              ↓
              FORWARD OUTCOME(direction-neutral,
              錨定 candidate_first_knowledge_at)
                              ↓
              ACTIONABILITY(empirical;未開始)
                              ↓
              TRADE EXPRESSION(未開始)
```

時間/知識語意橫切全圖(Master Brief §12):每一層寫入時固定七個時間身份;後評估不得改寫先知識;vendor 缺時保持 NULL 並標注,不以本地時間頂替。

---

# I. Dashboard 資訊架構(Information Architecture,非樣式)

## I.1 首屏(candidate-first)

```text
① SYSTEM / DATA HEALTH 列
   後端可達性 · 上次掃描 @時間+消耗 units · 每日收集(OI/Radar)最後成功日
   · Dealer archive 最後 vendor 觀測 · quota + 觀測時齡
   狀態機:DB_OFFLINE / NOT_RUN / FAILED / OK —— 六態互斥顯示(見 I.3)

② TODAY'S PRODUCT CANDIDATES(核心區,首屏可見)
   每 ticker 一張卡:
   NVDA ── Why Found:RADAR ×2 · EXPIRY_ACTIVITY ×1 · PERSISTENCE ×1
           各徽章附時間層:SAME-DAY / OI-CONFIRMED(vendor date)/ MULTI-DAY(視窗首末日)
   MAG7 階段不排名、不湊 12 格:合格幾個顯示幾個(vNext §18)

③ CANDIDATE 展開頁
   Why Found(anomaly 清單,時間層分組)
   → Shared Ticker Context(B1 價格 / B2 IV / B3 GEX)
   → Anomaly Details(B4;contract 可展開,expiry 有專屬視圖 —— 消滅 EXPIRY_ONLY 死路)
   → Deep Dive(Structure/Cluster,VALID-gated)
   → B5 時間/品質/provenance 卡

④ 原始工程表(Radar / Persistence / Activity)
   降級為「支持證據」摺疊區,置於候選之後;保留完整可稽核性
```

## I.2 時間呈現規則

固定 America/New_York 顯示 + UTC tooltip;每個時間值標注種類(event date / vendor observed / first known / evaluated / captured);「事件發生在 T、系統在 T+1 才知道」必須可視(radar 徽章同時顯示 observation_date 與 first_knowledge)。

## I.3 空/錯誤狀態(六態互斥)

DB offline / not run / failed / no qualifying candidate(唯一可說「今日無合格候選」的狀態)/ history immature(顯示 x/y 進度)/ feature unavailable(如 0DTE 基準不足,附解釋)。proxy 不得把後端錯誤轉為 200 空 payload。

## I.4 操作透明

Run Scan 按鈕標注:預估 ~14 付費呼叫、會/不會刷新哪些表(明言 Radar 來自每日收集);Phase 2B context 擷取在 UI 內提供入口並標注成本(4 calls/ticker,Model B)。

---

# J. 實作路線圖(Implementation Roadmap —— 本審查不實作)

依賴順序而非日曆排程;R1/R2 可並行,R4 依賴 R3 的候選模型。

```text
R0  唯讀證明(零付費,先行)
    · G22/N1:查 endpoint_statuses 證實 phase2b dealer_heatmap 400
    · G3:抽樣重建 first-detection 錨,確認可回溯範圍
    · G12:盤點 0DTE 快照可否區分盤中/EOD
    · Phase 2A 審查遺留 T1–T6 驗證查詢(見 project memory)

R1  止血修正(小、獨立於重構,對應 FIX_BEFORE_VNEXT_IMPLEMENTATION)
    · G1 空狀態狀態機 + proxy 真實錯誤
    · G2 停止 radar backfill 就地改寫(重評估改新列/新欄位)

R2  Daily Data Pipeline(vNext STEP 4;FIX_WITH_DAILY_PIPELINE 項目隨行)
    · archive-mag7-daily GitHub workflow(供應商時序獨立驗證)
    · G12 0DTE EOD canonical 快照 + session 完整度標記
    · G25 合約級 open_interest_as_of 保存
    · UI 健康列的資料來源欄位

R3  Phase 2A vNext 實作(候選模型與家族裁決;FIX_WITH_PHASE2A_VNEXT 項目隨行)
    · Candidate = Ticker 分組;移除 Expiry Persistence / Cold Start / Breadth
    · G8 persistence freshness(configurable、versioned、標記 calibration-required)
    · G9 no-lookahead 上界;G10 視窗跨距曝光
    · G11 0DTE basis 修正;G13 neighbor ratio;G14/G26 VALID-gating 與 NULL 對齊

R4  Phase 2B vNext 實作(本報告 Model B;FIX_WITH_PHASE2B_REDESIGN 項目隨行)
    · 單層 evaluation schema:candidate(ticker)級 + anomaly 明細
    · §12 七時間身份欄位;G3 first_knowledge 錨;G4 混鍵分離;G5 快取鍵修正
    · G22 heatmap 呼叫移除(archive-only);G23/G24 全 anomaly 類型覆蓋
    · G17 GEX 標籤降級為描述數值
    · 舊 v1.2/v2.0/v3.1 表只讀保留;新規格 additive 命名,
      工作名沿用「Phase 2B vNext」,正式 spec 號待遷移計畫審查後指配

R5  Dashboard candidate-first 重建(§I;G6/G20/G27/G29 隨行)

R6  MAG7 真實資料累積 → Candidate Forward Outcome 研究
    (前置:G3、G9 已修;沿用 2026-08-15 Forward Outcome Design Gate 文件)
    → 之後才輪到 GEX Evolution 校準(≥10 obs/ticker)與 Actionability
```

**遷移原則:** 全程 additive;不回寫已接受的歷史評估;歷史不可權威修復者(G2 被覆寫的時間戳、G12 無標記快照、G19 缺日)永久標記 UNRESOLVED/SUSPECT/missing,不假造。

---

# K. 明確「還不要動」清單(Do Not Change Yet)

1. **Dealer/GEX 每日封存與 GitHub 排程** —— 正在累積不可回補的歷史,原樣繼續;排程時間(15:30 ET)暫不調整。
2. **全部計分錨點與門檻**(Radar $150k/2,500、persistence/activity/structure/cluster 錨點、65/40 閘、0DTE 70/30、READY_PERCENTILE_FALLBACK 上限)—— 全數維持現值直到 forward-outcome 證據存在;本報告未提出任何新門檻/新權重/新排名。
3. **0DTE same-ticker 20 觀測自基準模型** —— 設計正確;只修基準汙染與呈現。
4. **NULL 紀律 / missing≠zero / UNRESOLVED≠Neutral / 無 BUY-SELL / 無方向推論 / 無 universal score** —— 語意紅線全數不動。
5. **append-only + spec/config version+hash 貫穿各層的版本化紀律** —— 新層照抄此紀律。
6. **REST + server-side key + 同源 proxy + 單一 Supabase 專案** —— 架構不動;不引入 MCP/queue/Redis。
7. **既有歷史資料表與已接受評估**(含 v1.2/v2.0/v3.1 Phase 2B 三層、Expiry Persistence 歷史觀測)—— 只讀保留,不刪除、不回寫(vNext §25 同旨)。
8. **MAG7 宇宙與預算/並行保護**(75 units/scan、advisory lock)—— Universe Expansion 另設 Design Gate。
9. **Phase 3 / Actionability / Trade Expression** —— 不開始;Phase 2B 不預吸收其語意。
10. **oi-change rollover timing 實驗**(0817 部署)—— 獨立研究線,照常進行,不與本重構耦合。

---

# L. 對 Phase 2A vNext 的相容性陳報(單獨列出,非重新設計)

未發現 critical technical incompatibility。三項**整合需求**(vNext 落地時 Phase 2B 側必須同步處理,否則 vNext 候選模型會踩空):

1. **Phase 2B 現行入口只認 Radar 合約(N2/G23)** —— vNext 的 Product Candidate 可能完全由 Expiry Activity / Persistence 構成;Phase 2B 重構必須改為 candidate+anomaly 入口,否則部分候選無脈絡可看。
2. **EXPIRY_ONLY anomaly 需要 expiry 級明細視圖(G24)** —— vNext 保留 expiry 作為 anomaly 實體,Phase 2B 必須能在不假造合約級資料的前提下呈現 expiry anomaly(B4 已設計)。
3. **`trigger_sources` 目前掛在 radar 列與 expiry 列上、且會隨重綁漂移(G3)** —— vNext 的「Why Found」清單需要穩定的 anomaly 身份與 first-knowledge 錨,應在 R3/R4 的 schema 中一併固定。

---

# M. Master Brief §7 十五題逐條回答(索引)

1. **Phase 2B 單句工作?** 見 §C。
2. **哪些元件提供真正獨特資訊?** 價格基線(唯一的 underlying 時序脈絡)、IV Rank + term 節點(唯一的 vol 定價脈絡)、GEX archive 結構(唯一的價格路徑結構脈絡)、strike location(唯一的跨 ticker 可比正規化)。
3. **哪些冗餘/過度複雜?** 三層 spec 堆疊、三次證據重述、Research Readiness 合成等級、恆真 GEX 標籤、Evidence Breadth(vNext 已裁)、Phase 2B 自己的 heatmap 呼叫。
4. **哪些應 ticker 級共享一次?** B1/B2/B3 全部(§D/§F)。
5. **哪些必須留在 anomaly 級?** strike location、contract IV、execution 快照、expiry 錨定的 term/GEX 視圖、Structure/Cluster 引用(§E)。
6. **哪些屬 Deep Dive 而非 Phase 2B?** Structure/Neighbor/Cluster(vNext 既定;Phase 2B 僅 VALID-gated 引用)。
7. **哪些屬 Actionability / Trade Expression?** Gamma/Theta/Vega、liquidity 作為 gate、任何 BIAS/RISK 判定、IV cheap/expensive 分類。
8. **GEX 哪些有用 vs 噪音?** 有用:floor/upper/below 節點數值、adjacent 同 strike 對照、archive 時序。噪音:STABILIZATION_BIAS/DOWNSIDE_ACCELERATION_RISK 現行形式(恆真/無量級)。
9. **Price 最小充分集?** close、1D/5D/20D、SMA20/50、ATR14、trend state(+可選 20 日高低)。
10. **IV 最小充分集?** IV Rank(raw)、candidate/shorter/longer 節點 IV、topology、contract IV(anomaly 級)、implied move(vendor 值,可選)。
11. **Greeks 是核心脈絡還是 Trade Expression 輸入?** 除 Delta(moneyness 脈絡)外皆為 Trade Expression 輸入;繼續封存、移出 Phase 2B 顯示。
12. **Liquidity/execution 是脈絡塊還是 gate?** 兩者,不同抽象層:描述性快照留 B4(標注 as-of);gate 語意屬 Actionability(VALIDATE-FIRST)。
13. **時間戳如何呈現?** §12 七身份 + I.2 規則(ET 顯示、種類標注、SAME-DAY/OI-CONFIRMED/MULTI-DAY 徽章)。
14. **哪些 API 可 ticker 級共享?** ohlc、stock_state、iv_rank、term_structure;dealer surface 改 archive 零呼叫(§F)。
15. **50–100 products 下什麼仍可行?** Phase 2B 本身可行(成本 ∝ 合格候選數);瓶頸在 daily pipeline 與 dealer archive(∝ 宇宙大小),屬 Universe Expansion Design Gate 範圍。

---

# N. 審查合規聲明

- 未修改任何程式碼;未執行任何資料庫寫入;未觸發任何付費 Nightwatch 呼叫(程式碼閱讀使用本機檔案的唯讀 staged 副本)。
- 未重開任何 Founder 已批准的 Phase 2A vNext 決策;§L 為相容性陳報。
- 未發明任何新門檻、新權重、新排名、新綜合分數;所有此類需求標記 VALIDATE-FIRST。
- Audit 作為證據使用,其 P0/P1 標籤已依新架構重新分級(§G),非機械複製。

## 決策提請(供 Founder 裁定)

1. 採納 Model B 五區塊 Phase 2B 架構(§D)為 Phase 2B vNext 規格基線。
2. 批准 §E 元件裁決表(特別是:GEX 兩標籤降級為描述數值、Greeks 移出 Phase 2B 顯示、heatmap 呼叫改 archive-only)。
3. 批准 §G 對賬矩陣的分類與 §J 路線圖順序(R0/R1 可即刻排入,無須等待 vNext 實作)。
4. Phase 2B 正式 spec 版號待 R4 遷移計畫審查後指配;此前沿用工作名「Phase 2B vNext」。

---

*審查方法備註:本報告由三份來源文件(依 Master Brief §2 層級)+ 現行工作樹程式碼唯讀重驗證交叉完成;所有行號以 2026-08-17 staged 副本為準。與同日 Phase 2A 架構審查(project memory 記錄之 Model B 兩階段設計)在術語與裁決上保持一致。本審查未執行任何寫入操作。*
