# NST vs Time Curves vs SG-t-SNE: Method Comparison

Generated session 13, 2026-04-12 via research agent.

## TL;DR

These are NOT alternatives — they sit at different pipeline layers. Keep all three:

```
Citation DAG → NST (representation) → SG-t-SNE (spatial layout) → Time Curves (temporal trajectory)
```

This three-stage pipeline is novel: no published work was found combining NST + Time Curves for citation phase detection.

---

## What Each Method Actually Is

| Method | Type | Input | Output |
|---|---|---|---|
| **SG-t-SNE** | Graph visualization | Undirected stochastic matrix | 2D/3D node coordinates |
| **NST** | Representation learning | Weighted directed DAG | Spatial + temporal coords per node |
| **Time Curves** | Timeline visualization | Pairwise temporal distance matrix | 2D curve (loops=recurring phases, cusps=transitions) |

**SG-t-SNE** symmetrizes the DAG (loses edge direction). Temporal signal must be baked in upstream.
**NST** explicitly encodes edge directionality in a separate temporal coordinate. Universal distortion 1+O(log k).
**Time Curves** is pure visualization — needs precomputed per-snapshot similarity, no graph input.

---

## Recommended Pipeline

```
1. Citation DAG (APS, directed, timestamped)
       ↓
2. NST embedding  [NEW ADDITION]
   - Spatial coords per paper: subcommunity membership
   - Temporal coords per paper: causal ancestry score
   - Input: raw directed citation DAG (natively supported)
   - Repo: github.com/haitzsaezdeocariz/NeuralSpaceTimesICLR2025
   - OGBN-Arxiv demo exists → adaptable to APS in ~2-3 days
       ↓
3. SG-t-SNE on NST spatial coords  [KEEP, feeds from NST now]
   - 2D layout for visual cluster inspection
   - "Which papers cluster together?" answer
       ↓
4. Per-year centroid of NST/SG-t-SNE embeddings
   → T×T pairwise distance matrix (T ≈ 130 years of APS)
       ↓
5. Time Curves  [NEW ADDITION]
   - Folds timeline into 2D curve
   - Loops = recurring Zeitgeist phases
   - Cusps = sharp paradigm shifts
   - "How do phases evolve over time?" answer
```

---

## Experimental Design (2-week comparison)

**Days 1–2: Data setup**
- Use APS subset OR OGBN-Arxiv as proxy (has year labels, equivalent structure)
- Extract citation DAG; define 5-year or decade snapshots
- Compute backward-influence matrix (existing pipeline)

**Days 3–7: Experiment A — NST vs SG-t-SNE on subcommunity structure**
- Baseline: SG-t-SNE on backward-influence matrix (current)
- New: NST on raw citation DAG (use `arxiv_embedding/` demo as starting point)
- Metrics:
  - Spearman ρ: NST temporal coord vs. paper year (causal preservation)
  - Silhouette score: APS journal codes in 2D embedding (cluster purity)
  - Per-cluster power-law fit: does each cluster have scale-free in-degree? (Zeitgeist test)

**Days 8–12: Experiment B — Time Curves for phase trajectory**
- From SG-t-SNE: per-year centroid → T×T distance matrix
- From NST: per-year centroid → T×T distance matrix
- Feed both to Time Curves
- Check: do cusps align with known physics paradigm shifts?
- Check: do loops indicate recurring Zeitgeist patterns?

**Days 13–14: Evaluation**
| Metric | Measures |
|---|---|
| Temporal rank correlation | NST causal preservation |
| Cluster purity (APS journal codes) | Subcommunity detection quality |
| Phase transition sharpness (2nd deriv of curve) | Identifiable Zeitgeist transitions |
| Loop detection (self-intersection) | Recurring phase evidence |
| Per-cluster power-law exponent | Zeitgeist mixture hypothesis test |

---

## Implementation Notes

| Method | Language | Status | Notes |
|---|---|---|---|
| SG-t-SNE | C++/Julia/MATLAB | ✅ In codebase | `deps/+jl_interface/sgtsnepi.jl` |
| NST | Python (PyTorch) | ✅ Adapted + training | `src/phase3_nst_adapter.py`, `src/phase3_nst_train.py`; job 159670 on UofT cluster |
| Time Curves | Python (reimplemented) | ✅ Implemented | `src/phase4_timecurves.py`; proxy run verified; full run pending NST |

---

## What This Adds to the Thesis

1. **NST as representation layer**: gives causal-aware embeddings of citation DAG — directly tests whether citation networks have a latent linear time dimension (relevant to Zeitgeist). No prior work uses NST on APS data.
2. **Time Curves as trajectory visualization**: makes the "phases as loops" picture visually legible. Cusps = paradigm shifts, loops = recurring Zeitgeist patterns.
3. **Novel combination**: NST + Time Curves not found in any prior work. The three-stage pipeline is a new contribution.

---

## Sources
- Neural Spacetimes (Choudhary et al., ICLR 2025): arxiv.org/abs/2408.13885
- GitHub: github.com/haitzsaezdeocariz/NeuralSpaceTimesICLR2025
- Time Curves (Bach et al., IEEE TVCG 2015): ieeexplore.ieee.org/document/7192639
- GitHub: github.com/benjbach/timecurves
- SG-t-SNE-Π: github.com/fcdimitr/sgtsnepi
