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
- **Price-only intermediate-horizon (weekly/monthly, 3/6/12-month) momentum only** — scope this
  precisely. "Dissecting Momentum in China" (Liu, Tan, Xu, Yuan, Zhu 2025) found classic
  intermediate-horizon momentum is absent — high past-news-day returns are offset by non-news-day
  reversal (retail-driven "tug-of-war"), net momentum ≈ 0.22%/mo, t=0.40. Structural, not a data
  artifact — don't re-test plain intermediate-horizon momentum on new data. **This does NOT rule
  out daily-horizon momentum** — see "Daily momentum (distinct from ruled-out momentum)" below,
  found in a broader thrust-search pass and easy to miss if "momentum" is treated as one bucket.
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

### Second pass (2026-07-21) — broad thrust re-search, not just gap-filling

The first curation pass ran gap-directed searches (execution/VWAP mechanics, turnover+low-vol
combos) and came up empty on those specific gaps. Re-running broad searches on the RQ's actual
core thrust (not just its edges) surfaced real misses the original weekly job's own search terms
apparently didn't catch:

- **Daily momentum (distinct from ruled-out momentum).** "Daily Momentum and New Investors in
  Emerging Stock Markets" (Gao, Jiang, W.A. Xiong, W. Xiong 2025): medium-term momentum is absent
  (confirms the ruled-out finding above), but a *daily* momentum exists — continues 1 day, reverses
  within a week — driven specifically by new/inexperienced-investor attention-chasing (directly
  evidenced via account-level trading data, not inferred). Asymmetric: stronger in bull markets.
  A systematic emerging-market phenomenon (14/21 emerging markets vs. 3/21 developed), not
  China-specific, which strengthens the causal story. **Open risk, not yet resolved:** this is the
  shortest-horizon signal in the collection — whether it survives next-day execution lag and
  realistic costs, given the effect itself reverses within days, is unaddressed by what's been read
  so far. Must be checked against the overnight-MAX and turnover-crowding candidates above for
  double-counting — plausibly the same underlying retail-attention mechanism seen from three angles.
- **Direct, quantified evidence for the RQ's "IC-based execution-gap" mechanism.** "Machine Learning
  Enhanced Multi-Factor Quantitative Trading... with Bias Correction" (Du 2025/2026, arXiv:2507.07107)
  — initially mis-triaged out of this collection as "general ML," re-added on discovery. Documents
  "upstream contamination": rolling-window factor pipelines that ingest non-executable
  limit-up/limit-down closing prices before row-filtering inflate apparent IC by 18% while cutting
  realised Sharpe by 0.44 points — a "phantom alpha" from mechanically-inflated but untradeable
  limit-move returns. Fixed via a "mask-first" design threading a Boolean tradability mask through
  every rolling-window operator. **This is the single strongest piece of evidence in the collection
  for the RQ's execution-gap concern** — it's quantified, root-caused, and the paper applies its own
  DSR check (0.978 real / 0.994 synthetic, correcting for ~50 configurations explored). Directly
  actionable: the same masking fix applies to the prior effort's own `low_vol.py` rolling-std
  computation (limit-move days currently included in the vol window, biasing rankings) — concrete
  fix given in the paper's own note.
- **Weak-evidence candidate, not to overweight**: "Sharpe-Driven Stock Selection and
  Liquidity-Constrained Portfolio Optimization" (Nguyen 2025, arXiv:2511.13251) — price/volume-only,
  on-thrust (25% CAGR/1.71 Sharpe/8.2% MDD vs. 21%/1.62/7.6% benchmark), but no train/test split
  described, no overfitting correction, no significance test, single author. Exactly the kind of
  result the eval survey's own papers (PBO, DSR) warn is unreliable without a trial-count-adjusted
  check — keep as a weak data point, not a validated candidate.

### Third pass (2026-07-21) — forward citation from seminal/central papers, not the newest ones

A third keyword-search round showed dropping yield (mostly repeats/corroboration) — see git
history for that assessment. Switched to forward citation instead, deliberately targeting
**older, central papers likely to have an accumulated citation trail**, not the newest preprints
(a 2026 paper has had no time to be cited yet, regardless of relevance). Used the Semantic
Scholar API directly rather than generic web search. High yield — stronger hit rate than the
third keyword round:

- **"Luck 'duels' among factors in China" (Wang/Shi/Wan/Wang 2026)**, citing Blitz et al. — a
  rigorous multiple-testing framework (bootstrap panel regression) applied directly to 169
  candidate A-share factors (139 characteristics + 30 PCA-derived). Only a few survive genuine
  incremental explanatory power (IPC9 = retail noise-trader-risk proxy, RPPC1 = flight-to-quality,
  CAPEX/debt-growth/earnings-consistency characteristics) — and even those are confined to
  specific market segments accessible to arbitrage capital. This is the eval-methodology rigor
  this survey's own candidates should eventually be checked against, applied natively to China.
- **"Conditional Multifactor Volatility-Managed Portfolios" (Yang/Liu/Chen 2025)**, citing Blitz et
  al. — extends the regime-conditioning thesis (Wang & Li) to 41 countries; finds performance
  improves further when conditioning on **US market volatility jointly with domestic**, not
  domestic alone. Directly testable against the prior effort's `regime.py` (currently
  domestic-only) — though adopting it means deliberately breaking the "price-only, single-market"
  framing, not an oversight if done.
