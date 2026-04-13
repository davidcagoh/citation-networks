# LitDiscover Paper — Wiki Index

A living knowledge base for the paper. Updated by LLM; read in any order.
Each file is short by design — the goal is to hold the full argument in your head in one read.

**Start every session here, then go to [session-log.md](session-log.md) to see what was last done.**

---

## Wiki Files

| File | Purpose | Read when |
|---|---|---|
| [thesis.md](thesis.md) | The core argument in 400 words | Every session, first |
| [argument-map.md](argument-map.md) | Section → claim → evidence → figure | Before touching any figure or script |
| [figure-roles.md](figure-roles.md) | Per-figure: what it proves, filename, status, priority | Before running analysis scripts |
| [open-questions.md](open-questions.md) | Unresolved issues and blockers | When deciding what to work on next |
| [decisions.md](decisions.md) | Design choices made and why | Before changing any parameter |
| [simulation-vs-production.md](simulation-vs-production.md) | How APS simulation relates to production system | Before framing paper claims or touching production code |
| [session-log.md](session-log.md) | Reverse-chronological log of what was done each session | Start of every session |
| [codebase-map.md](codebase-map.md) | citation-dynamics/ directory tree, what's implemented vs stub | Before touching citation-dynamics code |
| [nst-timecurves-comparison.md](nst-timecurves-comparison.md) | NST vs Time Curves analysis; novel pipeline verdict | Before starting NST/TimeCurves implementation |

---

## Figures

Active pub figures: **fig1–fig7** (fig8/8b/8c and fig9a–d all DROPPED).

Publication figures: `../data-aps/outputs/pub_figures/`
Figure index (filenames): `../data-aps/outputs/pub_figures/FIGURE_INDEX.md`
Per-figure status, roles, and blockers: **[figure-roles.md](figure-roles.md)**

---

## One-line status (2026-04-12)

- **Thesis**: defined ✅
- **Paper name**: LitDiscover ✅ — "Robust Literature Discovery from Minimal Seeds: Validating LitDiscover on APS Citation Benchmarks and Live Surveys"
- **Key recall**: S1=89.2% (519/582), S2=98.4% (425/432), S3=96.9% (375/387)
- **Figures**: fig1 ✅, fig2 ✅, fig3 ✅, fig4 ✅, fig5 ✅, fig6 ✅, fig7 ✅, fig8/8b/8c ❌ DROPPED, fig9a–d ❌ DROPPED — final figure set is fig1–fig7
- **References**: 21 entries in bibliography.json ✅ — Elicit [17], ResearchRabbit [18], ConnectedPapers [19], Goldberg2015 [20], CiteAgent [21] added
- **Filter direction (scripts 03/05/08)**: out-degree on forward candidates — finalized ✅
- **Hyperparameter sweep (script 08)**: complete, 1980 rows ✅
- **Live experiment K17-RGC (Kahle 2017)**: ✅ COMPLETE — 100% recall (56/56), depth 2, round 1
- **Live experiment Ge21-HSS (Galesic 2021)**: ✅ COMPLETE — 100% recall (202/202), 2 rounds
- **Live experiment Le25-GLLM**: ✅ COMPLETE — 73.7% recall (42/57), 1 round, temporal gap
- **Venue**: not yet decided — see venue analysis below
- **Paper text**: rewrite complete ✅ (Abstract, §1, §2, §5, §9 rewritten; §3–§8 intact)
- **citation-dynamics/**: renamed from `thesis/`; README written; data deduplicated via symlink ✅
- **citation-dynamics/ SOTA gap**: NOT yet assessed — lit review is ~2 years old; Nakis 2024 was cutting edge then

## Next priorities

1. **[CITATION NEEDED] yellow-highlight locations** — user will check final PDF (Q11)
2. **Venue decision** — share with PI first; ICASR 2026 watch for call
3. **SOTA gap assessment for citation-dynamics** — search 2024–2026 for temporal citation phase analysis, community detection in citation graphs, LLM-based synthesis; is the Zeitgeist approach still novel?
4. **Figure fixes** — Q2 (k=5 or k=20 in miss analysis?), Q3 (non-monotone recall for contaminated seeds), Q7, Q8

## Venue analysis

See **[decisions.md — Venue](decisions.md)** for full ranking table.

**Short answer:** ICASR 2026 ⭐⭐⭐⭐ (watch for call), ALTARS workshop ⭐⭐⭐, JASIST journal ⭐⭐⭐. Post to arXiv first regardless.

---

## Key numbers to remember

| Survey | Gold refs | Recall (k=5, 2 rounds) | Notes |
|---|---|---|---|
| S1 (MIT, 1998) | 582 | 89.2% (519/582) | Older subfield, clustering issue |
| S2 (UCG, 2008) | 432 | 98.4% (425/432) | Clean convergence |
| S3 (TOPO, 2019) | 387 | 96.9% (375/387) | Clean convergence |

Canonical parameters: k=5 seeds, N_ROUNDS=2, PARETO_P=80, YIELD_THRESHOLD=0.05, K_ESCAPE=20.

Live results: K17-RGC — 100% recall (56/56), 1 seed, depth 2, corpus 31,168.
