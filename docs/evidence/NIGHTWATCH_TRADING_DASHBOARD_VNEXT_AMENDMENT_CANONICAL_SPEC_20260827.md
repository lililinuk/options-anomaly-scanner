# Nightwatch Trading Dashboard vNext Amendment — Canonical Specification

**Specification date:** 2026-08-27

**Status:** FOUNDER_APPROVED_CANONICAL

**Scope:** Authoritative specification for the later Trading Dashboard vNext implementation package

**Implementation status:** NOT IMPLEMENTED BY THIS AMENDMENT

## 1. Authority and purpose

This Founder-approved amendment is the authoritative implementation specification for Trading Dashboard vNext. It freezes the product and semantic decisions below and establishes a strict boundary between current trading decision support, immutable first-knowledge research evidence, and the future Stage 9 Research Workspace.

This amendment changes presentation and context semantics only. It does not authorize application, test, workflow, schedule, configuration, database, migration, collection, scoring, qualification, or research-computation changes.

Normative terms such as **must**, **must not**, **may**, and **should** define implementation requirements. If an earlier dashboard presentation conflicts with this amendment, this amendment governs the Trading Dashboard vNext implementation. Historical evidence and no-lookahead safeguards remain authoritative and must be preserved.

## 2. Canonical context boundary

### 2.1 Trading Dashboard / Current Trading Context

The Trading Dashboard is the current decision-support view for what is relevant now. It must prioritize the latest eligible information and present a coherent, refreshable **Current Trading Context**.

Current Trading Context may contain:

- current/reference stock price;
- current/latest IV Rank;
- relevant active-expiry IV;
- current term-structure shape;
- latest eligible persisted Dealer/GEX archive;
- active anomalies;
- active expiries; and
- execution/liquidity context where already available.

All current-context blocks must expose truthful as-of and freshness information. Refreshing Current Trading Context must never mutate the Frozen First-Knowledge Baseline.

### 2.2 Frozen First-Knowledge Baseline

The Frozen First-Knowledge Baseline is immutable historical context representing what was knowable when a Candidate first became known. It must never be overwritten, reinterpreted as current, or refreshed with later market data.

It exists for:

- no-lookahead research;
- historical reconstruction;
- Stage 9 Forward Outcome;
- audit and provenance.

### 2.3 Future Stage 9 Research Workspace

Stage 9 is not implemented by this amendment. Future Stage 9 will contain:

- the Frozen First-Knowledge Baseline;
- historical trigger evidence;
- expired contracts and expiries;
- historical Price, IV, and GEX;
- complete timestamps and provenance;
- Forward Outcome;
- T+1, T+3, and T+5;
- future MFE/MAE research; and
- cohort and research analysis.

The Trading Dashboard must not mix these historical research semantics with current trading semantics. Historical or audit affordances such as expired-trigger toggles do not belong inside the Trading Dashboard.

## 3. Trading Dashboard candidate population

The Trading Dashboard homepage must represent the **latest successful Candidate population**.

Historical persisted Candidates must not be labelled **Today's Candidates** unless they actually belong to the current/latest successful trading-date population. The UI must expose:

- Candidate population market date;
- scan/run freshness; and
- CURRENT, STALE, or UNAVAILABLE state where relevant.

The population identity and freshness must remain visible enough that a successful historical population cannot be mistaken for today's population. Historical Candidate populations remain preserved for Stage 9.

## 4. Active-anomaly semantics

The Trading Dashboard must display and count **ACTIVE anomalies only**. **Active Anomalies** must not mean the lifetime persisted trigger count.

Active or expired state must be derived from the relevant contract expiry and trading/session date. It must not use a hard-coded calendar boundary such as `> 2026-08-26`, and it must not use the host timezone as market truth. An expiry remains active while it is legitimately tradeable during its expiry session and becomes expired afterward. US market-session/date logic must use `America/New_York`; persisted timestamps remain UTC.

Expired contracts and expiries must not appear anywhere in the Trading Dashboard. They remain preserved for Stage 9 Research.

