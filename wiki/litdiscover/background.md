# Background — algorithm, paper structure, sim-vs-production

**Read-once reference.** This file merges what used to be four files (`thesis.md`,
`argument-map.md`, `figure-roles.md`, `simulation-vs-production.md`) — load it to understand
what LitDiscover *is* and how the (pre-rejection) paper was shaped. For active work, read
`decisions.md` and `open-questions.md` instead; those are the live files.

**Staleness note:** the paper-structure sections below (Argument Map, Figure Roles) reflect the
draft as of the JCDL/TOIS/JASIST submission cycle (last synced ~2026-04-21), before IP&M's
desk-rejection (2026-07-07) and the ongoing redo. The core algorithmic claim (Thesis, Sim vs
Production) is unaffected by the redo — only the related-work/SOTA-baseline framing is changing.
See `lineages/similarity-cluster.md` for the narrative lineage and `decisions.md`'s full-text-verification entry for what's new.

---

## 1. Thesis

### The Claim

> **LitDiscover recovers near-complete literature sets (89–98% recall) from as few as 5 seed papers, using bidirectional citation traversal with a Pareto hub filter and yield-based stopping.**

Two rounds of traversal suffice. Round 1 does 85–98% of the work; round 2 is cheap insurance. What remains unreachable is structurally peripheral: rarely-cited papers that are adjacent to the core but filtered out or never seeded.

### Why This Is Non-Obvious

