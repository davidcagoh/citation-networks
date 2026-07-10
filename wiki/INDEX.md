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
| [concepts.md](concepts.md) | Cross-cutting methodological ideas (metric families, distribution fitting, citation motifs, HDP, traversal visualization) | When designing statistical validation or scoping future work |
| [research-program.md](research-program.md) | Plain-language narrative overview of all three pillars + two speculative extensions | Sharing the program with a collaborator |

---

## LitDiscover

**Read background.md once for context; decisions/open-questions/related-work-landscape are the live files.**

| File | Purpose |
|---|---|
| [litdiscover/background.md](litdiscover/background.md) | Read-once: core thesis/claim, sim-vs-production gap, pre-rejection paper structure (argument map + figure roles) |
| [litdiscover/decisions.md](litdiscover/decisions.md) | Live: algorithm parameters, experiment design, paper structure, venue |
| [litdiscover/open-questions.md](litdiscover/open-questions.md) | Live: open items, engine feature requests |
| [litdiscover/related-work-landscape.md](litdiscover/related-work-landscape.md) | Live: SOTA/close-hit competitor comparison table (motivation/scope/architecture/evaluation), driving the IP&M redo's Related Work section |

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

## Project status (2026-07-10)

**LitDiscover (solo):** ❌ Desk-rejected by IP&M (2026-07-07) for missing SOTA/LLM baselines and current-year references. **Actively being redone:** `automated-lit-review-methodology` reset and re-seeded with 8 fresh SOTA/2025-2026 anchors, traversed, prefiltered, and hand-eyeballed (366 included / 344 excluded / 147 still pending) directly against the rejection's stated gaps. All 366 included papers pulled and analyzed — 15 genuine close-hit competitor systems identified and now have a full tiered motivation/scope/architecture/evaluation comparison table (`litdiscover/related-work-landscape.md`), directly feeding the redo's Related Work section. Not yet re-extracted/re-synthesized — blocked on the Gemini spend cap (check ai.studio/spend) and another `traverse` cycle from the enlarged included set. Not yet decided: full PDFs vs. abstracts-only for the 7 Tier 1/2 papers.

**LitDiscover the engine:** ✅ Reworked to staged-by-default, autopilot opt-in (2026-07-09) — `run` now performs one traversal cycle and stops by default; LLM screening only fires via deliberate `screen`/`mark`/`prefilter` calls, never automatically. New commands: `traverse`, `screen`, `prefilter`, `mark`, `related-work-mine`. `watchdog.py` retired in code; host-side launchd job fully torn down (2026-07-10). 174 tests passing, merged to `main` (not yet republished to PyPI — still v2.0.0). Two real bugs found and fixed via the redo run (related-work section-heading false-positive; prefilter term-derivation leak). Still needed: bump + republish to PyPI.

**LitDiscover wiki:** `wiki/litdiscover/` consolidated 8 files → 4 to stop report-accumulation — `background.md` (read-once: thesis, sim-vs-production, pre-rejection paper structure), `decisions.md`/`open-questions.md`/`related-work-landscape.md` (live, updated in place). Flagged, not yet decided: RLS is disabled on all 6 tables in the `litreview-v2` Supabase project (anon key has full read/write).

**`robust-literature-discovery` repo (2026-07-10):** ✅ Fully restructured, pushed. Deleted `inbox-papers/` and `app-validation-data/` (dead). Split into two self-contained tracks — `closed-corpus-eval/` and `live-survey-eval/`, each owning its own `scripts/` + `data/` (verified zero cross-track coupling by reading all 12 pipeline scripts in full). `closed-corpus-eval/scripts/` further split into `eval/` (6 scripts, produces every paper-claimed number/figure) and `sweep/` (5 scripts, parameter-justification only — 2 are dead/superseded). Explicit decision: `wiki/litdiscover/included_366_2026-07-09.csv` stays in the wiki only, not duplicated into `rld/` — wiki is the living research artifact, `rld/drafts/refs.bib` is the frozen paper-authoritative citation record.

**citation-dynamics / Zeitgeist (joint w/ Xiaobai):** ⚡ First full LNCS draft compiled — `writings/zeitgeist_paper.pdf`, 10 pages, 0 errors. User reviewing PDF. Repo is `github.com/davidcagoh/citation-dynamics` (private, promoted from `citation-networks` 2026-07-06). **Relevant to Synthesis below:** litdiscover's traversal stage now exports the same HDF5 citation-graph format this repo's `phase1_build_graph.py`/`phase2_leiden_cluster.py` already use — opens up citation-network-aware synthesis clustering as a future redesign (see litdiscover's session-log entry, 2026-07-07). Next: address review feedback, verify bibliography, then iterate toward submission.

**Synthesis:** On hold until Zeitgeist submitted. Identified (2026-07-08) as the piece where LitDiscover's new traversal-visualization export and Zeitgeist's potential HDP-based soft community resolution would actually combine — currently the most stalled part of the program despite being the connective tissue.

**Wiki / program framing (2026-07-08):** No code changes this session. Captured two strengtheners (LitDiscover traversal visualization, Zeitgeist HDP-based resolution) and two speculative future directions (4th citation motif "coupled fields," HDP as its detection method) in `concepts.md`. Wrote `research-program.md` — plain-language, collaborator-facing overview of the full pipeline with schematics. Ran an ad hoc Shapiro-Wilk test on Zeitgeist's 25 per-community γ_c values (W=0.919, p=0.047, right-skewed) — not yet reflected in the paper, flagged as a possible addition.