## 5. Candidate Cards

Candidate Cards must be compact. They must replace repeated persisted-trigger chip walls, including repeated labels such as `OI-CONFIRMED Radar`, with concise counts by accepted anomaly family.

Illustrative presentation:

```text
NVDA
8 ACTIVE ANOMALIES
Radar                  5
Expiry Activity        2
Contract Persistence   1
```

The homepage card must not display every persisted trigger. It should let the user answer quickly:

- Why is this ticker relevant now?
- How many active anomalies are present?
- Which accepted anomaly families are represented?
- Which few anomalies deserve inspection first?
- How fresh is the current context?

Counts must be computed from active anomalies in the displayed Candidate population, not from lifetime or historical persisted evidence.

## 6. Featured Active Anomalies

Each Candidate may show at most one **Featured Active Anomaly** per accepted anomaly family and at most three Featured anomalies in total.

**Featured** means the highest-priority active evidence within that family. It means **priority to inspect**. It does not mean bullish, bearish, BUY, SELL, strongest trade, or strongest evidence across all families.

Family selection rules are:

- **Radar:** use the existing accepted deterministic Radar ordering. Do not create a synthetic Radar score for presentation.
- **Expiry Activity:** use the accepted native Same-Day Activity Score.
- **Contract Persistence:** use an existing accepted native ranking or strength only if one already exists. If none exists, do not invent one. The later implementation must use a deterministic, non-scoring presentation fallback that does not imply comparative strength, or omit the family Feature until an accepted native rule exists.

No cross-family universal score may be invented. Visual highlighting is permitted only when its semantics are clearly **priority to inspect**, never direction or recommendation.

## 7. Why Found

The existing large persisted-trigger dump must be replaced with a compact active-evidence summary followed by Featured Active Anomalies.

Illustrative presentation:

```text
WHY FOUND
8 active anomalies
Radar                  5
Expiry Activity        2
Contract Persistence   1
```

Complete historical trigger evidence belongs in Stage 9 Research/Audit and must not be reproduced as a homepage wall.

## 8. Global Current Trading Context contract

Current Trading Context is refreshable and semantically distinct from the immutable Frozen First-Knowledge Baseline. Every B1/B2/B3/B4 block must consume a coherent current-context identity and disclose its own source as-of and freshness state.

The later implementation must use persisted or cached data wherever possible. It must not trigger paid Nightwatch calls on page load, fabricate current data, silently substitute historical data for current data, or mutate preserved first-knowledge evidence.

### 8.1 B1 — Current Trading Price

The Trading Dashboard must use one authoritative **Current Trading Price Context** across B1, B2, B3, and B4 whenever computing or displaying current relative relationships.

The preferred source, when trustworthy and sufficiently fresh under accepted configuration, is:

```text
stock_state.current_price_usd
```

Associated metadata must include:

- `as_of`;
- session; and
- freshness.

If trustworthy current stock state is unavailable or stale, the fallback is the latest canonical completed regular-session close. The UI must label the actual semantic identity truthfully, using labels such as **Current Price**, **Latest Vendor Price**, **Previous Close**, **Reference Price**, **As of**, and **Session** only where they accurately describe the selected value.

A historical source-specific value must not be labelled current. Old Stock State, Frozen Canonical Close, GEX snapshot spot, and chain snapshot spot remain preserved source evidence but must not become the Trading Dashboard's primary current price merely because they are available.

### 8.2 B2 — Volatility

The Trading View must prioritize:

- latest/current IV Rank;
- IV Rank as-of;
- IV freshness;
- relevant active-expiry IV; and
- compact term-structure shape.

IV must be displayed naturally as a percentage where appropriate, for example `33.1%` rather than `0.331`.

The default Trading View must not render a large wall of every expiry or term node. Detailed term structure belongs in an expandable/detail view or Stage 9 Research.

The implementation must not invent LOW/MID/HIGH or similar IV Rank classifications while vendor semantics remain unapproved. IV Rank must not alter Candidate qualification or scoring unless separately authorized.

