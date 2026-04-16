# Synthesis Experiment Spec: Q-SYNTH

**Status:** Draft — awaiting planner + architect agent outputs before implementation begins.
**Test case:** K17-RGC (Bobrowski & Kahle 2017 — Random Geometric Complexes)

---

## 1. What Is This?

The synthesis step is the downstream application of the citation-dynamics pipeline to the output of LitDiscover (robust-literature-discovery). Instead of analyzing the full 709K-node APS corpus, we analyze a topic-specific subgraph built from a recovered paper set.

This closes the loop between the two halves of the project:
```
LitDiscover (recover papers) → citation-dynamics (understand their structure)
```

---

## 2. Test Case: K17-RGC

| Property | Value |
|---|---|
| Survey | Bobrowski & Kahle 2017, "Topology of random geometric complexes: a survey" |
| Gold paper count | 56 |
| Recall | 100% (56/56) from 1 seed paper |
| Seed | "Topology Applied to Machine Learning" |
| Traversal corpus | 31,168 APS papers visited |
| APS corpus | Full 709,803 papers available |

Why K17-RGC as the test case:
- Perfect recall means the gold set is authoritative — no recall gaps to explain away
- The topic (random geometric complexes / TDA) is coherent enough that clusters should be interpretable
- The gold set (56 papers) is small enough for manual validation by a domain expert
- The traversal already completed — no re-running needed

---

## 3. Pipeline Inputs

**Primary input:** The 56 recovered DOIs from the K17 traversal.

The DOI list needs to be extracted from the LitDiscover traversal output. Location: `lit-review/robust-literature-discovery/projects/kahle-simplicial-geometry/` — check traversal output files for the recovered DOI list.

**Three input scope options (choose one):**

| Option | Scope | Node count (estimate) | Rationale |
|---|---|---|---|
| A | 56 gold DOIs only + intra-set edges | ~56 + few edges | Too sparse for Leiden |
| **B (chosen)** | **56 DOIs + 1-hop APS neighborhood** | **~500–2,000 papers** | Dense enough for community detection, stays on-topic |
| C | Full 31,168 traversal-visited set | 31,168 | Too broad; includes many peripherally related papers |

**Why Option B:** Leiden community detection needs enough within-cluster edges to be meaningful. 56 papers alone will have few intra-set citations (most of the 56 cite external papers, not each other). The 1-hop neighborhood captures the immediate intellectual context — papers that the gold set cites or that cite the gold set — which is exactly the community relevant to the structured lit review.

**How to build the 1-hop subgraph:**
1. Start with 56 gold DOIs → find their indices in the full `doi` array
2. Use the full `C` sparse matrix to extract: all papers cited by the 56 (C(gold_indices, :)) and all papers citing the 56 (C(:, gold_indices))
3. Take the union of: gold papers + cited papers + citing papers
4. Build the induced subgraph on this union: `C_sub = C(union_idx, union_idx)`
5. Filter to APS papers only (all papers in `doi` array are already APS)

This is a direct application of `query_XY_subgraph.m` logic, adapted to DOI-index-based selection rather than date-range selection.

---

## 4. Pipeline Steps

```
[Input: 56 gold DOIs]
    ↓
Step 1: Build 1-hop subgraph
    - Extract gold DOI indices from full doi array
    - Expand to 1-hop neighborhood via C matrix
    - Build induced subgraph C_sub (n_sub × n_sub sparse)
    - Output: C_sub, doi_sub, pubDate_sub

    ↓
Step 2: Leiden community detection on C_sub
    - Run leiden.cluster(C_sub, ...)
    - Output: cluster assignment vector (n_sub × 1 integer)

    ↓
Step 3: Temporal window slicing
    - Group papers by publication decade (or 5-year bins)
    - Per cluster × per window: count papers
    - Output: cluster × time bin count matrix (emergence curves)

    ↓
Step 4: SG-t-SNE embedding
    - Embed C_sub into 2D
    - Output: 2D coordinates (n_sub × 2 float)

    ↓
Step 5: Per-cluster statistics
    - In-degree within C_sub (influence hub ranking)
    - Power-law exponent γ per cluster (Zeitgeist mixture test)
    - Representative paper selection: top-3 by in-degree per cluster

    ↓
Step 6: Generate report
    - Cluster map (2D embedding with cluster colors + top paper labels)
    - Temporal emergence curves (per cluster, papers per time bin)
    - Influence hub table (top-5 papers per cluster, with DOI + year)
    - Markdown summary file
```

---

## 5. Output Format

