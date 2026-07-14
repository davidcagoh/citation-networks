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

**Read research-roadmap.md for the standing cross-stage plan; decisions/open-questions are the
live files. Lineage construction lives in `litdiscover/lineages/` — three different methods run
over the same 27-paper corpus, see that table below.**

| File | Purpose |
|---|---|
| [litdiscover/research-roadmap.md](litdiscover/research-roadmap.md) | **Supersedes `background.md` (2026-07-14).** Cross-stage roadmap (Discovery/Extraction/Synthesis) — current bets, benchmark design; discovery detail split out (see next row) |
| [litdiscover/phase-discovery-roadmap.md](litdiscover/phase-discovery-roadmap.md) | Split out from research-roadmap.md (2026-07-14). Discovery-phase deep dive: current implementation, 27-method prior-art survey, operator inventory, **Experiment 1 — Cranfield-style gold standard, operator ablation/ordering/budget-normalized Pareto curves, paired significance testing**, simulation-vs-production gap |
| [litdiscover/phase-representation-roadmap.md](litdiscover/phase-representation-roadmap.md) | Split out from research-roadmap.md §3/Synthesis (2026-07-14). **Experiment 2 — does a structured-summary embedding organize a research field better than raw-text embeddings?** 4-condition clustering design against the 3 live surveys' section structure; framed as a representation-learning evaluation problem (retrieval → clustering → taxonomy-recovery → downstream-utility paradigm ladder) |
| [litdiscover/decisions.md](litdiscover/decisions.md) | Live: algorithm parameters, experiment design, paper structure, venue, full-text-verification audit trail for the 7 Tier 1/2 close-hit papers plus the 5-entry verification cohort |
| [litdiscover/open-questions.md](litdiscover/open-questions.md) | Live: open items, engine feature requests |
| [litdiscover/deep-dives.md](litdiscover/deep-dives.md) | Live: source doc — 22 full 6-field method deep-dives + Methods/Evaluation-Methods tables, mined from the 366-paper corpus beyond the original 7, plus a 5-entry verification cohort (SWIFT-Review, RobotSearch, ASReview, Elicit, ResearchRabbit) |