Current price-relative volatility relationships must use the same Current Trading Price Context selected by B1.

### 8.3 B3 — Dealer / GEX

The Trading View must use the **latest eligible persisted Dealer/GEX archive**, not the Frozen First-Knowledge GEX snapshot.

It must:

- display GEX as-of clearly;
- display freshness clearly;
- never imply that AVAILABLE means CURRENT;
- label stale GEX as STALE;
- show active/unexpired expiries only by default and provide no expired-expiry Trading View;
- use the global Current Trading Price Context for trading-relative presentation;
- preserve vendor `spot_usd` as historical source metadata;
- never present vendor GEX snapshot spot as today's/current stock price;
- rename raw net GEX to **Net GEX**;
- display main-view GEX approximately in integer USD millions, for example `+$32M` or `-$8M`;
- preserve actual strike precision, including strikes such as `212.5`;
- permit positive and negative GEX to be visually differentiated; and
- state explicitly that GEX sign is not equivalent to bullish/bearish direction.

Exact raw GEX values remain preserved and available for Research/Audit.

### 8.4 B4 — Active Trigger Details

B4 contains **ACTIVE trigger details only**. It must not contain **Show expired**, **Historical triggers**, **Archived triggers**, or equivalent historical affordances. Those belong to Stage 9.

The user may select any combination of ACTIVE anomaly families for display, such as:

```text
[x] Radar
[x] Expiry Activity
[ ] Contract Persistence
```

An optional **Featured only** control is permitted.

The contract-level Trading View should prioritize:

- contract identity;
- expiry and DTE;
- Call/Put;
- strike;
- delta OI;
- premium;
- IV;
- delta;
- bid/ask; and
- spread.

Large provenance and timestamp blocks must not be repeated on every Trading card. `source_first_received`, `vendor_observed`, `local_captured`, `trigger_first_known`, configuration/version/hash, and complete raw provenance remain preserved for Stage 9 Research/Audit.

All price-relative fields in B4 must use the same Current Trading Price Context selected by B1. Immutable DTE and bucket values captured at detection must remain preserved; a current Trading View must not overwrite those historical fields with dynamic state.

## 9. Freshness semantics

The Trading Dashboard must consistently distinguish at least:

- **CURRENT:** the persisted context satisfies its accepted source-, session-, and dataset-specific freshness rule;
- **STALE:** data exists but does not satisfy that accepted freshness rule; and
- **UNAVAILABLE:** no eligible persisted/cached data exists for the block.

AVAILABLE is not a synonym for CURRENT. This contract applies especially to:

- Candidate population;
- Price;
- IV;
- Dealer/GEX; and
- current-context supporting datasets.

Each current-context block must disclose enough source identity, as-of, session where applicable, and freshness information to prevent mismatched historical inputs from appearing jointly healthy/current. For example, Price from August 25, IV from August 12, and GEX from August 19 must not all be presented as current without each independently satisfying its accepted freshness rule.

This amendment does not invent freshness durations. Dataset-specific freshness thresholds belong in validated configuration or already accepted domain rules and must be traceable. When persisted evidence cannot establish CURRENT, the UI must present STALE or UNAVAILABLE rather than fabricate confidence.

## 10. Historical data preservation and no-lookahead integrity

This amendment must not delete, rewrite, or collapse historical evidence. Preserve for Stage 9:

- Frozen First-Knowledge Baseline;
- all persisted triggers;
- expired contracts;
- expired expiries;
- historical Price;
- historical IV;
- historical term structure;
- historical Dealer/GEX;
- all source, vendor, and local timestamps; and
- configuration, version, and hash provenance.

Current-context refreshes must write only to their authorized current/persisted archive path and must never backfill or mutate frozen first-knowledge records. Financial logic must remain traceable, documented, and reproducible from preserved raw source evidence.

## 11. Explicit non-goals and prohibited semantics

This Canonical Specification does not authorize implementation changes to:

