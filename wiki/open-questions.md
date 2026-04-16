# Open Questions

Unresolved issues that block or weaken the paper. Ordered by importance.

---

## BROADER PROJECT QUESTIONS (citation-dynamics / synthesis stage)

### ~~Q-SOTA: Is the citation-dynamics lit review still current? What is the state of the art in 2026?~~
**RESOLVED (2026-04-12, session 12).** Search run over 2024–2026. Full source list in session-log.md.

**Verdict: Zeitgeist hypothesis is still a gap.** No paper formalizes the specific claim that the global APS citation distribution is a temporal mixture of individually scale-free subcommunity distributions corresponding to distinct research generations, nor does any paper combine backward-influence mapping + spherical-geometry t-SNE for phase detection.

**Nearest prior art to cite and differentiate from:**
- Costa & Frigori (2024). "Complexity and phase transitions in citation networks." *Frontiers Research Metrics*, 9:1456978. Uses entropy + fractal dimension to detect phase transitions in AI literature only; no mixture decomposition, no geometric embedding.
- Aparício et al. (2024). "Using dynamic knowledge graphs to detect emerging communities of knowledge." *Knowledge-Based Systems*, 294:111671. Temporal community trajectories in KDD conference; no scale-free mixture modeling, no APS corpus.
- Castillo-Castillo et al. (2025). "A growth model for citations networks." *Applied Network Science*. Generative model formalizing mixture-of-subcommunities picture, but no temporal phases or empirical APS test.
- Ke, Gates & Barabási (2023). "A network-based normalized impact measure." *PNAS* 120(47). Characterizes temporal "golden periods" of scientific discovery; measures impact, not structural subcommunity decomposition.

**Competition on the embedding front (action required):**
- Romero et al. (2024). "Gaussian Embedding of Temporal Networks" (TGNE). arXiv:2405.17253. Richer geometry than prior parametric embeddings.
- **Choudhary et al. (2024). "Neural Spacetimes for DAG Representation Learning." arXiv:2408.13885. ICLR 2025.** Embeds DAGs (= citation networks) into product manifolds with quasi-metric + partial order. Universal embedding theorem. This is the strongest geometric competitor to SG-t-SNE — thesis must either compare against NST or reframe SG-t-SNE as a visualization tool (complementary, not competing).

**LLM synthesis SOTA (for synthesis stage framing):**
The area has exploded. Key tools to be aware of:
- AutoSurvey (Wang et al., NeurIPS 2024 workshop): two-stage parallel LLM survey generation with live RAG
- PaSa (He et al., 2025, arXiv:2501.10120): RL-trained agentic paper search — direct candidate for the retrieval stage
- GraphRAG (Edge et al., Microsoft Research, arXiv:2404.16130): LLM-built community graph → hierarchical summarization. Directly applicable to citation corpus synthesis
- LiRA (Agrawal et al., 2024, arXiv:2510.05138): multi-agent SLR pipeline

**Repositioning actions for thesis:**
1. Claim APS corpus + backward-influence mapping as the empirical instantiation (no one has done this combination)
2. Claim Zeitgeist hypothesis as an original statistical conjecture (mixture of scale-free subcommunities) — still untested in the literature
3. SG-t-SNE framing: reposition as *visualization* relative to NST (representation); direct comparison optional but strengthens chapter
4. Add Costa & Frigori (2024) and Aparício et al. (2024) to related work as nearest prior art

### Q-SYNTH: What does the synthesis pipeline experiment look like concretely?
**MOSTLY RESOLVED (2026-04-16, sessions 17–19).** Spec written in `wiki/synthesis-experiment.md`. Option B (1-hop subgraph) chosen. 51 gold DOIs extracted. Python scripts for Phase 1 HDF5 (`build_aps_hdf5.py`), Phase 5 subgraph (`build_synthesis_subgraph.py`), and Leiden clustering (`leiden_cluster.py`) all written.
**Still open:** None of these scripts have been run yet — `data/exported/` is empty. Run `build_aps_hdf5.py` first (≈10–20 min).

---

## RESOLVED

### ~~MAX_DEPTH vs N_ROUNDS — are they redundant?~~
**Resolved:** Different granularities. MAX_DEPTH caps depth within one traversal call (safety valve, rarely binds). N_ROUNDS caps how many traversal-then-escape-hatch cycles run. N_ROUNDS is the operative parameter. In production there is no N_ROUNDS — the loop runs until the escape hatch mechanism is exhausted.

### ~~Is the APS simulation a valid proxy for production?~~
**Resolved:** Yes, as a conservative lower bound. Both systems implement the same core idea (expand graph, measure yield, stop when low, search for re-entry). The simulation uses weaker escape hatches (graph-only) and a fixed Pareto filter. Production is more powerful on both counts. So APS recall numbers are a floor. See simulation-vs-production.md.

### ~~Should we implement adaptive Pareto filter in the simulation?~~
**Resolved:** Not yet. Run the fixed-filter sweep first. If different surveys have different optimal thresholds, adaptive is motivated. If not, it adds complexity for nothing.

### ~~Filter direction in APS simulation — in-degree or out-degree?~~
**Resolved:** **Out-degree filter on forward candidates** is the correct semantics for the APS simulation. Scripts 03, 05, 08 have been reverted to match 04b. This is finalized. The production system (`traverse.py`) uses in-degree of frontier papers — a separate, documented implementation choice. See simulation-vs-production.md.

