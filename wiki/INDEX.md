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

**Read background.md once for context; decisions/open-questions are the live files. Lineage
construction now lives in `litdiscover/lineages/` — three different methods run over the same
27-paper corpus, see that table below.**

| File | Purpose |
|---|---|
| [litdiscover/background.md](litdiscover/background.md) | Read-once: core thesis/claim, sim-vs-production gap, pre-rejection paper structure (argument map + figure roles) |
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

## Project status (2026-07-13)

**LitDiscover (solo):** ❌ Still desk-rejected by IP&M (2026-07-07), redo in progress. **Related-work research restructured 2026-07-13:** all 22 genuine LLM-native close-hit method papers (7 Tier 1/2 originals + 15 mined from the 366-paper CSV) plus a 5-paper verification cohort have full 6-field deep-dives (`litdiscover/deep-dives.md`). The original narrative "who-answers-whom" lineage (`litdiscover/lineages/similarity-cluster.md`) was audited, found to represent only 12 of 32 real citation edges (thematic-bucket structure was silently dropping cross-lineage citations), and **deprecated** rather than rebuilt — rebuilding it would either duplicate the two rigorous methods built alongside it or keep forcing a bucket shape twice shown to be wrong for this corpus (a 19–21 node giant component, not six lineages). Paper prose now drafts directly from `explicit-citation-graph.md` (32 confirmed edges, ground truth) and `implicit-pairwise-analysis.md` (10 more uncited-but-real edges, richest signal) — already done for `related-work.tex`'s rewritten "Automated systematic review" paragraph, now ProfOlaf-centered (it implicitly answers 3 other papers' named gaps while still lacking citation-graph traversal + validated recall). Separately, `related-work.tex`'s citations were audited too: SWIFT-Review's DOI was fabricated (pointed to an unrelated paper) and RobotSearch was cited to the wrong Marshall/Wallace paper — both fixed. Separately, `automated-lit-review-methodology`'s pending queue has **4,534 candidates awaiting `prefilter`** (not yet run) after a traversal cycle on the enlarged 390-included set — held per the new prefilter-before-screen discipline (see decisions.md), not blocked on spend anymore.

**LitDiscover the engine:** ✅ Staged-by-default, autopilot opt-in (unchanged since 2026-07-09). New this session: `traverse` prints a running `(i/N)` progress counter (was silent before, caught live when a 4,534-candidate cycle gave no sense of progress); `synthesize` now runs a diagnostic citation-grounding check by default (`check_citation_grounding()`, precision-only, writes `<slug>_grounding_report.md`, `--skip-grounding-check` to opt out) — built from the extract/synthesize technique audit's #1 finding, **not yet run against a real project**, so the actual grounding number is still unmeasured. 181 tests passing (was 174). Still needed: bump + republish to PyPI (unchanged blocker, now several sessions old).

**LitDiscover wiki:** `wiki/litdiscover/` now has `background.md` (read-once), `decisions.md`/`open-questions.md`/`deep-dives.md` (live, updated in place) plus a new `lineages/` subdirectory (2026-07-13) holding the three parallel lineage-construction methods — see the table above. `related-work-landscape.md` deleted 2026-07-13 — its full-text-verification audit trail was folded into `decisions.md`, and its paper coverage is a subset of `deep-dives.md`. `included_366_2026-07-09.csv` also deleted the same day (see below). Also cloned `sr-lab/ProfOlaf` and `lira-workflow/auto-review-writing` into `lit-review/` (gitignored, reference-only) to ground the audit in actual code — this is what caught the LiRA/CQF1 correction (offline metric, not live check). Flagged, still not decided: RLS is disabled on all 6 tables in the `litreview-v2` Supabase project (anon key has full read/write).

**`robust-literature-discovery` repo (2026-07-10):** ✅ Fully restructured, pushed. Deleted `inbox-papers/` and `app-validation-data/` (dead). Split into two self-contained tracks — `closed-corpus-eval/` and `live-survey-eval/`, each owning its own `scripts/` + `data/` (verified zero cross-track coupling by reading all 12 pipeline scripts in full). `closed-corpus-eval/scripts/` further split into `eval/` (6 scripts, produces every paper-claimed number/figure) and `sweep/` (5 scripts, parameter-justification only — 2 are dead/superseded). Explicit decision (2026-07-10, since superseded): the raw `included_366_2026-07-09.csv` snapshot was kept in the wiki rather than duplicated into `rld/` — deleted 2026-07-13 once its mining work was fully captured in `litdiscover/deep-dives.md`/`related-work-lineage.md` and the live Supabase table (`litreview-v2`) had moved past it (4,534 new pending candidates added since). `rld/drafts/refs.bib` remains the frozen paper-authoritative citation record.

**citation-dynamics / Zeitgeist (joint w/ Xiaobai):** ⚡ First full LNCS draft compiled — `writings/zeitgeist_paper.pdf`, 10 pages, 0 errors. User reviewing PDF. Repo is `github.com/davidcagoh/citation-dynamics` (private, promoted from `citation-networks` 2026-07-06). **Relevant to Synthesis below:** litdiscover's traversal stage now exports the same HDF5 citation-graph format this repo's `phase1_build_graph.py`/`phase2_leiden_cluster.py` already use — opens up citation-network-aware synthesis clustering as a future redesign (see litdiscover's session-log entry, 2026-07-07). Next: address review feedback, verify bibliography, then iterate toward submission.

**Synthesis:** On hold until Zeitgeist submitted. Identified (2026-07-08) as the piece where LitDiscover's new traversal-visualization export and Zeitgeist's potential HDP-based soft community resolution would actually combine — currently the most stalled part of the program despite being the connective tissue.

**Wiki / program framing (2026-07-08):** No code changes this session. Captured two strengtheners (LitDiscover traversal visualization, Zeitgeist HDP-based resolution) and two speculative future directions (4th citation motif "coupled fields," HDP as its detection method) in `concepts.md`. Wrote `research-program.md` — plain-language, collaborator-facing overview of the full pipeline with schematics. Ran an ad hoc Shapiro-Wilk test on Zeitgeist's 25 per-community γ_c values (W=0.919, p=0.047, right-skewed) — not yet reflected in the paper, flagged as a possible addition.