- Candidate eligibility;
- Candidate scoring;
- Radar qualification thresholds;
- Expiry Activity scoring;
- Contract Persistence scoring;
- OI thresholds;
- ticker universe;
- API frequency;
- Phase2A collection;
- Dealer/GEX collection schedule;
- Phase2B;
- Stage 8;
- Stage 9 implementation;
- Forward Outcome; or
- MFE/MAE.

No BUY/SELL recommendation semantics, bullish/bearish inference, trade-strength claim, synthetic family score, or cross-family universal score may be introduced.

## 12. Constraints for the later implementation package

The later Trading Dashboard vNext implementation package must:

- use persisted/cached data wherever possible;
- not trigger paid Nightwatch calls on page load;
- not fabricate current data;
- display STALE or UNAVAILABLE when persisted current data is insufficient;
- preserve every no-lookahead safeguard;
- keep the Frozen First-Knowledge Baseline immutable;
- separate Trading and Research semantics;
- avoid migrations unless genuinely necessary;
- preserve transport, ingestion, normalized models, analytics, persistence, and API route separation;
- use UTC for persisted timestamps and `America/New_York` for US market-session/date logic;
- keep the Nightwatch API key server-side and out of frontend code and `NEXT_PUBLIC_*` variables;
- use fixtures/mocks rather than live Nightwatch calls in automated tests; and
- include focused regression tests.

No implementation detail may invent a financial formula, anomaly threshold, score weight, classification, or freshness threshold. Such rules require accepted, validated configuration or separate authorization.

## 13. Later implementation acceptance contract

The later implementation is conformant only if all of the following are true:

1. The homepage identifies the latest successful Candidate population and exposes its market date and freshness.
2. Candidate Cards and Why Found count active anomalies by accepted family without dumping persisted trigger history.
3. No expired contract, expiry, trigger, or historical-data toggle appears in the Trading Dashboard.
4. Each accepted family contributes at most one Featured Active Anomaly and the page shows at most three total.
5. Featured selection uses only accepted family-native ordering/ranking and does not imply direction or recommendation.
6. B1/B2/B3/B4 use one Current Trading Price Context for current relative relationships.
7. Price, IV, GEX, Candidate population, and supporting current-context blocks independently disclose truthful as-of/freshness state.
8. B3 uses the latest eligible persisted Dealer/GEX archive, retains strike precision, presents approximate main-view USD millions, and does not treat vendor spot as current stock price.
9. B4 supports selectable active families and contains active trigger details only.
10. Frozen First-Knowledge and all historical/audit evidence remain immutable and preserved for Stage 9.
11. Page load makes no paid Nightwatch request.
12. Focused regression tests prove the boundary between current Trading semantics and frozen/historical Research semantics.

## 14. Documentation-only safety boundary for this amendment

This amendment freezes the specification only. It does not implement the Trading Dashboard or Stage 9.

```text
APPLICATION_CODE_CHANGES=0
TEST_CODE_CHANGES=0
NIGHTWATCH_REQUESTS=0
PAID_UNITS=0
REMOTE_DB_WRITES=0
REMOTE_SCHEMA_WRITES=0
MIGRATIONS=0
MANUAL_GITHUB_WORKFLOW_RUNS=0
TRADING_DASHBOARD_IMPLEMENTED=NO
STAGE9_IMPLEMENTED=NO
FORWARD_OUTCOME_COMPUTED=0
```

Backend application files, frontend application files, tests, workflows, configuration, and schedules are outside this documentation-only change. The accepted Phase2A runtime code must remain byte-identical; only this canonical Markdown specification is added.

## 15. Canonical status

```text
TRADING_DASHBOARD_VNEXT_CANONICAL_SPEC_STATUS=FOUNDER_APPROVED_CANONICAL
AUTHORITATIVE_IMPLEMENTATION_BOUNDARY=TRADING_CURRENT_CONTEXT_VS_FROZEN_FIRST_KNOWLEDGE_VS_STAGE9_RESEARCH
NEXT_STEP=WAIT_FOR_PHASE2A_NATURAL_RUNTIME_THEN_IMPLEMENT_TRADING_DASHBOARD_VNEXT
```
