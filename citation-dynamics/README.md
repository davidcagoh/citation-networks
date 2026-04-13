# Citation Dynamics

Research infrastructure for *Recognizing Signature Patterns and Phases of Time-Varying Networks* (David Goh, supervisor: Xiaobai Sun, September 2024).

## Research Goal

This project characterizes how information propagates through the APS physics citation corpus across time. The core intellectual contribution is the **Zeitgeist hypothesis**: the global citation distribution is a mixture of subcommunity distributions, each corresponding to a distinct research generation or school of thought, each individually scale-free.

Three planned contributions:
1. Extend spatial embedding and classification (SG-t-SNE, BlueRed spectral) to account for **time-dependent variation** in propagation patterns
2. Develop a **backward mapping** method to identify influential sources and their influenced followers
3. Introduce **quantitative characteristics** of propagation phases: emergence, growth, persistence, decay, transition

## Relationship to `lit-review/robust-literature-discovery`

These projects share the APS 2022 dataset and sit at adjacent stages of a pipeline:

```
citation-dynamics/       →   lit-review/robust-literature-discovery/
Understand structure         Exploit structure to discover papers
(Why does the graph          (Can we recover a topic's literature
 look like it does?)          from minimal seeds?)
                         →   [synthesis step — planned]
                             Apply community detection + temporal
                             phase analysis to the recovered set
                             to produce a structured lit review
```

The synthesis step (post-discovery) would draw directly on this project's methods: Leiden community detection, temporal window analysis, SG-t-SNE embedding, and backward influence mapping — applied not to the full corpus but to a discovered paper set.

## Data

Canonical APS 2022 dataset lives in `data/processed/`. The lit-review project symlinks to this location.

| File | Size | Contents |
|------|------|----------|
| `aps-dataset-citations-2022.csv` | 508 MB | Raw edge list (citing DOI → cited DOI) |
| `aps-2022-author-doi-citation-affil.mat` | 82 MB | Sparse matrices: C, B, D, E + metadata |
| `aps-2022-doi-citation.mat` | 33 MB | Minimal citation-only sparse matrix |
| `aps-2020-author-doi-citation.mat` | 39 MB | Earlier snapshot |

Coverage: 709,803 articles, 9,758,100 citations, 20 APS journals, 1893–2022.

## Structure

```
citation-dynamics/
├── src/
│   ├── parse/          # CSV → MATLAB sparse matrix compilation
│   ├── analysis/       # Graph characterization (distributions, temporal, spectral)
│   └── graph_select/   # Subgraph extraction utilities
├── utils/              # Query functions, Pareto analysis, distribution fitting
├── deps/               # External: SG-t-SNE, Leiden/igraph, BlueRed, Julia interface
├── data/
│   ├── processed/      # Canonical MAT files (canonical; lit-review symlinks here)
│   ├── raw/            # Optional full JSON archive
│   └── sample/         # Test datasets (1k node graph, BA synthetic)
├── notebooks/          # Exploratory Jupyter notebooks
├── writings/           # Research writing: abstract, lit review, thesis draft
├── config.py           # Path configuration (ROOT_DIR = os.getcwd())
└── setup.m             # MATLAB path setup
```

## Key Methods

- **SG-t-SNE** (`deps/+sgtsne/`): Stochastic graph t-SNE for embedding citation networks
- **BlueRed spectral** (`deps/+bluered/`, `src/analysis/blueRed_*.m`): Spectral analysis for community direction
- **Leiden algorithm** (`deps/+leiden/`): Community detection on citation subgraphs
- **Sliding window analysis** (`utils/analyze_citation_window.m`): Temporal slicing and per-window statistics
- **Pareto analysis** (`utils/pareto_*.m`): Hub concentration, Lorenz curves, Gini coefficients
- **Distribution fitting** (`src/analysis/fitDistribution.m`): Power-law, lognormal, Weibull, Pareto model comparison

## Status

Exploratory/infrastructure phase. The theoretical framing (Zeitgeist hypothesis, propagation phases) and data pipeline are in place. The embedding and community detection scripts exist but the full analysis loop connecting them to synthesis output has not been built.

See `writings/` for the research abstract, literature review (~50 papers), and thesis draft outline.
