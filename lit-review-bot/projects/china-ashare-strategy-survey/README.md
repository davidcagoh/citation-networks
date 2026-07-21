# china-ashare-strategy-survey

Manual composable-pipeline experiment (2026-07, candidate replacement for the
LitDiscover engine — see `wiki/litdiscover/` for status): keyword search →
curate/extract (motivation, method, eval, results, limitations) → refine
terms → repeat → forward citation → co-citation, with Zotero as the
reference store.

Research question: What price-only, execution-realistic signal or portfolio
construction improves the competition Score (CAGR/Sharpe/MDD) of a long-only
Chinese A-share strategy, without reintroducing hidden momentum or IC-based
execution-gap failure modes?

Zotero: group library `6619241`, collection "A-Share Strategy Survey"
(`8MPXJM4U`).

## Synthesis (2026-07-21) — inherited from the (ended) Feishu competition, not carried forward as-is

The 26-item Zotero collection's extraction notes were pre-populated by a separate weekly-search
job, run in service of a now-ended Feishu trading competition. That prior effort had its own
codebase (`signals/low_vol.py`, `trend_vol_v4`/`v5`, `regime.py`, `alpha191_046/071`,
`volume_reversal`) and a real dataset (`D001–D484` in-sample, `D485–D726` out-of-sample, 2270
assets, single bear-dominated regime). **Deliberately not reusing that dataset or code** — it's a
narrow, single-regime competition snapshot, not general — but the validated/ruled-out hypotheses
it produced are a real, literature-cross-checked seed list worth re-testing against a fresher,
more general dataset before this survey does any fresh keyword searching of its own.

### Ruled out
- **Price-only intermediate-horizon momentum (3/6/12-month).** "Dissecting Momentum in China"
  (Liu, Tan, Xu, Yuan, Zhu 2025) found classic momentum is absent in China — high past-news-day
  returns are offset by non-news-day reversal (retail-driven "tug-of-war"), net momentum ≈ 0.22%/mo,
  t=0.40. Structural, not a data artifact — don't re-test plain momentum on new data.
- **Raw IC as sufficient portfolio-performance proxy.** The prior effort's own empirical finding
  (IC=+0.034 → CAGR=−54%) is independently confirmed by "Do Better Volatility Forecasts Lead to
  Better Portfolios?" (Wade 2026): even rank-correlation of the forecast target still fails to
  predict portfolio Sharpe, because portfolio construction method (min-variance vs. inverse-vol vs.
  long-short) determines whether a better forecast helps at all. This is the RQ's "IC-based
  execution-gap failure mode" directly evidenced twice, independently.

### Validated / carry-forward candidates
Carry forward the *signal theses* below, not the prior effort's *tuned parameter values* — each
thesis is independently evidenced on its own paper's sample, mostly multi-regime (Blitz/Hanauer/
van Vliet ~2004–2020; Wang & Li 2000–2022 spanning the 2007 boom/2015 crash/COVID; Gu/Hu/Xiong
2007–2020; the SHAP/turnover study 2009–2019), not on the competition's narrow bear-dominated
window. It's the *parameters* built on top of these theses (window lengths, stock counts,
thresholds — see the methodological flag below) that are bear-window-specific, not the underlying
claims.
- **Low-volatility / idiosyncratic-volatility anomaly** — the core signal family. Blitz, Hanauer &
  van Vliet (2021) document it as structural (retail overpricing of high-vol "lottery" stocks),
  not a backtest artifact; low turnover, concentrated in liquid names. Prior effort's `low_vol.py`
  alone: CAGR=+9.32%, SR=0.85, beating all IC-based signals.
- **Regime-conditioning on top of low-vol** ("Volatility-Managed Portfolios in the Chinese Equity
  Market," Wang & Li) — a price-data-only switch scaling exposure down in low-vol bear periods,
  up/momentum-tilted in low-vol bull periods. Addresses low-vol's one real weakness (bull-market
  underperformance) without reintroducing plain momentum.
- **Overnight-specific MAX/lottery filter.** Gu, Hu & Xiong (2025): the lottery anomaly is
  entirely an overnight-return phenomenon (T+1-constrained retail demand), not intraday — directly
  execution-relevant if buying at a morning-auction VWAP, more precise than a total-daily-return
  MAX filter.
- **Turnover as the dominant behavioral signal**, not valuation (Han/Xiao/Zhang/Zheng SHAP study:
  58.2% of predictive attribution vs. 10.7% for valuation) — supports filtering by turnover/
  behavioral crowding over fundamentals-based screens.
- **Robust/heavy-tail-aware covariance & position sizing**: MAD-based vol ranking under China's
  price-limit-induced fat tails (Fonseca 2026 decision-geometry result), ARFIMA-FIGARCH adaptive
  covariance windows (Jha/Shirvani/Jaffri/Rachev/Fabozzi 2025) for faster bear-regime response,
  conformal regime-weighted VaR for smoother MDD control (Schmitt 2026) — all portfolio-construction
  refinements on top of the low-vol core, not new signals.
- **Clustering-constrained stock selection** (Jiao & Zheng): explicitly targets the concentration
  risk in a low-vol N=20 book (prior effort's own selected stocks had mean pairwise r=0.33, ~7
  effective bets) — real diversification improvement, not cosmetic.

### Open methodological flag (from the eval survey, see `trading-eval-survey/`)
This flag is about the prior effort's *own parameter tuning*, not the literature theses above.
Its parameter choices (60d vol window, N=20/30 stock count, −0.025 trend threshold, regime-detector
cutoffs) were calibrated informally against the single bear-dominated IS window (`D001–D484`) —
several notes explicitly flag awareness of this ("parameter space exhausted... do not test on IS
data" for one signal). **This calibration was never run through PBO/DSR-style overfitting
correction** (see `trading-eval-survey/`'s notes on Bailey et al.'s CSCV and Deflated Sharpe Ratio).
When this survey re-tests the signal theses above against a fresh dataset, treat every parameter
choice as needing to be re-tuned and re-validated from scratch — none of the old parameter values
transfer, even though the underlying signal concepts do.