- **"Calm Stocks, Wild Hopes" (Su 2025, NYU Shanghai honors thesis — not peer-reviewed, weight
  accordingly)**, citing Gu/Hu/Xiong — directly synthesizes two of this survey's core threads:
  low-vol anomaly is *amplified* by lottery preference but not fully explained by it (both remain
  significant after controlling for MAX/skewness/kurtosis). Concrete refinements: use predictive
  IVOL, not contemporaneous Beta or naive same-period IVOL (the latter is mechanically inflated by
  extreme events unless double-sorted); the anomaly is stronger in equal-weighted/small-cap-
  inclusive portfolios than the large-cap-only universe Blitz et al. studied; and — cutting against
  general factor-decay concerns raised elsewhere in this survey — the IVOL anomaly has
  *strengthened*, not decayed, over its 1995–2024 sample.
- **"Lottery Preference and Skewness Risk Premium" (Zhou/Roh/Xu 2025)**, citing the lottery
  anomaly paper — decomposing total implied skewness into upper/lower components resolves a null
  result: upper (lottery-driven) carries a significant *negative* price, lower is weakly positive,
  and they cancel in the aggregate. Methodological lesson directly transferable to this survey's
  own skewness/lottery-based candidates: **decompose, don't aggregate** higher-moment measures, or
  risk averaging away a real, sign-asymmetric effect.

Lower priority (found via the same forward-citation pass, not pursued further): China elderly
household long-term-care asset allocation, Sina Weibo COVID-sentiment sensitivity, IPO-sentiment
lottery demand, oil-futures lottery gambling — all tangential to this RQ.

### Fourth pass (2026-07-21) — co-citation, via a well-connected paper's own reference neighborhood

True co-citation (Blitz et al.'s citers' shared reference overlaps) wasn't computable — the one
paper whose reference list would've been richest ("Luck 'duels' among factors in China") has its
references elided by the publisher. Fell back to mining the neighborhood of a broad, well-cited
(52 citations) survey paper instead, same underlying goal. High yield — the best round yet for
methodological rigor specifically:

- **"Anomalies in the China A-share market" (Jansen/Swinkels/Zhou 2021)** — tests 32 known
  anomalies against 20 years of A-share data and, uniquely in this collection, computes
  **break-even transaction costs per anomaly**. Value/low-vol are low-turnover and cost-robust
  (book-to-market tolerates 1.47% costs at a 1-month hold). Short-horizon effects — short-term
  vol, short-term/residual reversal, seasonal, abnormal turnover — have break-even costs as low as
  **0.12%**. This is the single most important execution-realism data point in the collection:
  it means this survey's several short-horizon candidates (daily momentum, last-hour momentum,
  overnight-MAX, day-night institutional timing) are structurally the same kind of high-turnover
  effect this paper shows gets wiped out by realistic costs — none of them can be trusted as
  "execution-realistic" without the equivalent break-even-cost check run on fresh data.
- **"More Powerful Tests for Anomalies in the China A-Share Market" (Jansen/Swinkels/Zhou 2023)**
  — China's short usable sample leaves *conventional* single-characteristic portfolio sorts
  statistically underpowered; an efficient sorting procedure (characteristics + covariance matrix)
  roughly doubles t-statistics, turning 3 significant anomalies into 9 on the same data.
  Reassuringly, efficient-sorting and equal-weighted portfolios correlate highly — same anomaly,
  better-powered test, not a different phenomenon. Actionable: before downweighting any borderline
  candidate in this survey as "too weak," try this power upgrade first.
- **"Replicating and Digesting Anomalies in the Chinese A-Share Market" (Li/Liu/Liu/Wei 2023/2024,
  Management Science, 34 citations)** — replicates 469 anomaly variables under mainboard-only
  breakpoints + value-weighted returns: **83.37% show no significant spread**, rising to 84-87%
  after risk adjustment. Directly argues the field's *conventional* procedure — all-A-share
  breakpoints with equal-weighted returns — overweights microcaps far beyond real investable
  capacity, inflating apparent significance. **This sits in real tension with "Calm Stocks, Wild
  Hopes"'s finding that equal-weighted portfolios show a stronger low-vol/IVOL anomaly than
  value-weighted** — reconciled by "More Powerful Tests" above: the *breakpoint choice*
  (mainboard-only vs. all-share), not the weighting scheme itself, is what drives the inflation.
  Actionable: re-check this survey's low-vol/lottery candidates against mainboard-only breakpoints
  before trusting any equal-weighted result at face value — the prior effort's 2270-asset universe
  likely included small/micro-caps beyond real investment capacity, exactly this failure mode.

Taken together, this round's three papers give this survey a concrete, quantified execution-
realism and statistical-power toolkit it didn't have before — arguably more valuable than any
single new signal candidate found so far.

Note: "Dissecting Momentum in China" isn't yet well-indexed in Semantic Scholar (too new/preprint),
so no forward-citation trail was available for the survey's key ruled-out-momentum finding.

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
