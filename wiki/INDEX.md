# Citation Networks — Project Wiki

**Start every session:** read `session-log.md` → check the relevant project's `open-questions.md`.

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
| [LitDiscover](litdiscover/) | Complete (venue pending) | ICASR 2026 |
| [Zeitgeist / citation-dynamics](citation-dynamics/) | Active — §§1–4 figures done, §§1+8 rewrite next | COMPLEX NETWORKS 2026 (~Aug) |
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

## Project status (2026-04-21)

**LitDiscover:** ⚡ JCDL 2026 submission filed (EasyChair). PDF: 9 pages, ACM sigconf, anonymous, 300 DPI figures. Deadline June 30. Next: send to PI Xiaobai (~June 8), get her ORCID, verify JCDL city.

**citation-dynamics:** §§1–4 complete with figures (γ_global=2.74, 25 communities, γ_c ∈ [2.1, 3.3], 100% KS pass). Next: rewrite §§1+8, LaTeX §4 table.

**Synthesis:** K17-RGC subgraph built (90 nodes, 7 communities). On hold until Zeitgeist paper submitted. Caveat: 49/51 gold DOIs are non-APS.
