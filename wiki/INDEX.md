# Citation Networks — Project Wiki

**Start every session:** read `session-log.md` → check the relevant project's `open-questions.md`.

**Presenting this program to someone new?** Read [research-program.md](research-program.md) first — narrative overview of all three pillars + the two speculative extensions, written for a potential collaborator.

---

## Thesis: Recognizing Signature Patterns and Phases of Time-Varying Networks

**Supervisor:** Xiaobai Sun | **Started:** Sept 2024

Formal thesis contributions:
1. Temporal embedding of citation networks
2. Backward influence mapping
3. Quantitative phase characterization

Three contributions, each with its own subdirectory:

| Contribution | Status | Target |
|---|---|---|
| [LitDiscover](litdiscover/) | Paper **desk-rejected by IP&M** (2026-07-07) — redo planned; engine on PyPI but **out of date** (v2.0.0 has a known bug, fixed locally 2026-07-07, not yet republished) | Information Processing & Management (redo) |
| [Zeitgeist / citation-dynamics](citation-dynamics/) | Active — §§1–4 figures done, §§1+8 rewrite next; **now its own repo** (`github.com/davidcagoh/citation-dynamics`) | COMPLEX NETWORKS 2026 (~Aug) |
| [Synthesis](synthesis/) | Subgraph built, on hold | Post-Zeitgeist thesis chapter |

---

## Global files (read across all projects)

| File | Purpose | Read when |
|---|---|---|
| [session-log.md](session-log.md) | What was done each session + UofT cluster SSH reference | Start of every session |
| [concepts.md](concepts.md) | Cross-cutting methodological ideas (metric families, distribution fitting) | When designing statistical validation |

---

## LitDiscover

| File | Purpose |
|---|---|
| [litdiscover/thesis.md](litdiscover/thesis.md) | Core claim, mechanism, what the paper does NOT claim |
| [litdiscover/argument-map.md](litdiscover/argument-map.md) | Section-by-section argument chain |
| [litdiscover/decisions.md](litdiscover/decisions.md) | Algorithm parameters, experiment design, paper structure, venue |
| [litdiscover/open-questions.md](litdiscover/open-questions.md) | Believed resolved; verify before submission |
| [litdiscover/figure-roles.md](litdiscover/figure-roles.md) | Per-figure argumentative role + status |
| [litdiscover/simulation-vs-production.md](litdiscover/simulation-vs-production.md) | APS simulation vs production system gap |
| [litdiscover/n-rounds-extension.md](litdiscover/n-rounds-extension.md) | Empirical sweep justifying N_ROUNDS=2 |

---

## citation-dynamics (Zeitgeist)

| File | Purpose |
|---|---|
| [citation-dynamics/decisions.md](citation-dynamics/decisions.md) | Venue, K_min scan, scope cuts, Python pipeline |
| [citation-dynamics/open-questions.md](citation-dynamics/open-questions.md) | §§1+8 rewrite, LaTeX table, uncertain labels |
| [citation-dynamics/codebase-map.md](citation-dynamics/codebase-map.md) | Pipeline status, directory tree, key results |
| [citation-dynamics/nst-timecurves-comparison.md](citation-dynamics/nst-timecurves-comparison.md) | NST vs SG-t-SNE vs Time Curves method anatomy (archived — not in paper scope) |

---

## Synthesis

| File | Purpose |
|---|---|
| [synthesis/experiment-spec.md](synthesis/experiment-spec.md) | K17-RGC Q-SYNTH pipeline spec |
| [synthesis/methods-comparison.md](synthesis/methods-comparison.md) | Leiden vs BlueRed + NST vs SG-t-SNE vs UMAP comparison plan |

---

## Project status (2026-07-07)

**LitDiscover (solo):** ❌ **Desk-rejected by IP&M** (2026-07-07): "not suitable for full review... several existing publications address this stage of research... leverage SOTA baselines and research, especially LLMs... reference the most updated articles from the current year, which you have not done." Reads as a scoping/currency problem (traversal set too shallow/dated), not a fundamental-idea problem. **Next: redo the underlying lit-review run** with SOTA/LLM-focused baselines and current-year references, once the engine is republished (see below).

**LitDiscover the engine:** ⚠ **PyPI v2.0.0 is out of date** — fixed a real bug 2026-07-07 (two embedding calls were silently 404ing: wrong model names for the Gemini OpenAI-compat endpoint) but haven't republished yet. Same session: added reviewable per-stage artifacts (`run` now exports a citation graph as HDF5 + full paper metadata as JSON; `extract` writes a markdown vetting report) and absorbed two standalone `.bib` scripts into the engine as DB-backed `forward-cites`/`verify` commands. Full plan at `~/.claude-main/plans/elegant-inventing-scroll.md`. **Next: bump + republish to PyPI before the paper redo**, then smoke-test the new commands against a real project.

**citation-dynamics / Zeitgeist (joint w/ Xiaobai):** ⚡ First full LNCS draft compiled — `writings/zeitgeist_paper.pdf`, 10 pages, 0 errors. User reviewing PDF. Repo is `github.com/davidcagoh/citation-dynamics` (private, promoted from `citation-networks` 2026-07-06). **Relevant to Synthesis below:** litdiscover's traversal stage now exports the same HDF5 citation-graph format this repo's `phase1_build_graph.py`/`phase2_leiden_cluster.py` already use — opens up citation-network-aware synthesis clustering as a future redesign (see litdiscover's session-log entry, 2026-07-07). Next: address review feedback, verify bibliography, then iterate toward submission.

**Synthesis:** On hold until Zeitgeist submitted.