### 5a. Cluster Map (Figure)
- 2D SG-t-SNE embedding of the subgraph
- Points colored by Leiden cluster label
- Top-3 most-cited papers per cluster labeled by last-name + year
- Saved as: `citation-dynamics/outputs/synthesis/k17-rgc-cluster-map.pdf`

### 5b. Temporal Emergence Curves (Figure)
- One line/bar per Leiden cluster
- X-axis: publication year (binned by decade or 5-year window)
- Y-axis: paper count in that bin
- Shows: when did each research thread emerge? Is it growing or declining?
- Saved as: `citation-dynamics/outputs/synthesis/k17-rgc-temporal-curves.pdf`

### 5c. Influence Hub Table (Data + Markdown)
For each cluster:
```
## Cluster [N]: [human label — to be filled in after inspection]
- Representative papers (by in-degree within subgraph):
  1. [DOI] — [Author year] — [in-degree N]
  2. ...
  3. ...
- Active period: [decade range with most papers]
- Status: [growing / stable / declining]
- Papers: [count]
- Power-law γ: [value] (Zeitgeist check)
```
Saved as: `citation-dynamics/outputs/synthesis/k17-rgc-report.md`

### 5d. Structured Summary (Human-readable)
A single Markdown file that a non-expert could hand to a domain expert and say "does this match how you understand the field?" Structure:
- Brief field overview (generated manually based on cluster inspection)
- Numbered cluster descriptions
- Temporal narrative: "Thread X emerged in [decade], peaked in [decade], gave rise to Thread Y"
- Key foundational papers list

---

## 6. Success Criterion

**Primary:** A domain expert in TDA / random geometry (could be David's supervisor Xiaobai Sun, or confirmed via literature knowledge) reads the cluster labels + representative papers and says: "Yes, these clusters correspond to recognizable research threads. The temporal ordering makes historical sense."

**Operationally:**
- ≥ 70% of clusters have interpretable labels (not arbitrary groupings)
- Temporal emergence ordering is monotone-plausible (older threads precede threads they seed)
- The top-cited paper within each cluster appears in David's mental model of the field's foundational works
- The influence hub table would be useful to someone writing a manual lit review on this topic

**Zeitgeist sub-test (informal):**
- Each cluster's in-degree distribution should be approximately scale-free (γ ∈ [1.5, 3.0])
- This is not a formal statistical test at this scale (56+neighbors is too small for robust power-law fitting), but it's a sanity check

**What failure looks like:**
- All 56 papers end up in one cluster (Leiden found no structure)
- Cluster labels are incoherent (e.g., papers from completely different topics share a cluster)
- The temporal curves are flat (no emergence signal — all threads active simultaneously)

---

## 7. What This Is NOT

- Not an automated survey writing tool — it does not generate narrative text
- Not a replacement for reading the papers — it structures them for human consumption
- Not a formal Zeitgeist validation — that experiment uses the full 709K corpus (see Zeitgeist validation plan)

This is a **proof-of-concept application** demonstrating that the citation-dynamics pipeline produces useful output when applied to a small, curated paper set. It motivates the synthesis stage as a practical tool.

---

## 8. Files to Create

```
citation-dynamics/
└── src/
    └── synthesis/
        ├── build_synthesis_subgraph.m    Extract 1-hop subgraph from DOI list
        ├── run_synthesis_pipeline.m      Top-level script: Leiden + temporal + SG-t-SNE
        └── generate_synthesis_report.m  Produce cluster map + temporal curves + Markdown report

citation-dynamics/
└── data/
    └── synthesis/
        └── k17-rgc-gold-dois.txt         Input: 56 recovered DOIs (one per line)

citation-dynamics/
└── outputs/
    └── synthesis/
        ├── k17-rgc-cluster-map.pdf
        ├── k17-rgc-temporal-curves.pdf
        └── k17-rgc-report.md
```

---

## 9. Prerequisites Before Coding

- [ ] Planner agent has returned sprint plan (defines order of implementation)
- [ ] Architect agent has returned data handoff design (defines format for subgraph export if Python is involved)
- [ ] This spec reviewed and agreed by David
- [ ] Gold DOI list extracted from LitDiscover traversal output (k17-rgc project)
- [ ] `citation-dynamics/src/synthesis/` directory created

---

## 10. Relationship to Zeitgeist Hypothesis

The synthesis pipeline is a downstream application of the core Zeitgeist hypothesis. If the hypothesis holds at scale (709K papers), we expect it to hold at the subgraph scale too:
- Each Leiden cluster within the 56-paper neighborhood should have approximately scale-free in-degree distribution
- The mixture of per-cluster distributions should reconstruct the subgraph's global distribution

This is an informal sanity check, not the main validation experiment. The formal Zeitgeist validation runs on the full corpus and is defined in the planner agent's sprint plan.