Naively, comprehensive literature discovery requires either a complete database query (impossible without knowing the query terms) or manual snowballing (slow, depends entirely on the reviewer's knowledge).

The insight that makes LitDiscover possible is structural: **citation graphs are power-law skewed**. A small fraction of papers accumulate most of the citations, and those hub papers act as connectors that link disparate subfields. Starting from any 5 papers in a subfield, bidirectional BFS reaches most of the connected literature within 2–3 hops.

Two practical problems arise from naive BFS:
1. **Forward traversal explodes** — papers that cite a hub may cite thousands of other things too, most irrelevant. The Pareto filter suppresses forward-direction nodes whose out-degree is in the top 20%.
2. **When to stop?** — the screen yield (new relevant papers / new papers seen) drops sharply as you move away from the core. Stopping when yield < 5% keeps cost manageable.

### The Mechanism (one paragraph)

A user provides k seed papers. LitDiscover traverses backward (papers the seeds cite) and forward (papers that cite the seeds), applying the Pareto filter to forward candidates. It stops each round when yield drops below 5%. After round 1, it picks k=20 new seeds from the neighbourhood of papers already found and repeats — this is the "Escape Hatch" for papers the first round missed. Two rounds converge in all three benchmark surveys.

### What This Paper Does NOT Claim

- It does not claim 100% recall in all cases. S1 (a 1998 survey in an older subfield) reaches ~89% — the gap is explained.
- It does not claim to replace human judgement on inclusion/exclusion. The system produces a candidate set; screening remains human.
- It does not claim the method works outside physics journals — the APS corpus is the validation environment; live experiments (Kahle, Galesic) extend this.

### The Contribution

Not a new algorithm — bidirectional BFS and Pareto filtering are known. The contribution is:
1. **The combination**: bidir BFS + Pareto filter + yield stopping + Escape Hatch, run together, achieves near-complete recall from minimal seeds.
2. **The benchmark**: three real physics survey papers as ground truth, in a 700k-paper corpus, with full closed-form validation.
3. **The structural explanation**: characterising what gets missed and why (structural peripherality, not random failure).

---

## 2. Simulation vs Production

The APS simulation and the production LitDiscover system implement the same core idea with different engineering constraints. Understanding the gap is important for scoping the paper's claims correctly.

### They're doing the same thing

APS simulation: `traverse (BFS, depth-by-depth) → check yield per depth → stop when yield < 5% → escape hatch (top-K graph-neighbours) → repeat N_ROUNDS times`

Production: `traverse (one pass over all included papers) → screen candidates → check yield per cycle → escape hatch (Semantic Scholar keyword search) → repeat until stable`

Same core logic: expand the graph, measure how fruitful the expansion is, stop when it isn't, search for a new entry point, repeat. Production just expresses this in an event-driven, persistent, parallelised form because it needs to run on real APIs without ground truth.

### Why the simulation is cleaner for research

Production accumulated complexity to solve deployment problems (Supabase persistence, background threads, event-driven triggers, adaptive Pareto filter, criteria refinement) — none of which change the research question. The APS simulation strips them away and asks: does the core algorithm work? That's the research contribution; live experiments validate the engineering wrapper doesn't break it.

### Key differences (what the paper needs to acknowledge)

| Dimension | APS simulation | Production |
|---|---|---|
| Traversal unit | BFS depth-by-depth | One pass over full included set |
| Traversal trigger | Fixed N_ROUNDS | Event-driven (yield ≥ 5% or queue empty) |
| Escape Hatch | Top-K graph-neighbours by in-degree | LLM-generated query → Semantic Scholar search |
| **Pareto filter target** | **Forward candidates (citers), by OUT-DEGREE** | **Frontier papers, by IN-DEGREE (citation_count)** |
| Pareto filter calibration | Fixed percentile (parameter to sweep) | Adaptive (Gini-calibrated per round) |
| Yield measured | New gold refs / new nodes at each BFS depth | Included / screened per screening cycle |
| Ground truth | Known (gold bibliography) | None — yield is proxy |
| Stopping | Fixed N_ROUNDS | Escape hatch exhausted (max 3 attempts) |

### What this means for the paper

**Simulation claims (§8 APS Validation):** the fixed-parameter algorithm achieves 89–98% recall on three benchmark surveys — the core algorithmic claim. N_ROUNDS, Pareto threshold, and yield threshold are hyperparameters characterised in the sweep (Appendix).

**Live experiment claims (§7):** production, implementing the same algorithm with adaptive Pareto and event-driven triggers, achieves comparable recall on real discovery tasks (Kahle, Galesic) — validates the engineering wrapper doesn't break the algorithm.

**Limitations to state explicitly:**
1. The APS escape hatch is graph-expansion (graph-neighbours by in-degree), not semantic search. It works because APS misses happen to be graph-adjacent (BFS distance 1). Production's semantic search escape hatch is stronger — it can find papers with no graph path to the found set.
2. All APS hyperparameters are characterised on three surveys in one corpus. Generalisation to other corpora is validated by live experiments, not by the APS sweep.

### Pareto filter direction (SETTLED)

The filter direction in the APS simulation is finalized. Scripts 03, 05, 08 have been reverted to match script 04b: **out-degree filter on forward candidates**. This is consistent across all simulation scripts and is no longer an open question. The simulation-production gap is a known, documented difference, not a bug — it is acknowledged in the paper.

The conceptual intent is identical ("don't explode the traversal through giant hubs") but the proxy differs:

**Production:** a highly-cited frontier paper (e.g., cited by 50k papers) has an enormous forward neighbourhood. If `citation_count > Pareto threshold`, skip forward traversal for that paper entirely. Filter is on the **frontier paper's in-degree**.

**APS simulation:** after collecting citers of the frontier set, removes citers whose own reference list exceeds the Pareto percentile — treating a high-out-degree citer as "survey-like." Filter is on the **citer's out-degree**.

**Where they diverge:** a domain survey citing 400 relevant physics papers but itself cited by only 30 papers — production lets it through (low citation_count → forward traversal proceeds, its 400 refs enter the corpus, correct). The simulation would instead risk removing the *survey itself* from the forward candidate set if its own out-degree is in the top 20%. In practice this failure mode is rare (the problematic citer IS usually a specialist paper, not a survey), which is why the simulation's recall numbers hold up — but the paper should describe the in-degree-on-frontier-papers semantics as correct, noting the simulation approximates it via out-degree of forward candidates.

### On the adaptive Pareto filter

Production auto-calibrates the Pareto threshold based on the Gini coefficient of the included set's citation counts: high Gini (power-law, large topic) → strict 80th percentile; low Gini (uniform, small niche) → relaxed 90th–95th percentile.

Script 08's hyperparameter sweep (1980 rows across S1/S2/S3, covering PARETO_P × YIELD_THRESHOLD × N_ROUNDS × K_ESCAPE with k=5 top-k seeds) is complete. Whether this motivates adaptive calibration can be read directly from the sweep results — if all three surveys share the same optimal threshold, adaptive adds no value.

---

## 3. Paper Structure — Argument Map + Figure Roles

*Last synced to draft: ~2026-04-21, pre-IP&M-rejection. Section numbering and content below will
shift once SOTA/LLM baseline comparisons from the redo are incorporated — treat as the shape of
the old draft, not a spec for the new one.*

### Argument chain

Each step is a section of the paper. The "without this" column shows what breaks if the step is missing.

**§1 Introduction** — Claim: comprehensive literature discovery is expensive and current tools are incomplete. Evidence: prose, cited prior work. Without this: reader has no reason to care.

**§2 Related Work** — Claim: existing approaches (keyword search, forward/backward citation chasing, manual-heavy systematic review tools) each fail in isolation. Evidence: citations to existing tools. Without this: paper looks like it ignores prior art. Moved up front (was §6 in the original draft) — the argument depends on knowing what's already been tried. **This section is exactly what the redo (see `lineages/similarity-cluster.md`) is rebuilding.**

**§3 Architecture** — Claim: LitDiscover implements a specific state machine: SEED → SEARCH → SCREEN → TRAVERSE → ESCAPE HATCH → STABLE. Evidence: system diagram, pseudocode, parameter table. Without this: figures 3–8 are uninterpretable.

**§4 Benchmark Design** — Claim: three APS review papers with known bibliographies form a closed-corpus ground truth for recall measurement. Evidence: table of surveys (S1, S2, S3), APS corpus statistics, definition of "overlap" metric. Without this: results look circular. Note: 100% of gold refs from all three surveys are in the APS corpus (confirmed empirically) — no corpus-coverage ceiling, all misses are algorithm failures.

**§5 Structural Motivation** — Claim: the citation graph's structure explains why the algorithm works.

| Sub-claim | Figure | What it shows |
|---|---|---|
| Citations are power-law skewed | Fig 1 | γ ≈ 1.85 in-degree; Gini = 0.69 → top 20% papers hold most citations |
| Starting near the core, BFS reaches everything in 2 hops | Fig 2 | Oracle-seeded BFS overlap vs depth (oracle/upper bound) |
| Bidir+Pareto dominates other strategies on cost–recall | Fig 3 | Strategy scatter at depth 3 |
| Yield collapses rapidly → stopping is principled | Fig 4 | Screen yield per depth |

Without this section, the algorithm looks arbitrary — the structural argument is what makes it convincing.

**§6 Miss Analysis + Efficiency** — Claim: what the algorithm misses is not random — it is structurally peripheral. The Pareto filter dramatically cuts cost at no recall penalty. Evidence: Fig 7 (missed papers have low in-degree, median 9–29 vs 220 for recovered; 90%+ at BFS distance 1) and Fig 8 (Pareto threshold sweep — all thresholds reach 100% recall at depth 3, cost drops 20–30% with Pareto-80 vs no filter). Placed before main results — primes the reader to understand the residual gap before seeing recall numbers.

**§7 Main Results: Live Discovery** — Claim: LitDiscover achieves high recall on real discovery tasks outside the training distribution. Evidence:

| Survey | ID | Gold papers | Result |
|---|---|---|---|
| Bobrowski & Kahle 2017 (random geometric complexes) | K17-RGC | 56 | 100% recall (56/56), depth 2, round 1, 1 seed, corpus 31,168 |
| Galesic et al. 2021 (human social sensing) | Ge21-HSS | 202 | done |
| Le et al. 2025 (grounded LLMs) | Le25-GLLM | — | 73.7% (per `open-questions.md`'s Q1 resolution) |

Without this, the paper is purely a closed-corpus study validating the algorithm where ground truth is known in advance.

**§8 APS Closed-Corpus Validation** — Claim: 89–98% recall across three APS benchmark surveys using k=5 seeds and 2 rounds.

| Survey | Recall (k=5, 2 rounds) | Gold set |
|---|---|---|
| S1 MIT 1998 | 89.2% (519/582) | 582 refs |
| S2 UCG 2008 | 98.4% (425/432) | 432 refs |
| S3 TOPO 2019 | 96.9% (375/387) | 387 refs |

Narrative tension: S1 underperforms vs S2/S3, explained by age (1998 survey — most-cited papers have very high in-degree, concentrate in a small part of the graph; random seeds sometimes outperform top-k because top-k is too concentrated). Discussed, not hidden.

**§9 Conclusion** — Claim: minimal-seed literature discovery via graph traversal is practical, residual gap is structural and interpretable.

### Figure status (as of last sync)

Dependency chain: fig3 → fig4, fig8 (uses Pareto default/needs lower range); fig6 → fig5 (uses k=5).

| Fig | Proves | Status |
|-----|--------|--------|
| fig1 — degree distributions + Lorenz curves | Citation graphs heavy-tailed → Pareto filter structurally justified | Fixed — Barabási MLE fit (γ ≈ 3.03, p=0.69), log-scale histogram |
| fig2 — BFS reachability vs depth | Bidirectional traversal necessary (backward-only misses recent work, forward-only misses foundational work) | Fixed — backward/forward/bidirectional comparison from same fixed seeds |
| fig3 — strategy comparison | Pareto filter reduces cost with no recall penalty at correct depth | Fixed — annotated "Pareto-80 (operational default)" |
| fig4 — screen yield collapse | Depth 2 does most of the work (72/66/54% of gold for S1/S2/S3); round 2 adds 1–4% | Fixed — stacked bar (Round 1 solid + Round 2 lighter) |
| fig5 — cold-start recall per round (k=5) | Even 50% off-topic seeds recover to ≥90% by round 2 | Fixed — y-axis corrected, labels simplified |
| fig6 — final recall vs seed size (k=1–10) | Recall robust across seed sizes | Fixed — non-monotonicity explained (top-k dips at k=2 from shared backward neighborhoods; contaminated declines with k) |
| fig7 — miss analysis (in-degree + BFS distance) | Missed papers structurally peripheral | Fixed — log-log histogram; 97% of misses at BFS distance 1 |
| fig8 — efficiency frontier (Pareto sweep) | Dropped — at full depth all Pareto values reach 100% recall, misleading; fig3 covers strategy comparison, trade-off now stated in prose |
| fig8b, fig8c, fig9a–d | All dropped — each redundant with a kept figure (fig3, fig4, fig6, fig8c) or vacuous (fig9b's yield sweep falls below any tested threshold regardless of setting) |

**Open question carried forward:** why Pareto-80 and not Pareto-50? Fig 8 shows both reach 100% recall at depth 3 (full-depth, no yield stopping) — but under yield stopping (operational condition), threshold genuinely matters (see `decisions.md`'s PARETO_P sweep table). Both figures are correct; they describe different operating conditions, and the paper must make that explicit.