**`litdiscover/lineages/` — three lineage-construction methods over the same 27-paper corpus** (2026-07-13, prompted by catching Lineage E's structure was clustering-based, not citation-based):

| File | Method | Finding |
|---|---|---|
| [litdiscover/lineages/similarity-cluster.md](litdiscover/lineages/similarity-cluster.md) | **Deprecated 2026-07-13** — thematic clustering, kept unedited as the control condition in `lineage-comparison.md`, not a drafting source | Only 12/32 real citation edges represented; 3 drawn edges have no textual support |
| [litdiscover/lineages/explicit-citation-graph.md](litdiscover/lineages/explicit-citation-graph.md) | O(n) bottom-up — read each paper once, extract only what it explicitly states about others | 32 confirmed edges, ground truth for the other two methods |
| [litdiscover/lineages/implicit-pairwise-analysis.md](litdiscover/lineages/implicit-pairwise-analysis.md) | O(n²)-ish content-matching — date-ordered pairwise check of named limitations vs. later mechanisms | 10 new uncited-but-real edges (likely undercounted); unioned with the 32 explicit edges, 2 previously fully-isolated papers (ResearchRabbit, Scholar Augment) get pulled into the field's main connected structure |
| [litdiscover/lineages/lineage-comparison.md](litdiscover/lineages/lineage-comparison.md) | Worked example — ProfOlaf drawn all three ways | 6 real relationships total; no single method found more than half |

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

## Project status (2026-07-14)

**LitDiscover (solo):** ❌ Still desk-rejected by IP&M (2026-07-07), redo in progress. **IP&M resubmission checklist item 1 closed 2026-07-14:** `related-work.tex` re-read fresh against the actual desk-rejection wording ("leverage SOTA baselines, especially LLMs... reference the most updated articles from the current year") — confirmed addressed (6 papers from 2025-2026 cited). Both flagged "not independently verified" bib entries closed out: `Lau2025Elicit` had a real error (wrong author initial + missing DOI/volume/pages, fixed via PMC full-text verification), `Haryanto2024LLAssist` confirmed correct as-is. Recompiled clean, 21 pages, 0 errors.

**LitDiscover — discovery-phase Experiment 1: run live, real findings, now ⏸ paused (2026-07-14):**
Baselines/marginal-contribution/ablation ran live against all 3 surveys for the first time —
**co-citation is the standout non-traversal operator** (best precision of anything that fires,
10-29%; only operator with a nonzero ablation drop on every survey), while **embedding search,
venue expansion, and recency search show ~0% recall and ~0% precision on every survey, every
experiment** — reproducible, not noise. A follow-up composition/chaining attempt made things
*worse* (root-caused: unfiltered forward traversal + citation-count frontier selection → noisy
corpus → generic hub papers), and checking precision for the first time on the *original* system's
own 73-100%-recall validation found it implies **0.03-0.45% precision** (that eval never screens)
— likely relevant to how the IP&M submission frames its headline claim. Precision tracking, a
429-retry fix (root-caused against S2's actual docs, not guessed), and retry-trace logging were
added along the way. Experiment 1 is now marked **paused** in `phase-discovery-roadmap.md` (⏸ box
at the top of §4) rather than abandoned — real findings preserved, a redesign path
(budget-normalized comparison, §4.7, never built) scoped for whenever this resumes. See
`wiki/session-log.md` session 38 for the full account, including a mid-session file-clobber
incident (concurrent session) that was caught and reconstructed.

**LitDiscover — representation-learning research program, new 2026-07-14:** `phase-representation-roadmap.md` scopes Experiment 2 — does embedding a structured 6-field paper summary organize a field's papers better than embedding raw/lightly-processed text, motivated by `lineages/similarity-cluster.md`'s documented clustering failure. Framed around a representation-learning evaluation paradigm ladder (retrieval → clustering → taxonomy-recovery → downstream-utility), with the deeper hypothesis stated explicitly: discourse-structure-aware representations should organize a field better than raw-text ones. Section-level ground truth for the 3 live surveys (Ge21-HSS, K17-RGC, Le25-GLLM) is built and saved to `live-survey-eval/data/section-ground-truth/`. **Along the way, found and fixed a real gold-set data-quality bug**: 2-6 entries per survey (except Le25-GLLM) didn't correspond to any reference the survey actually cites — traced to S2's own `/references` endpoint linking malformed records, not this codebase's PDF parsing. Two automated content filters were tried and both reverted after live testing proved them net-harmful (they rejected far more real short/all-caps titles than actual garbage); the actual fix was manual, surgical removal of the confirmed-bad entries from `Ge21-HSS_gold.json` (202→200) and `K17-RGC_gold.json` (56→52). **Next:** recompute `phase-discovery-roadmap.md`'s live-survey recall numbers against the corrected gold-sets (stale, small expected effect), then resolve §5's remaining open decisions (full-text pooling, k-fixed-vs-elbow, flat-vs-hierarchical scoring) before building the actual embedding/clustering pipeline.

**LitDiscover the engine — repo restructured twice 2026-07-14:** `litdiscover/intake/` renamed to `litdiscover/discovery/` (all import references updated across the codebase + CLAUDE.md); the whole repo promoted from `lit-review/litdiscover` to sit directly at the `citation-networks` repo root (`.gitignore` updated accordingly — verified no relative-path/symlink dependencies broke). Otherwise unchanged: staged-by-default, autopilot opt-in (since 2026-07-09); `synthesize`'s citation-grounding check (`check_citation_grounding()`) still **not yet run against a real project** — still the top blocker for deciding whether the synthesis-stage redesign work is worth it. Still needed: bump + republish to PyPI (unchanged blocker, now several sessions old).

**LitDiscover wiki:** `wiki/litdiscover/` now has `research-roadmap.md` + `phase-discovery-roadmap.md` + `phase-representation-roadmap.md` (all new 2026-07-14, superseding `background.md`), `decisions.md`/`open-questions.md`/`deep-dives.md` (live, updated in place), and `lineages/` (three parallel lineage-construction methods, 2026-07-13). Flagged, still not decided: RLS is disabled on all 6 tables in the `litreview-v2` Supabase project (anon key has full read/write).

**`robust-literature-discovery` repo (2026-07-10):** ✅ Fully restructured, pushed. Deleted `inbox-papers/` and `app-validation-data/` (dead). Split into two self-contained tracks — `closed-corpus-eval/` and `live-survey-eval/`, each owning its own `scripts/` + `data/` (verified zero cross-track coupling by reading all 12 pipeline scripts in full). `closed-corpus-eval/scripts/` further split into `eval/` (6 scripts, produces every paper-claimed number/figure) and `sweep/` (5 scripts, parameter-justification only — 2 are dead/superseded). Explicit decision (2026-07-10, since superseded): the raw `included_366_2026-07-09.csv` snapshot was kept in the wiki rather than duplicated into `rld/` — deleted 2026-07-13 once its mining work was fully captured in `litdiscover/deep-dives.md`/`related-work-lineage.md` and the live Supabase table (`litreview-v2`) had moved past it (4,534 new pending candidates added since). `rld/drafts/refs.bib` remains the frozen paper-authoritative citation record.

**citation-dynamics / Zeitgeist (joint w/ Xiaobai):** ⚡ First full LNCS draft compiled — `writings/zeitgeist_paper.pdf`, 10 pages, 0 errors. User reviewing PDF. Repo is `github.com/davidcagoh/citation-dynamics` (private, promoted from `citation-networks` 2026-07-06). **Relevant to Synthesis below:** litdiscover's traversal stage now exports the same HDF5 citation-graph format this repo's `phase1_build_graph.py`/`phase2_leiden_cluster.py` already use — opens up citation-network-aware synthesis clustering as a future redesign (see litdiscover's session-log entry, 2026-07-07). Next: address review feedback, verify bibliography, then iterate toward submission.

**Synthesis:** On hold until Zeitgeist submitted. Identified (2026-07-08) as the piece where LitDiscover's new traversal-visualization export and Zeitgeist's potential HDP-based soft community resolution would actually combine — currently the most stalled part of the program despite being the connective tissue.

**Wiki / program framing (2026-07-08):** No code changes this session. Captured two strengtheners (LitDiscover traversal visualization, Zeitgeist HDP-based resolution) and two speculative future directions (4th citation motif "coupled fields," HDP as its detection method) in `concepts.md`. Wrote `research-program.md` — plain-language, collaborator-facing overview of the full pipeline with schematics. Ran an ad hoc Shapiro-Wilk test on Zeitgeist's 25 per-community γ_c values (W=0.919, p=0.047, right-skewed) — not yet reflected in the paper, flagged as a possible addition.
