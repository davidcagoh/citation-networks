# Signature Patterns: Embedding and Clustering Method Comparison

**Status:** Planned — thesis chapter / post-Zeitgeist-paper work.

This document frames the method comparison as a research contribution, not just an ablation study. The question is whether different methodological choices produce qualitatively different views of the citation structure, and whether any method is specifically suited to recovering the temporal lineage of research.

---

## The Two Comparisons

### 1. Clustering: Leiden vs BlueRed

**What each does:**
- **Leiden** — modularity-based community detection, resolution parameter tunable, scales to 700K nodes, Python/C++. Already used for the Zeitgeist paper.
- **BlueRed (DT-II spectral)** — bisection algorithm using the graph's second eigenvector (Fiedler vector), MATLAB-only, ~23 files. Bisects recursively; produces a hierarchical partition rather than a flat one.

**The question:** Does the Zeitgeist result — that each community has a distinct power-law exponent γ_c and temporal window — hold regardless of which clustering method finds the communities?

**Where it belongs:** Robustness appendix for the Zeitgeist paper (COMPLEX NETWORKS 2026). Low implementation cost: BlueRed is already in `deps/+bluered/`; the comparison is running both on the same graph and comparing γ_c distributions and community temporal windows. If the two partitions agree on the main finding, the result is method-agnostic — a strong thing to claim.

**Expected result:** Leiden and BlueRed should find broadly similar large-scale community structure (the APS physics subfields are real). Differences are likely at community boundaries and in how small communities are handled. The Zeitgeist claim should hold under both.

---

### 2. Embedding: NST vs UMAP vs SG-t-SNE

**What each does:**

| Method | Type | Key property |
|---|---|---|
| **NST** (Neural Spacetimes, Choudhary et al. ICLR 2025) | Representation learning on DAG | Causal/temporal ordering explicitly trained in — produces a separate temporal coordinate. DAG-native. |
| **SG-t-SNE** (Linderman et al.) | Graph visualization | Sparse-graph-native, 2D layout, symmetrizes the DAG (loses edge direction). Already in pipeline via Julia bridge. |
| **UMAP** | General-purpose manifold learning | Fast, topology-preserving, treats the graph as a proximity structure — ignores edge direction entirely. |

**The question:** Do causal/DAG-aware embeddings preserve research lineage structure that topology-blind methods lose?

**The thesis claim (hypothesis):** NST's explicit temporal coordinate should correlate more strongly with actual publication year within a research thread than UMAP or SG-t-SNE, because it trains on directed citation edges rather than symmetrized proximity. A paper's "causal ancestry score" (NST temporal coordinate) should reflect intellectual succession, not just co-citation proximity.

**Metrics to compare:**
- Spearman ρ between embedding temporal coordinate and publication year (causal preservation)
- Silhouette score within Leiden communities (cluster purity in 2D)
- Whether the community structure looks qualitatively different: NST may separate communities that SG-t-SNE merges because NST respects edge direction

**Where it belongs:** Thesis chapter / signature patterns contribution. This is not a robustness check — it's a methodological claim about what DAG-awareness buys you. The negative result from session 22 (NST spatial PCA not community-separating at the full-corpus level) doesn't kill this comparison: the synthesis subgraph scale (~500–2000 papers) is where NST may shine, since the temporal signal is cleaner in a focused topic area than across 25 heterogeneous physics communities.

**Implementation note:** NST is already trained and archived (`data/exported/aps-nst-*.pt/.npy`). The comparison can be run on the K17-RGC synthesis subgraph as a focused test case before scaling to the full corpus.

---

## Relationship to Other Work

- **Zeitgeist paper (COMPLEX NETWORKS 2026):** Leiden vs BlueRed comparison goes in as a robustness appendix. No new code needed.
- **Synthesis chapter:** NST vs SG-t-SNE vs UMAP comparison is the methodological backbone. The synthesis pipeline spec (`experiment-spec.md`) currently uses SG-t-SNE; adding NST and UMAP is the upgrade that makes it a comparison study rather than a single-method demo.
- **Aging model π(C):** Separate thesis chapter, not directly related to this comparison.

---

## Open Questions

- At what scale does NST's DAG-awareness become detectable vs SG-t-SNE? The full-corpus result (ρ=−0.668) suggests the signal is weak at scale; the synthesis subgraph is the right test bed.
- Does BlueRed's hierarchical partition have a natural correspondence to Leiden's flat partition at a given resolution? Needs a mapping strategy (e.g., majority-vote assignment of BlueRed leaves to Leiden communities).
- Is UMAP worth including, or is the NST vs SG-t-SNE contrast sufficient? UMAP adds a "no graph structure used" baseline which sharpens the argument.
