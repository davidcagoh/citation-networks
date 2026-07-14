# Q-SYNTH: Graph-Native Corpus Structuring — Plan

**Status:** Not started. Merged 2026-07-14 from `experiment-spec.md` + `methods-comparison.md`
(both deleted, superseded by this file) to remove duplication between the pipeline spec and the
method-comparison framing — they were describing the same investigation from two angles.

**Test case:** K17-RGC (Bobrowski & Kahle 2017 — Random Geometric Complexes), 56 gold papers,
100% recall from 1 seed paper via LitDiscover's traversal.

---

## What is this?

The downstream application of the citation-dynamics pipeline (Leiden community detection,
power-law/Zeitgeist fitting, NST/UMAP/SG-t-SNE embeddings) to a topic-specific subgraph built from
a LitDiscover-recovered paper set, instead of the full 709K-node APS corpus:

```
LitDiscover (recover papers) → citation-dynamics (understand their structure)
```

**Not** an automated survey-writing tool — it does not generate narrative text. It structures a
curated paper set for human consumption (cluster map, temporal emergence curves, influence-hub
table), and separately tests two methodological claims about *how* to do that structuring. This is
the **graph-native** protocol for corpus structuring — see `background/lineages/` for the
LLM-text-native alternative (citation-graph extraction + implicit mechanism-matching over paper
text) and `representation-learning-plan.md` for the embedding-native alternative (clustering over
different text representations). All three answer the same question — given a curated corpus,
organize it into interpretable structure — via disjoint mechanisms; see `roadmap.md` for how they
relate.

---

## Why K17-RGC

- Perfect recall (56/56) means the gold set is authoritative — no recall gaps to explain away.
- Topic (random geometric complexes / TDA) is coherent enough that clusters should be interpretable.
- Small enough (56 papers) for manual validation by a domain expert.
- Traversal already completed — no re-running needed.

---

## Pipeline

**Input scope — Option B (chosen):** 56 gold DOIs + 1-hop APS neighborhood (~500–2,000 papers).
56 papers alone have too few intra-set citations for Leiden to find meaningful structure (Option A);
the full 31,168-paper traversal set is too broad and off-topic (Option C). The 1-hop neighborhood
(papers the gold set cites, or that cite the gold set) is the immediate intellectual context —
exactly what's relevant to the review.

**Build the 1-hop subgraph:**
1. Find the 56 gold DOIs' indices in the full `doi` array.
2. Use the full `C` sparse matrix to extract all papers cited by, and citing, the 56.
3. Union: gold papers + cited papers + citing papers.
4. Build the induced subgraph `C_sub = C(union_idx, union_idx)`.
5. Filter to APS papers only (already guaranteed — all papers in `doi` are APS).

Direct application of `query_XY_subgraph.m`'s logic, adapted to DOI-index selection instead of
date-range selection.

**Pipeline steps:**

```
[Input: 56 gold DOIs]
    ↓
1. Build 1-hop subgraph → C_sub, doi_sub, pubDate_sub
    ↓
2. Leiden community detection on C_sub → cluster assignment vector
    ↓
3. Temporal window slicing → cluster × time-bin count matrix (emergence curves)
    ↓
4. Embedding into 2D — see "Embedding comparison" below for which method(s)
    ↓
5. Per-cluster statistics: in-degree hub ranking, power-law γ (Zeitgeist mixture test),
   top-3 representative papers per cluster
    ↓
6. Report: cluster map, temporal emergence curves, influence-hub table, markdown summary
```

---

## The two method-comparison questions

These aren't robustness afterthoughts — `methods-comparison.md` (now merged here) framed both as
real methodological claims, not just ablations.

### 1. Clustering: Leiden vs. BlueRed

| Method | Type | Property |
|---|---|---|
| **Leiden** | Modularity-based community detection | Resolution-tunable, scales to 700K nodes, Python/C++. Already used for the Zeitgeist paper. |
| **BlueRed (DT-II spectral)** | Fiedler-vector bisection | MATLAB-only, ~23 files. Recursive bisection → hierarchical partition, not flat. |

**Question:** Does the Zeitgeist finding (each community has a distinct power-law exponent γ_c and
temporal window) hold regardless of which method finds the communities?

**Where it belongs:** Robustness appendix for the *Zeitgeist* paper (COMPLEX NETWORKS 2026), not
this one — low implementation cost (BlueRed already in `deps/+bluered/`), run both on the same
graph, compare γ_c distributions and community temporal windows.

### 2. Embedding: NST vs. UMAP vs. SG-t-SNE

| Method | Type | Key property |
|---|---|---|
| **NST** (Neural Spacetimes, Choudhary et al. ICLR 2025) | DAG representation learning | Trains on directed citation edges; produces an explicit temporal coordinate |
| **SG-t-SNE** (Linderman et al.) | Graph visualization | Sparse-graph-native 2D layout, symmetrizes the DAG (loses direction). Already in pipeline via Julia bridge. |
| **UMAP** | General manifold learning | Fast, topology-preserving, treats the graph as proximity structure — ignores direction entirely |

**This is the actual thesis-chapter claim**, not a robustness check: do causal/DAG-aware
embeddings preserve research lineage structure that direction-blind methods lose?

**Hypothesis:** NST's temporal coordinate correlates more strongly with real publication year
within a research thread than UMAP or SG-t-SNE, because it trains on directed edges rather than
symmetrized proximity.

**Known disconfirming result already on record:** full-corpus NST test gave ρ=−0.668 (wrong sign)
— NST's spatial PCA didn't separate communities at that scale (session 22). This doesn't kill the
comparison: the synthesis-subgraph scale (~500–2,000 papers) is a genuinely different regime — the
temporal signal may be cleaner in one focused topic than across 25 heterogeneous physics
communities. But it means the hypothesis is currently disconfirmed at the one scale it's been
tested at, and untested at the scale that matters here.

