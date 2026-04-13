# Codebase Map: citation-dynamics/

Generated session 13, 2026-04-12 via Explore agent.

## Status Summary

**MATLAB-dominant** research infrastructure. Julia used only for SGtSNEpi embedding backend.

| Layer | Status |
|---|---|
| Data parsing (CSV/JSON → MAT) | ✅ Complete |
| Sparse matrix ops (sort, WCC, trim) | ✅ Complete |
| Statistics (degree, Gini, Pareto, power-law γ) | ✅ Complete |
| SG-t-SNE embedding (2D/3D via Julia SGtSNEpi) | ✅ Complete |
| BlueRed DT-II spectral clustering | ✅ Complete |
| Leiden community detection (MEX/igraph) | ✅ Complete |
| Temporal sliding windows + per-window metrics | ✅ Complete |
| Visualizations (animated embedding, cluster overlay, distributions) | ✅ Complete |
| **Phase detection (emergence/growth/decay model)** | ⚠️ Partial — tracking exists, quantitative model missing |
| **Backward influence mapping (dedicated pipeline)** | ⚠️ Partial — `query_XY_subgraph` enables it; full pipeline TBD |
| **Zeitgeist validation** (global = mixture of subcommunity distributions) | ❌ Not implemented |
| Aging/background outdegree model | ❌ Not implemented |

## Directory Tree (key files only)

```
citation-dynamics/
├── config.py                     Python path config
├── setup.m                       MATLAB path setup
├── src/
│   ├── parse/                    CSV/JSON → sparse MAT (7 files, all complete)
│   ├── analysis/
│   │   ├── main_window.m         Temporal window loop (198 lines) ← KEY
│   │   ├── main_window2.m        Revised version (222 lines) ← KEY
│   │   ├── blueRed_largestWCC.m  BlueRed on WCC
│   │   ├── showEmbedding.m       Animate 3D t-SNE through time (82 lines)
│   │   ├── cluster_dates_analysis.m  Track cluster emergence/decay
│   │   └── cluster_size_analysis.m   Cluster size distribution
│   └── graph_select/             Synthetic test graph loader
├── utils/
│   ├── analyze_citation_window.m  ← CORE: per-window degree/Gini/γ/Pareto
│   ├── query_XY_subgraph.m        ← CORE: cited/citing subgraph by date
│   ├── estimateStableParameter.m  Power-law exponent γ, λ
│   ├── compute_pareto_stats.m     Gini + Pareto ratios
│   ├── orderByDate.m              Sort C by publication date
│   ├── getLargestWCC.m            Extract largest WCC
│   └── show_highlight_embedding.m  Highlight cluster in 2D layout
├── deps/
│   ├── +sgtsne/     SG-t-SNE MATLAB implementation (9 files)
│   ├── +bluered/    BlueRed DT-II spectral (23 files) ← dtii.m is CORE
│   ├── +leiden/     Leiden MEX wrapper → igraph C++ (142-line cluster.m)
│   ├── +jl_interface/  Julia SGtSNEpi bridge (sgtsnepi.jl + sgtsnepi.m)
│   └── +utilities/  Math utils (modularity, isapprox)
├── data/
│   └── processed/   APS 2022: 709,803 articles, 9.76M citations
│       ├── aps-2022-author-doi-citation-affil.mat  (82 MB, C+B+D+E)
│       └── aps-2022-doi-citation.mat               (33 MB, C only)
└── writings/
    ├── Thesis Text.md              Full thesis outline Chapters 1-6
    ├── Literature Review_*.md      ~50 paper survey
    └── Year by Year.md             Temporal statistics summary
```

## Core Algorithm Signatures

```matlab
% Temporal window: extract subgraph + stats
[C_sub, doi_cited, doi_citing, ...] = query_XY_subgraph(C, doi, pubDate, t1, t2, t3, t4)
[num_cited, num_citing, intra, avg_in, avg_out, gini, gamma, lambda, pareto] = analyze_citation_window(C, paretoParameter)

% Power-law exponent
[gamma, lambda_est] = estimateStableParameter(C)
[slope, intercept] = regionFit(logX, logY, 'range')  % robust log-log fit

% Embedding
y = sgtsne.embed(P, labels, no_dims, opt)    % SG-t-SNE (MATLAB backend)
% OR: deps/+jl_interface/sgtsnepi.m → Julia SGtSNEpi

% Clustering
categories = runBlueRed(C, gname)            % BlueRed spectral
[cid, qq] = leiden.cluster(A, func, opt)    % Leiden community detection

% BlueRed core
[cid_f, ha_f, hr_f, ...] = dtii(A, strfunc, opt)   % Descending Triangulation II
```

## Data Format

- `C`: sparse n×n, C(i,j) = paper j cites paper i (indegree on rows)
- `pubDate`: string array 'YYYY-MM-DD'
- `doi`: cell array of strings

## What the Thesis Needs Next

The three claimed contributions and their implementation status:
1. **Temporal embedding** → ✅ SG-t-SNE via SGtSNEpi working
2. **Backward influence mapping** → ⚠️ `query_XY_subgraph` exists but no dedicated pipeline
3. **Quantitative phase characterization** → ❌ core gap — cluster tracking exists but no emergence/growth/decay model

The **Zeitgeist validation experiment** (global distribution = mixture of subcommunity distributions) is the missing empirical centrepiece. It requires: temporal window → Leiden clusters → per-cluster power-law fit → mixture decomposition test.
