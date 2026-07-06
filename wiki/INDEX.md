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
| [LitDiscover](litdiscover/) | **Submitted** (2026-07-06) | Information Processing & Management |
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

## Project status (2026-07-06)

**LitDiscover (solo):** ✅ **Submitted to Information Processing & Management** (2026-07-06), via Elsevier's Editorial Manager. Venue odyssey in one day: JCDL 2026 deadline (June 30) missed → reformatted for JASIST → switched to ACM TOIS (best acceptance/turnaround stats) → **TOIS abandoned** after discovering its ~20-page minimum (paper is a focused 12pp) → **IP&M**, chosen on genuine content fit rather than stats. Submitted with cover letter, anonymized manuscript, title page, and highlights (IP&M uses anonymized review — discovered mid-submission and handled). Repo (`github.com/davidcagoh/robust-literature-discovery`, now with an MIT license) linked as "Original data," pushed and in sync with what reviewers see. Dead-end drafts (JCDL, JASIST, TOIS) archived in `paper-drafts/archive/`. **Xiaobai Sun dropped as co-author** for this paper (no contribution; her work still cited). Next: nothing — awaiting IP&M's decision (~5–6mo typical first-decision turnaround).

**citation-dynamics / Zeitgeist (joint w/ Xiaobai):** ⚡ First full LNCS draft compiled — `writings/zeitgeist_paper.pdf`, 10 pages, 0 errors. User reviewing PDF. Next: address review feedback, verify bibliography, then iterate toward submission.

**Synthesis:** On hold until Zeitgeist submitted.
