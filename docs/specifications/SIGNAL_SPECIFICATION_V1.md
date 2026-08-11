# Signal Specification V1 — Phase 2A

Version: `signal_spec_v1.0_phase2a`

Phase 2A answers **where unusual MAG7 option positioning is occurring today**. It describes Call/Put activity structure symmetrically. It does not infer investor direction, produce BUY/SELL, or calculate Tradeability, GEX, IV, price, catalyst, unwind, roll, or machine-learning signals.

## Universe and tenor

The versioned fixed universe is AAPL, MSFT, NVDA, AMZN, META, GOOGL, and TSLA. Calendar DTE uses the `America/New_York` market date. Buckets are VERY_SHORT 0–7, SHORT 8–30, MEDIUM 31–90, and LONG 91–180. LONG is aggregate-only; deep contract analysis stops at 90 DTE. `dte_at_detection` and `bucket_at_detection` are immutable. `current_dte` and `current_bucket` are presentation state. DTE 0 adds `ZERO_DTE`.

## Preliminary expiry features and score

Within 0–180 DTE the scanner preserves Call/Put volume and OI and calculates:

- `volume_share = expiry volume / ticker 0–180 DTE volume`;
- `oi_share = expiry OI / ticker 0–180 DTE OI`;
- `volume_skew = (call volume - put volume) / total volume`;
- `oi_skew = (call OI - put OI) / total OI`;
- `neighbor_ratio = expiry OI / median comparable-expiry OI`.

Zero denominators yield unavailable values. Vendor expiry type wins; otherwise third-Friday is recorded as inferred `STANDARD_MONTHLY` and all others as inferred `OTHER`. Insufficient comparable neighbors produce null and `INSUFFICIENT`.

The preliminary score is normalized over available components: volume share (max 40; 10/20/30/40/50% → 0/10/20/30/40), neighbor ratio (max 30; 1.2/1.5/2/3/5x → 0/5/10/20/30), and absolute volume skew (max 30; .10/.30/.50/.70 → 0/10/20/30). Eligibility begins at 40. Ticker score is the highest eligible 0–90 DTE expiry. At most four tickers and one qualifying expiry per VERY_SHORT/SHORT/MEDIUM bucket are selected (three per ticker).

## Contract eligibility and score

Invalid required identity, DTE above 90, unusable supplied quote, or spread above 50% of mid is a hard rejection. Missing bid/ask is not fabricated and makes liquidity unavailable. There is no minimum OI filter. `LOW_OI_BASE` marks previous OI below 100. `volume_oi_ratio = volume / max(previous_oi, 1)` and never proves opening activity.

Estimated premium is `volume × 100 × price proxy`; proxy order is intraday VWAP, suitable vendor aggregate, last, then valid midpoint. Its method is persisted and the result remains an estimate.

Contract score is `earned available points / available maximum points × 100`:

- relative activity max 20: Volume/OI max 12 at .5/1/2/5/10x → 0/4/7/10/12; volume max 8 at 100/500/2,000/10,000 → 0/3/5/8;
- premium max 20 at $0/$50k/$150k/$500k/$1m/$5m → 0/2/6/10/14/20;
- historical max 20: robust Z at 1/2/3/4/5 → 0/5/10/15/20, available only with at least 10 observations, otherwise `HISTORY_INSUFFICIENT`;
- intraday burst max 15 at 2/3/5/10x → 0/5/10/15;
- liquidity max 15 at spread 5/10/20/30/50% → 15/13/10/6/2;
- moneyness max 10 by abs(delta): 0–.10=2, .10–.20=5, .20–.35=8, .35–.65=10, .65–.80=8, .80–.90=5, .90–1=4. Below .10 adds `LOTTO_RISK`.

Classification is IGNORE below 50, OBSERVE 50–64, CANDIDATE 65–74, STRONG 75–84, EXTREME 85+. A `CONTRACT_CANDIDATE` additionally requires score at least 65 and basis at least 60. Intraday drilldown is capped at 12 contracts per scan and rescoring follows the same formula.

## Final expiry score

The normalized components are OI share max 25 (5/10/20/30/40/50% → 0/5/10/15/20/25), neighbor max 25 (1.2/1.5/2/3/5x → 0/5/10/15/25), volume share max 20 (5/10/20/30/40/50% → 0/4/8/12/16/20), strongest absolute OI/volume/premium skew max 15 (.10/.30/.50/.70 → 0/5/10/15), and premium share max 15 (5/10/20/30/40/50% → 0/3/6/9/12/15). Missing optional evidence is unavailable and the score is rescaled. At least 65 is `EXPIRY_CANDIDATE`; at least 80 is `STRONG_EXPIRY_CANDIDATE`.

## Strike clusters and summaries

A cluster contains at least two candidates with the same ticker, expiry, and right. The complete same-side strike ladder is used; adjacent candidates can bridge one non-candidate listed strike, and an available-spot moneyness span cannot exceed 20%. Calls and Puts never merge.

Cluster score normalizes contract strength max 25, same-side premium share max 25 (10/20/40/60% → 0/5/15/25), volume share max 20 (10/20/40/60% → 0/5/12/20), strike coherence max 20 (2/3/4+ → 10/15/20, minus 5 for a one-strike gap), and liquidity max 10. Score at least 65 is `VALID_CLUSTER`; at least 80 is `STRONG_CLUSTER`. Shapes are TIGHT_CLUSTER at no more than 7.5% moneyness span, BROAD_CLUSTER up to 20%, or LADDER for at least three strikes with monotonic premium/volume progression across at least 75% of adjacent pairs. Premium-weighted strike is a positioning center, never a target.

Bucket summaries may say `CALL_DOMINANT`, `PUT_DOMINANT`, `TWO_SIDED`, or `NO_STRONG_STRUCTURE`. An expiry candidate with a valid cluster and no hard rejection may be `PROVISIONAL_POSITIONING_CANDIDATE`. OI state is limited to `PENDING`, `CONFIRMED`, `NOT_CONFIRMED`, and `INCONCLUSIVE`. None is a trade recommendation.
