# Citation Dynamics Paper — Outline

**Target venue:** COMPLEX NETWORKS 2026  
**Working title:** *Temporal Phase Structure of Citation Networks: Community Mixture Decomposition and Phase Visualization of the APS Corpus*

---

## §1 Introduction

- Citation networks encode causal structure of knowledge propagation — directed, irreversible, trustworthy
- Existing work: scale-free degree distributions documented since 1960s; single-process models fit global corpus
- The puzzle: a 1935 nuclear physics paper and a 2010 topological insulator paper live in the same global distribution. Implausible that one preferential attachment process governs both.
- **Zeitgeist hypothesis:** the global citation distribution is a mixture of subcommunity distributions, each individually scale-free, each corresponding to a distinct research generation
- What we do: decompose (Leiden) → validate mixture (per-community power-law fitting) → embed with causal awareness (NST) → visualize phase evolution (Time Curves)
- Why now: NST (ICLR 2025) makes causal-aware embedding tractable; Time Curves visualization not previously applied to citation networks; APS 2022 corpus gives 130 years of data

---

## §2 Related Work

- **Scale-free citation models:** Barabasi Network Science (2016): APS citation network γ=2.79 (pure) / 3.03 (with saturation+cutoff, p=0.69). Documents that pure power law fails globally (p<10^-4). Ke et al. 2023 PNAS "golden periods."
- **Temporal community detection:** Aparício et al. 2024 (KDD conference, no mixture model)
- **Phase transitions in citation networks:** Costa & Frigori 2024 (entropy+fractal dimension, AI lit only)
- **Generative mixture models:** Castillo-Castillo et al. 2025 (formal mixture model, no empirical APS test)
- **DAG embedding:** NST (Choudhary et al. ICLR 2025) — our representation layer, not a competitor
- **Temporal visualization:** Time Curves (Bach et al. IEEE TVCG 2015) — our visualization layer
- **Gap:** no work jointly tests mixture hypothesis + gives causal-aware embedding + produces temporal phase trajectories on a 130-year longitudinal corpus

---

## §3 Dataset

**Numbers (all confirmed):**
- N = 709,803 papers; L = 9,833,191 citations; 1893–2022; 20 APS journals
- Mean degree 13.84; Gini 0.692; 99.3% year coverage
- Pareto: top 1% → 20.5% citations; top 20% → 71.5%
- 1 giant WCC + 447 small components

**Global degree distribution:**
- Looks approximately power-law; Barabasi fits this exact dataset type at γ=2.79 (K_min=49) or γ=3.03 with saturation+cutoff
- Note: pure power law fails KS test globally (p<10^-4 per Barabasi) — motivates the mixture decomposition
- **OUR RESULT:** γ_global=2.738 (K_min=96, K_min scan over [1,100]) — consistent with Barabasi 2.79. Saved to `data/figures/global_fit.txt`

**Figure:** Fig 1 — in-degree CCDF log-log, power-law fit (γ=2.74, K_min=96) ✅ `data/figures/fig1_indegree_ccdf.pdf`

---

## §4 The Zeitgeist Hypothesis

### 4.1 Formal statement
- P(k) = Σ α_c P_c(k), each P_c(k) ~ k^{-γ_c}
- Two testable predictions: (i) each subcommunity passes power-law KS test; (ii) subcommunities are temporally localized

### 4.2 Community detection
- Leiden, resolution 1.0, full APS graph
- Result: 446 communities, Q = 0.7883
- Size distribution: 25 communities ≥ 30 nodes, covering 99.8% of papers (708,622/709,803)
- 421 communities are tiny fragments (<30 nodes) — expected at this resolution

### 4.3 Per-community power-law fitting
- Method: discrete MLE (Clauset et al. 2009) with K_min scanning (not fixed K_min=1)
- **FINAL RESULTS** (K_min scan, ks_boots=500): 25/25 pass KS test; γ_c ∈ [2.099, 3.268], mean=2.500±0.246
- Key finding: 100% of large communities pass KS power-law test — validates prediction (i)

### 4.4 Temporal localization
- Per-community year IQR: mean 18.4y, median 17y
- 68% of communities have IQR < 20 years — temporally localized Zeitgeists
- Medians span 1950–2017: community 20 (median 1950, IQR 16y) through community 12 (median 2017, IQR 7y)
- Validates prediction (ii)

**Table:** top-10 communities by size — n, γ_c, KS p, year median, year IQR, physics label  
(labels in `data/analysis/community_labels.csv` — verify communities 13/14/16/19 against APS journal context)

