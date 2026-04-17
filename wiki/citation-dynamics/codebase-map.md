# Codebase Map: citation-dynamics/

Last updated: session 21, 2026-04-16.

## Pipeline Status

| Phase | Script | Status | Output |
|---|---|---|---|
| 1 — HDF5 build | `src/phase1_build_graph.py` | ✅ | `data/exported/aps-2022-citation-graph.h5` |
| 2 — Leiden full corpus | `src/phase2_leiden_cluster.py` | ✅ | `data/exported/aps-2022-leiden-1p00.npz` |
| 2b — Zeitgeist fitting | `src/phase2b_zeitgeist_fit.py` | ✅ | `data/analysis/zeitgeist_community_fits.csv` |
| 3 — NST training | `src/phase3_nst_train.py` | 🔄 cluster job 159670 | `data/exported/aps-nst-model.pt` + `aps-nst-embeddings.npy` |
| 4 — Time Curves | `src/phase4_timecurves.py` | ⏳ awaits Phase 3 | `data/analysis/timecurves_nst_result.npz` |
| 5 — Synthesis subgraph | `src/phase5_synthesis_subgraph.py` | ✅ | `data/synthesis/k17-rgc-subgraph.npz` |

Run everything: `make -f citation-dynamics/Makefile all`

## MATLAB-only components (not ported)

| Component | Files | Status |
|---|---|---|
| SG-t-SNE embedding | `deps/+sgtsne/`, `deps/+jl_interface/` | ✅ Working (Julia bridge) |
| BlueRed DT-II spectral | `deps/+bluered/` (23 files, `dtii.m` core) | ✅ Working |
| Temporal window analysis | `utils/analyze_citation_window.m`, `utils/query_XY_subgraph.m` | ✅ Working |
| Backward influence interface | `src/analysis/showEmbedding.m` | ⚠️ Exists, no standalone pipeline |

BlueRed stays MATLAB-only — ~20 files, no Python equivalent, not worth porting for paper scope.

## Directory Tree (key files)

```
citation-dynamics/
├── Makefile                          Pipeline orchestration
├── train_cluster.slurm               UofT cluster job (gpunodes)
├── src/
│   ├── phase1_build_graph.py         CSV+JSON → HDF5
│   ├── phase2_leiden_cluster.py      Full-corpus Leiden
│   ├── phase2b_zeitgeist_fit.py      Per-community power-law fitting
│   ├── phase3_nst_adapter.py         APS→NST data adapter
│   ├── phase3_nst_train.py           NST training + embedding export
│   ├── phase4_timecurves.py          Time Curves (SMACOF + cusp/loop detection)
│   ├── phase5_synthesis_subgraph.py  K17-RGC 1-hop subgraph
│   └── load_aps.py                   HDF5 loader utility
├── deps/
│   ├── +bluered/                     BlueRed DT-II (MATLAB, 23 files)
│   ├── +sgtsne/, +jl_interface/      SG-t-SNE via Julia SGtSNEpi
│   ├── +leiden/                      Leiden MEX wrapper
│   └── nst/arxiv_embedding/          NST source (neural_spacetime.py, layers.py)
├── data/
│   ├── processed/                    Raw MAT files (82MB+33MB, gitignored)
│   ├── exported/                     HDF5, Leiden NPZ, NST outputs (gitignored)
│   ├── synthesis/                    K17-RGC subgraph files (gitignored)
│   └── analysis/                     Zeitgeist fits, Time Curves outputs (gitignored)
└── writings/
    ├── paper_draft_sections.md       Paper outline (§§1–8)
    └── Thesis Text.md                Original thesis chapter outline
```

## Key data formats

- HDF5: `/edge_row` int32[E], `/edge_col` int32[E], `/year` float32[N], `/doi` bytes[N]
- Leiden NPZ: `membership` int32[N], `modularity` float, `n_communities` int
- NST embeddings NPZ: `coords` float32[N, space_dim+time_dim], `doi`, `year`, `membership`
- Time Curves NPZ: `coords` float32[T,2], `years` int[T], `cusps` int[], `loops` int[L,2]

## Core key results (APS 2022)

- N=709,803 papers, L=9,833,191 citations, 1893–2022
- Leiden: 446 communities, Q=0.7883; 25 major communities (≥30 nodes) cover 99.8% of papers
- Zeitgeist: γ_c ∈ [2.099, 3.268], mean=2.50, std=0.246; 100% pass KS test; 68% have year IQR<20y
- K17-RGC subgraph: 90 nodes (2 gold APS + 88 neighbors), 7 communities, Q=0.4291; 49/51 gold DOIs are non-APS