**Metrics:**
- Spearman ρ between embedding temporal coordinate and publication year (causal preservation)
- Silhouette score within Leiden communities (cluster purity in 2D)
- Qualitative check: does NST separate communities SG-t-SNE merges, because it respects direction?

**Open questions carried over from `methods-comparison.md`:**
- At what scale does NST's DAG-awareness become detectable vs. SG-t-SNE? Full-corpus signal is
  weak (ρ=−0.668); K17-RGC subgraph is the untested test bed.
- Does BlueRed's hierarchical partition have a natural correspondence to Leiden's flat partition at
  a given resolution? Needs a mapping strategy (e.g. majority-vote assignment of BlueRed leaves to
  Leiden communities).
- Is UMAP worth including, or is the NST-vs-SG-t-SNE contrast sufficient? UMAP adds a
  "no-graph-structure-used" baseline that sharpens the argument either way.

---

## Output format

- **Cluster map** (`k17-rgc-cluster-map.pdf`): 2D embedding, points colored by Leiden cluster,
  top-3 most-cited papers per cluster labeled.
- **Temporal emergence curves** (`k17-rgc-temporal-curves.pdf`): one line/bar per cluster, x=year
  (binned), y=paper count — when did each thread emerge, is it growing or declining.
- **Influence hub table + report** (`k17-rgc-report.md`): per cluster — representative papers by
  in-degree, active period, growing/stable/declining, paper count, power-law γ.
- **Structured summary**: plain-language markdown a domain expert can sanity-check against ("do
  these clusters match how you understand the field?").

---

## Success criteria

**Primary:** A domain expert in TDA/random geometry reads the cluster labels + representative
papers and confirms the clusters are recognizable research threads with historically-plausible
temporal ordering.

**Operationally:**
- ≥70% of clusters have interpretable labels (not arbitrary groupings)
- Temporal emergence ordering is monotone-plausible (older threads precede threads they seed)
- Top-cited paper per cluster matches David's own mental model of the field's foundational works
- The influence-hub table would be useful to someone writing a manual lit review on this topic

**Zeitgeist sub-test (informal, not a formal statistical test at this scale):** each cluster's
in-degree distribution approximately scale-free (γ ∈ [1.5, 3.0]).

**Failure looks like:** all 56 papers in one cluster (no structure found); incoherent cluster
labels (unrelated papers sharing a cluster); flat temporal curves (no emergence signal).

---

## Files to create

```
citation-dynamics/src/synthesis/
    build_synthesis_subgraph.m    Extract 1-hop subgraph from DOI list
    run_synthesis_pipeline.m      Top-level script: Leiden + temporal + embedding
    generate_synthesis_report.m   Cluster map + temporal curves + Markdown report

citation-dynamics/data/synthesis/
    k17-rgc-gold-dois.txt         Input: 56 recovered DOIs, one per line

citation-dynamics/outputs/synthesis/
    k17-rgc-cluster-map.pdf
    k17-rgc-temporal-curves.pdf
    k17-rgc-report.md
```

---

## Blocking prerequisites

- [x] **Gold set exists — verified 2026-07-14.** Not at the path this spec originally guessed
  (`projects/kahle-simplicial-geometry/` doesn't exist); actual location is
  `lit-review/robust-literature-discovery/live-survey-eval/data/gold-sets/K17-RGC_gold.json` — **52
  entries** (not 56; matches the already-logged gold-set data-quality fix, 56→52), each with
  `raw_title`/`doi`/`s2_id`/`manual_s2_id`. All 52 have an S2 ID; 49 of 52 also have a DOI directly.
  Enough to build the 1-hop subgraph either way (S2 ID alone suffices for identity lookup against
  the `C` matrix if a DOI join isn't available for the remaining 3). Section-level ground truth
  (`K17-RGC_sections.json`) and the source PDF/seed list are in the same `live-survey-eval/data/`
  tree, already built per `representation-learning-plan.md`.
- [ ] Planner agent sprint plan (defines implementation order)
- [ ] Architect agent data-handoff design (subgraph export format, if Python is involved anywhere)
- [ ] `citation-dynamics/src/synthesis/` directory created
- [ ] This spec reviewed and agreed by David

**Immediate next action:** the cheapest blocking prerequisite is now resolved. Next up is either
the planner/architect agent outputs, or — cheaper still — just building the 1-hop subgraph
directly from the verified gold set and running Leiden once to see if there's a signal worth
formalizing before investing in the full sprint-planning step.

---

## Relationship to Zeitgeist

If the Zeitgeist hypothesis holds at 709K-paper scale, it should hold at subgraph scale: each
Leiden cluster within the 56-paper neighborhood should be approximately scale-free, and the mixture
of per-cluster distributions should reconstruct the subgraph's global distribution. Informal sanity
check, not the main validation (that runs on the full corpus, defined separately).

---

## Positioning against the LLM-synthesis literature

Not survey generation — analyzing the *already-recovered* paper set's citation structure, not
recovering or summarizing papers. AutoSurvey, PaSa, GraphRAG, LiRA and the rest of
`background/reference-implementation-survey.md`'s corpus are background, not competitors:
cite them to establish that no validated synthesis-quality standard exists in that literature
(`background/eval-standard-gap.md`), and that Q-SYNTH's success criteria (cluster interpretability,
temporal plausibility, expert recognition) are a different, more tractable validation target than
"is this generated prose good synthesis" — worth stating explicitly since a reviewer familiar with
the AutoSurvey-style literature might otherwise expect Q-SYNTH to be held to that same
(unvalidated) bar.