**Figures:** ✅
- Fig 3: γ_c histogram — `data/figures/fig3_gamma_histogram.pdf`
- Fig 4: community year-median timeline — `data/figures/fig4_timeline.pdf`

---

## §5 Causal Embedding via Neural Spacetimes

*(Pending cluster job 159670 — email notification at daveed@cs.toronto.edu)*

- **Motivation:** SG-t-SNE symmetrises the DAG, destroys causal direction. Need representation that preserves "paper A came before and influenced paper B."
- **Method:** NST (Choudhary et al. ICLR 2025) — product manifold R^D × R^T_+, spatial coord (community) + temporal coord (causal ancestry). Distortion bound: 1 + O(log n).
- **APS adapter:** 4 structural features [year_norm, log_indegree, log_outdegree, community_norm]; 500K sampled edges; space_dim=4, time_dim=4
- **Expected results:**
  - Temporal rank correlation: Spearman ρ(NST time coord, publication year) — expect >0.7
  - Cluster purity: do spatial coords separate Leiden communities?
  - Comparison: NST vs. SG-t-SNE baseline on same data

**Figure:** 2D projection of NST spatial coords, coloured by Leiden community  
**Figure:** NST temporal coord vs. publication year scatter (rank correlation)

---

## §6 Temporal Phase Visualization via Time Curves

*(Pending NST embeddings)*

- **From NST:** per-year centroid of spatial coords → 73×73 distance matrix (1950–2022)
- **Time Curves algorithm:** classical MDS init → SMACOF stress majorization + temporal ordering penalty → cusp/loop detection
- **Proxy run (done):** structural features give stress=0.000294, no cusps/loops — expected (year is directly encoded). NST will break this smoothness via community structure.
- **Expected findings:** cusps at known physics paradigm shifts; loops at recurring Zeitgeist themes
- **Candidate cusps to look for:** quantum mechanics consolidation (~1930s); nuclear/particle physics rise (~1950s–60s); condensed matter dominance (~1980s); topological matter emergence (~2005–10s)

**Figure:** Time Curves plot (2D curve, year labels, coloured by era, cusps annotated)

---

## §7 Backward Influence Mapping

*(Lower priority — may reduce to a brief case study)*

- Query: for a high-impact paper, who cited it and when?
- Method: `query_XY_subgraph` (existing MATLAB) — extract citing subgraph by date window
- Show in NST embedding: citing papers cluster near target in causal time
- Case study: pick 1–2 papers from the temporally extreme communities (cid=20 median 1950, cid=12 median 2017)
- Decision point: keep as full section or fold into §6 as a case study on the Time Curves?

---

## §8 Discussion

- **What we showed:** Zeitgeist validated; NST gives causal-aware embeddings; Time Curves reveals phase structure
- **Universal γ_c:** communities don't have heterogeneous exponents — same universal preferential attachment dynamics, different temporal windows. The Zeitgeist is about when, not how fast.
- **Limitations:** APS corpus only; NST uses structural features (no text/semantic); K17-RGC synthesis subgraph has 49/51 non-APS papers (corpus coverage gap)
- **Future:** aging model π(C) per community; cross-corpus validation; semantic features for NST

---

## Figures needed (complete list)

| Fig | Content | Status |
|-----|---------|--------|
| 1 | In-degree CCDF (global, log-log, γ=2.74, K_min=96) | ✅ `fig1_indegree_ccdf.pdf` |
| 2 | Community size distribution (446 communities) | ✅ `fig2_community_sizes.pdf` |
| 3 | Histogram of γ_c across 25 communities | ✅ `fig3_gamma_histogram.pdf` |
| 4 | Community year-median timeline (sorted horizontal bars) | ✅ `fig4_timeline.pdf` |
| Table §4 | Top-10 communities (n, γ_c, KS p, yr median, IQR, physics label) | Needs LaTeX markup from community_labels.csv |

---

## Open methodological TODOs

1. **Rewrite §§1 and 8** — remove NST/Time Curves framing. §1 currently pitches 4-stage pipeline; §8 discusses NST/Time Curves. Both dropped.
2. **LaTeX table for §4** — format top-10 communities from community_labels.csv into a proper table with physics labels.
3. **Verify 4 uncertain community labels** — communities 13, 14, 16, 19 (see community_labels.csv). Cross-check APS journal names for the top DOIs if needed.

**DONE:**
- ✅ K_min scan + γ_global=2.74 (K_min=96)
- ✅ Community physics labelling (all 25)
- ✅ All four §§1–4 figures generated