### ~~Script 08 hyperparameter sweep — has it been run?~~
**Resolved:** Complete. 1980 rows in `hyperparameter_sweep.csv`. Used out-degree filter (consistent with other scripts).

### ~~Fig 4 title — is it "seeded from survey paper" or "seeded from top-5 gold references"?~~
**Resolved:** Fixed. Title now says "seeded from top-5 gold references". See figure-roles.md.

### ~~Why use Pareto-80 and not Pareto-50?~~
**Resolved (2026-04-10):** Under yield-based stopping (the operational condition), Pareto-50 gives S1=80.4% vs Pareto-80=86.9%. The choice is not arbitrary — tighter filter reduces nodes explored per round, directly lowering recall under stopping. Pareto-80 is the chosen operating point. Fig3 (full-depth, no stopping) shows all thresholds reach 100% — that is a different operating condition. See decisions.md PARETO_P section.

---

## BLOCKERS

### Q1: Complete live experiments before submission
**Why it matters:** §7 (Main Results: Live Discovery) requires at least two live results. The paper's argument has live experiments as its centrepiece.

**Current status:**

| Survey | ID | Gold papers | Status | Result |
|---|---|---|---|---|
| Bobrowski & Kahle 2017 (random geometric complexes) | K17-RGC | 56 | ✅ Complete | **100% recall (56/56), depth 2, round 1**. Corpus 31,168. Yield at depth 2 = 0.16% (well below 5% threshold). 1 seed paper ("Topology Applied to Machine Learning"). |
| Galesic et al. 2021 (human social sensing) | Ge21-HSS | 202 | 🔄 In progress | Not yet complete. |
| Le et al. 2025 (grounded LLMs) | Le25-GLLM | TBD | ⏳ Seeds added, not yet run | — |

**K17-RGC note:** 100% recall from 1 seed stopping at depth 2 is a strong result and validates the system on a real user task. Corpus yield dropping to 0.16% confirms that the yield-stopping rule fires correctly.

**What's needed to unblock:** Complete Ge21-HSS run. Le25-GLLM is a bonus third experiment.
**Config files:** `projects/kahle-simplicial-geometry/project.toml`, `projects/galesic-human-social-sensing/project.toml`

---

## ANALYSIS GAPS

### Q2: Does Fig 7 miss analysis use k=5 or k=20 seeds?
**Why it matters:** Script 05 says "canonical case = k=20"; paper reports k=5 results. If the missed sets differ, Fig 7 is showing the wrong scenario.
**How to resolve:** Check whether `cold_start_results_lowseed.json` at k=5 gives 519/582 for S1, same as k=20 run. If different, rerun script 05 with k=5.

### Q3: Why does Fig 6 show non-monotone recall for contaminated seeds?
**Why it matters:** Recall drops at k=4 in some surveys. Reviewers will flag this as a bug.
**Probable answer:** Contaminated seeds (50% irrelevant) reduce yield faster → yield-stopping triggers earlier → less traversal → lower recall. More contaminated seeds = worse stopping.
**How to resolve:** Add one paragraph explaining this in §8. Optionally move contaminated condition to appendix.

### Q4: Why use Pareto-80 and not Pareto-50?
**Why it matters:** Fig 8 shows Pareto-50 achieves identical recall at depth 3 with lower cost. The choice of 80th percentile looks arbitrary.
**Probable answer:** Pareto-50 is more aggressive and may fail under yield-based stopping (the actual operating condition). Need to test this.
**How to resolve:** Either demonstrate that Pareto-50 fails under stopping, or acknowledge Pareto-80 is a conservative default and note Pareto-50 could work.

### Q5: For S1, why do random seeds outperform top-5-by-citation at round 1?
**Why it matters:** Top-5 is labelled "best-case" — it should not lose to random.
**Probable answer:** The 5 most-cited gold refs in S1 (a 1998 metal-insulator survey) all cluster in one corner of the graph; 5 random draws cover more diversity by chance. This is a single draw, so it may also be sampling noise.
**How to resolve:** Run multiple trials (≥5) for random seeds and report mean ± std. If mean of random < top-5, the issue goes away. If not, discuss concentration problem in text.

---

## FIGURE FIXES (not blockers but needed before submission)

### Q11: Add [CITATION NEEDED] at yellow-highlighted locations
Paper text has yellow-highlighted locations that need citations. Must be completed before submission.

### Q15: §5 note — yield lines overlap
In fig9b, yield threshold lines overlap (different yield thresholds produce identical recall curves). This is a finding: yield threshold doesn't affect final recall, only screening cost. §5 needs an explicit sentence stating this.

**Resolved figure fixes:** Q6 (fig4 title), Q7 (fig7 out-degree skipped), Q8 (fig2 oracle callout), Q12 (related work moved to §2), Q13 (k=1 in conclusion), Q14 (§5 fig2 text update), Q16 (fig6 non-monotonicity caption + §5 paragraph) — all ✅.

---

## LOW PRIORITY

### Q9: Should γ < 2 be flagged in Fig 1?
Both in-degree and out-degree exponents are < 2 (γ ≈ 1.85/1.90). This is unusual. A KS goodness-of-fit test would either support or qualify the power-law claim. Adding a sentence in §5 is sufficient.

### Q10: Add error bars to Figs 5–6
Random and contaminated seed conditions show results from a single draw. Multiple trials would replace the erratic zigzag with a mean + confidence interval. Improves robustness but not strictly required for the paper's argument.
