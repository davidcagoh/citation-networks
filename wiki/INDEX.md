# Citation Networks — Project Wiki

**Start every session:** read `session-log.md` → check the relevant project's `open-questions.md`.

**Presenting this program to someone new?** Read [research-program.md](research-program.md) first — narrative overview of all three pillars + the two speculative extensions, written for a potential collaborator.

**Repo layout note (2026-07-14):** the actual `litdiscover` codebase, the 14 cloned reference
systems, `deep-dives.md`, and the source PDFs (`fulltext/` → `reference-pdfs/`) all now live under
`lit-review-bot/` at the repo root (`lit-review-bot/litdiscover/`, `lit-review-bot/reference-systems/`,
`lit-review-bot/reference-systems/deep-dives.md`, `lit-review-bot/reference-systems/reference-pdfs/`)
— not deleted, confirmed via directory listing. `lit-review-bot/` is the shell folder for the
LitDiscover engine, the reference-systems corpus, and the RLD paper together; the wiki keeps its
own research/decisions docs separately in `wiki/litdiscover/` as before.

**Repo admin (2026-07-14, session 43):** `citation-dynamics` GitHub repo renamed to `zeitgeist`
(local clone's remote repointed); `automated-lit-reviews` deleted from GitHub (`deprecated-bot/`
keeps a local-only copy, its own `origin` now points at a dead URL); June-24 (Mohammed Junaid
Anwar) invited as a Write collaborator on `citation-networks`. Root and per-project READMEs
(`citation-networks`, `lit-review-bot/`, `litdiscover`, `paper`, `zeitgeist`) audited against
actual code/wiki state and fixed where stale — see session 43 below for the full list, including
a real broken symlink the rename caused. `forward_cites.py`/`verify_refs.py` moved from repo root
into `utils/` (see `utils/README.md`).

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
| [LitDiscover](litdiscover/) | Paper **desk-rejected by IP&M** (2026-07-07) — redo planned; engine on PyPI but **out of date**. Discovery/screening evaluation redesigned 2026-07-14 around an end-to-end recall/precision metric (§4.0 of `discovery-roadmap.md`), after isolated-stage numbers proved indefensible on their own | Information Processing & Management (redo) |
| [Zeitgeist](zeitgeist/) | Active — §§1–4 figures done, §§1+8 rewrite next; **its own repo** (`github.com/davidcagoh/citation-dynamics`, local clone renamed `zeitgeist/`) | COMPLEX NETWORKS 2026 (~Aug) |
| [Synthesis](synthesis/) | Refactored 2026-07-14 into 3 tracks (see `synthesis/roadmap.md`); K17-RGC gold set verified, pipeline not yet run | Post-Zeitgeist thesis chapter |

---

## Global files (read across all projects)

| File | Purpose | Read when |
|---|---|---|
| [session-log.md](session-log.md) | What was done each session + UofT cluster SSH reference | Start of every session |
| [concepts.md](concepts.md) | Cross-cutting methodological ideas (metric families, distribution fitting, citation motifs, HDP, traversal visualization) | When designing statistical validation or scoping future work |
| [research-program.md](research-program.md) | Plain-language narrative overview of all three pillars + two speculative extensions | Sharing the program with a collaborator |

---

## LitDiscover

**Read `research-roadmap.md` for the standing cross-stage plan; `decisions.md`/`open-questions.md`
are the live files.** Discovery + screening research (`discovery-roadmap.md`,
`corpus-curation-prior-art.md`) lives flat in this directory, not a subfolder — it was briefly
promoted to a top-level `wiki/discovery/` study on 2026-07-14, then folded back the same day: the
promotion made sense in isolation (§4.0's redesign genuinely turned it into a rigorous
investigation), but discovery + screening *is* LitDiscover's core identity, unlike Synthesis
(which draws on Zeitgeist's own graph-analysis machinery and is a genuinely separable
corpus-structuring add-on — that's why Synthesis stayed promoted, see below).

| File | Purpose |
|---|---|
| [litdiscover/research-roadmap.md](litdiscover/research-roadmap.md) | **Supersedes `background.md` (2026-07-14).** Cross-stage roadmap (Discovery/Extraction/Synthesis) — current bets, benchmark design |
| [litdiscover/discovery-roadmap.md](litdiscover/discovery-roadmap.md) | **Start here for discovery/screening.** §1 implementation audit (current engine, the eval-code's three tiers of production-integration), §2 prior-art survey (27 methods, by discovery mechanism family), §3 the two-mechanism bet, **§4.0 — the methodological principle (isolated-stage recall/precision isn't defensible) + primary end-to-end experiment design + "ironclad/defensible" checklist**, §4.1-§4.11 — operator-level ablation/ordering/budget work (diagnostic-only, not the headline), §5 simulation-vs-production gap, §7 open decisions (step 0 = build the §4.0 harness, ahead of anything else) |
| [litdiscover/corpus-curation-prior-art.md](litdiscover/corpus-curation-prior-art.md) | Companion to `deep-dives.md` (see below for its actual location), re-cut around one question: how does each surveyed system discover *and screen* its corpus? Comparison table (discovery mechanism / screening mechanism / stopping criterion / screening validated?) across all 27+5 methods, grouped analysis, and a "what this means for LitDiscover" section — also where the mature-eval-standard finding lives (CLEF TAR/SYNERGY is mature for screening-in-isolation, decades-old relative-recall methodology exists for discovery-in-isolation, but nobody validates the two *together* against a citation-traversal-fed queue — the exact gap §4.0 closes) |
| [../lit-review-bot/litdiscover/litdiscover/discovery/README.md](../lit-review-bot/litdiscover/litdiscover/discovery/README.md) | Lives next to the code it documents rather than in the wiki. Reference doc (not research framing) for how `litdiscover/discovery/` actually works: module map, the `OperatorResult` contract, all 7 operators, the `GraphSource` protocol/`S2Source`/`ClosedCorpusSource`, rate limiting + budget accounting, and what the CLI actually calls vs. what's research-only |
| [litdiscover/decisions.md](litdiscover/decisions.md) | Live: algorithm parameters, experiment design, paper structure, venue, full-text-verification audit trail, the §4.0 methodological-principle decision entry |
| [litdiscover/open-questions.md](litdiscover/open-questions.md) | Live: open items, including discovery/screening-specific ones (pre-submission recall figures, Groq screening-backend gap, gold-set data-quality bug) folded back in alongside the general-engine ones |
| [../lit-review-bot/reference-systems/deep-dives.md](../lit-review-bot/reference-systems/deep-dives.md) | Lives with the reference-systems corpus it documents, not in the wiki. Source doc — 22 full 6-field method deep-dives + Methods/Evaluation-Methods tables, mined from the 366-paper corpus, plus a 5-entry verification cohort and SurveyLens. Source PDFs at `../lit-review-bot/reference-systems/reference-pdfs/` |

---

## Zeitgeist

**Wiki folder renamed `citation-dynamics/` → `zeitgeist/` (2026-07-14) to match the local code
clone's rename** (repo itself is still `github.com/davidcagoh/citation-dynamics` on GitHub).

| File | Purpose |
|---|---|
| [zeitgeist/decisions.md](zeitgeist/decisions.md) | Venue, K_min scan, scope cuts, Python pipeline |
| [zeitgeist/open-questions.md](zeitgeist/open-questions.md) | §§1+8 rewrite, LaTeX table, uncertain labels |
| [zeitgeist/codebase-map.md](zeitgeist/codebase-map.md) | Pipeline status, directory tree, key results |
| [zeitgeist/nst-timecurves-comparison.md](zeitgeist/nst-timecurves-comparison.md) | NST vs SG-t-SNE vs Time Curves method anatomy (archived — not in paper scope) |

---

## Synthesis

**Refactored 2026-07-14 into a single entry point + three protocol tracks. Read
[synthesis/roadmap.md](synthesis/roadmap.md) first** — it states the goal, each track's real
status, and the one next action per track, so nothing below needs re-deriving that.

| File | Purpose |
|---|---|
| [synthesis/roadmap.md](synthesis/roadmap.md) | **Start here.** Goal, three-track status table, immediate next action per track, what "rigor" means before any track counts as a real result |
| [synthesis/q-synth-plan.md](synthesis/q-synth-plan.md) | Graph-native track — K17-RGC pipeline (Leiden + power-law + embedding), the Leiden-vs-BlueRed and NST-vs-UMAP-vs-SG-t-SNE method comparisons, success criteria, blocking prerequisites. Merged from the former `experiment-spec.md` + `methods-comparison.md` |
| [synthesis/representation-learning-plan.md](synthesis/representation-learning-plan.md) | Embedding-native track (formerly `litdiscover/phase-representation-roadmap.md`) — does a structured 6-field summary embed better for clustering than raw text? 4-condition design; ground truth built, pipeline not yet run, 3 open design decisions before it can be |
| [synthesis/example-comparison/](synthesis/example-comparison/) | LLM-text-native track, **complete as a control condition** — three methods run over the same 27-paper corpus; still LitDiscover's own related-work-drafting source, grouped here because it's a disjoint corpus-structuring protocol, not because it stopped serving that role. Renamed from `background/lineages/` (2026-07-14) |
| [synthesis/background/reference-implementation-survey.md](synthesis/background/reference-implementation-survey.md) | Code-grounded (not paper-text) audit of 14 cloned reference systems: embedding/clustering choices, synthesis-mechanism deep-dives, paper-vs-code fidelity gaps (SurveyX's "attribute forest" doesn't exist in code, SurveyGen's re-ranking formula doesn't match its stated coefficients, InteractiveSurvey's clustering variable is named `hdbscan_model` but instantiates `AgglomerativeClustering`), plus each system's paper-reported eval/results |
| [synthesis/background/eval-standard-gap.md](synthesis/background/eval-standard-gap.md) | Is there a mature eval standard for synthesis quality across the LLM-narrative-generation corpus? No — converged-but-unvalidated (AutoSurvey's citation-NLI + LLM-judge rubric reused everywhere, but ρ≈0.54 against human judgment and no shared benchmark); the "synthesis"/"critical analysis" axis specifically has no validated instrument anywhere in the corpus |

**`synthesis/example-comparison/` — three LLM-text-native corpus-structuring methods:**

| File | Method | Finding |
|---|---|---|
| [similarity-cluster.md](synthesis/example-comparison/similarity-cluster.md) | **Deprecated 2026-07-13** — thematic clustering, kept unedited as the control condition in `lineage-comparison.md`, not a drafting source | Only 12/32 real citation edges represented; 3 drawn edges have no textual support |
| [explicit-citation-graph.md](synthesis/example-comparison/explicit-citation-graph.md) | O(n) bottom-up — read each paper once, extract only what it explicitly states about others; connected-components analysis (union-find) on the resulting graph | 32 confirmed edges; 19-paper giant component, 2-paper satellite, isolates — ground truth for the other two methods |
| [implicit-pairwise-analysis.md](synthesis/example-comparison/implicit-pairwise-analysis.md) | O(n²)-ish content-matching — date-ordered pairwise check of named limitations vs. later mechanisms | 10 new uncited-but-real edges (likely undercounted); unioned with the 32 explicit edges, 2 previously fully-isolated papers (ResearchRabbit, Scholar Augment) get pulled into the field's main connected structure |
| [lineage-comparison.md](synthesis/example-comparison/lineage-comparison.md) | Worked example — ProfOlaf drawn all three ways | 6 real relationships total; no single method found more than half |

**Why all three tracks are grouped under Synthesis, not scattered across LitDiscover:** all three
answer the same question — given a curated paper set, structure it into interpretable organization
— via disjoint subroutines. `example-comparison/` operates on paper *text* (LLM-extracted
citations/mechanisms) and does only the shallowest graph-topological operation, connected
components; the representation-learning track operates on *which text representation* gets
embedded before clustering; Q-SYNTH operates on real citation *graph data* (APS's sparse `C`
matrix) and does actual community detection (Leiden), degree-distribution fitting (power-law γ),
and manifold/spectral embedding (NST/UMAP/SG-t-SNE). `example-comparison/` and Q-SYNTH are both
graph-topological in the loose sense; they differ in depth and in whether the graph comes from an
LLM's reading of text or from a real bibliometric database — worth stating precisely rather than as
a text-vs-graph dichotomy.

---

## Project status (2026-07-14)

**LitDiscover — Discovery/screening evaluation redesigned around end-to-end recall/precision,
then folded back into `litdiscover/` from a brief top-level promotion (session 41):** Research
into whether the field has a mature eval standard for discovery/screening (see
`litdiscover/corpus-curation-prior-art.md`) surfaced a real methodological flaw in this project's
own Experiment 1: isolated discovery-only or screening-only recall/precision numbers aren't
defensible, since precision's denominator is discovery-dependent — the same fact that made the
original system's 73-100% recall headline imply 0.03-0.45% precision once anyone checked (session
38's finding, below). `litdiscover/discovery-roadmap.md` §4.0 (new) defines the corrected primary
experiment — end-to-end recall/precision of the actual `included` set against real survey
bibliographies, budget-capped, funnel-reported — and demotes the existing operator-ablation work
(§4.1-§4.11, the "Experiment 1" described below) to diagnostic-decomposition status: real,
reusable, but not the headline claim anymore. Was briefly promoted to its own `wiki/discovery/`
top-level study the same day, then folded back into `litdiscover/` on reflection that discovery +
screening is LitDiscover's core identity, not a separable phase (see the LitDiscover section
above). **Next:** build the §4.0 end-to-end harness (§7 step 0) — supersedes recomputing the
stale isolated-recall numbers below in isolation.

**LitDiscover — discovery unified across closed-corpus/live-S2, canonical result promoted (2026-07-14, session 39):** Built `litdiscover/discovery/graph_source.py` (`GraphSource`/`S2Source`/`ClosedCorpusSource`) so `backward_traversal_operator`/`forward_traversal_operator`/`pareto_hub_threshold`/`author_expansion_operator`/`venue_expansion_operator` run identically against live S2 or the closed APS corpus — 259/259 tests passing, all 227 pre-existing tests unmodified. Used it to migrate all 6 closed-corpus eval/sweep scripts + a new `07_operator_benchmark.py`, and `live-survey-eval/09`; deduplicated `10`/`11`/`12` into a shared `_shared.py`. **`eval/04b` (the paper's canonical cold-start result) was actually re-run and promoted**: a real filter-design flaw in the old Pareto implementation (discarded candidates by their own out-degree, not the frontier's) was found and fixed — full 54-condition comparison shows mean recall 93.5%→99.6%, mean corpus size 3.1x smaller. This leaves `05_miss_analysis.py`'s canonical condition with zero misses, so `06_publication_figures.py`'s Fig 7 has nothing to plot — paused, not resolved, pending a paper-facing decision. `eval/03`/`sweep/08`/`live-survey-eval/09` were migrated but deliberately not run to completion (real time/API cost at scale, a user-directed call, see `litdiscover/discovery-roadmap.md` §1.4). `.mat` file's author data confirmed technically inaccessible (MCOS-encoded `string` type, `mat73` explicitly rejects it) — author/venue-expansion benchmarking against the closed corpus stays S2-only.

**LitDiscover (solo):** ❌ Still desk-rejected by IP&M (2026-07-07), redo in progress. **IP&M resubmission checklist item 1 closed 2026-07-14:** `related-work.tex` re-read fresh against the actual desk-rejection wording ("leverage SOTA baselines, especially LLMs... reference the most updated articles from the current year") — confirmed addressed (6 papers from 2025-2026 cited). Both flagged "not independently verified" bib entries closed out: `Lau2025Elicit` had a real error (wrong author initial + missing DOI/volume/pages, fixed via PMC full-text verification), `Haryanto2024LLAssist` confirmed correct as-is. Recompiled clean, 21 pages, 0 errors.

**LitDiscover — discovery-phase Experiment 1: run live, real findings, now ⏸ paused (2026-07-14) — status superseded by session 41's §4.0 redesign above, findings below still stand as diagnostic evidence:**
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
added along the way. Experiment 1 is now marked **paused** in `discovery-roadmap.md` (⏸ box
at the top of §4) rather than abandoned — real findings preserved, a redesign path
(budget-normalized comparison, §4.7, never built) scoped for whenever this resumes. See
`wiki/session-log.md` session 38 for the full account, including a mid-session file-clobber
incident (concurrent session) that was caught and reconstructed.

**LitDiscover — representation-learning research program, new 2026-07-14 (moved to `synthesis/representation-learning-plan.md` same day, see below):** scopes Experiment 2 — does embedding a structured 6-field paper summary organize a field's papers better than embedding raw/lightly-processed text, motivated by `synthesis/example-comparison/similarity-cluster.md`'s documented clustering failure. Framed around a representation-learning evaluation paradigm ladder (retrieval → clustering → taxonomy-recovery → downstream-utility), with the deeper hypothesis stated explicitly: discourse-structure-aware representations should organize a field better than raw-text ones. Section-level ground truth for the 3 live surveys (Ge21-HSS, K17-RGC, Le25-GLLM) is built and saved to `live-survey-eval/data/section-ground-truth/`. **Along the way, found and fixed a real gold-set data-quality bug**: 2-6 entries per survey (except Le25-GLLM) didn't correspond to any reference the survey actually cites — traced to S2's own `/references` endpoint linking malformed records, not this codebase's PDF parsing. Two automated content filters were tried and both reverted after live testing proved them net-harmful (they rejected far more real short/all-caps titles than actual garbage); the actual fix was manual, surgical removal of the confirmed-bad entries from `Ge21-HSS_gold.json` (202→200) and `K17-RGC_gold.json` (56→52). **Next:** recompute `discovery-roadmap.md`'s live-survey recall numbers against the corrected gold-sets (stale, small expected effect), then resolve the remaining open decisions (full-text pooling, k-fixed-vs-elbow, flat-vs-hierarchical scoring) before building the actual embedding/clustering pipeline — see `synthesis/roadmap.md` for current status.

**LitDiscover the engine — repo restructured three times 2026-07-14:** `litdiscover/intake/` renamed to `litdiscover/discovery/` (all import references updated across the codebase + CLAUDE.md); promoted from `lit-review/litdiscover` to sit directly at the `citation-networks` repo root; then, later the same day, moved again into `lit-review-bot/litdiscover/` as part of consolidating it with the 14 cloned reference-systems repos and the RLD paper under one shell folder (`lit-review-bot/` — see the repo-layout note at the top of this file; `deprecated-bot/` holds an older, no-longer-active `litreview` variant, kept for reference not active use). `synthesize`'s citation-grounding check (`check_citation_grounding()`) still **not yet run against a real project** — still the top blocker for deciding whether the synthesis-stage redesign work is worth it. Still needed: bump + republish to PyPI (unchanged blocker, now several sessions old).

**LitDiscover wiki:** `wiki/litdiscover/` has `research-roadmap.md`, `discovery-roadmap.md` +
`corpus-curation-prior-art.md` (round-tripped through a brief `wiki/discovery/` promotion, folded
back 2026-07-14), and `decisions.md`/`open-questions.md` (live, updated in place, discovery items
folded back into `open-questions.md` too). `deep-dives.md` lives with the reference-systems corpus
now, not in the wiki — see the repo-layout note at the top of this file. `phase-representation-roadmap.md` and the lineage-construction work moved to
`wiki/synthesis/` (2026-07-13/14) — see the Synthesis section above. Flagged, still not decided:
RLS is disabled on all 6 tables in the `litreview-v2` Supabase project (anon key has full
read/write).

**`robust-literature-discovery` repo (2026-07-10):** ✅ Fully restructured, pushed. Deleted `inbox-papers/` and `app-validation-data/` (dead). Split into two self-contained tracks — `closed-corpus-eval/` and `live-survey-eval/`, each owning its own `scripts/` + `data/` (verified zero cross-track coupling by reading all 12 pipeline scripts in full). `closed-corpus-eval/scripts/` further split into `eval/` (6 scripts, produces every paper-claimed number/figure) and `sweep/` (5 scripts, parameter-justification only — 2 are dead/superseded). Explicit decision (2026-07-10, since superseded): the raw `included_366_2026-07-09.csv` snapshot was kept in the wiki rather than duplicated into `rld/` — deleted 2026-07-13 once its mining work was fully captured in `litdiscover/deep-dives.md`/`related-work-lineage.md` and the live Supabase table (`litreview-v2`) had moved past it (4,534 new pending candidates added since). `rld/drafts/refs.bib` remains the frozen paper-authoritative citation record.

**Zeitgeist (joint w/ Xiaobai):** ⚡ First full LNCS draft compiled — `writings/zeitgeist_paper.pdf`, 10 pages, 0 errors. User reviewing PDF. Repo is `github.com/davidcagoh/citation-dynamics` (private, promoted from `citation-networks` 2026-07-06; local clone renamed `zeitgeist/` 2026-07-14). **Relevant to Synthesis below:** litdiscover's traversal stage now exports the same HDF5 citation-graph format this repo's `phase1_build_graph.py`/`phase2_leiden_cluster.py` already use — opens up citation-network-aware synthesis clustering as a future redesign (see litdiscover's session-log entry, 2026-07-07). Next: address review feedback, verify bibliography, then iterate toward submission.

**Synthesis — refactored end-to-end 2026-07-14 (session 40), no longer the stalled connective tissue it was 2026-07-08:** built `synthesis/background/reference-implementation-survey.md`, a code-grounded (not paper-text) audit of 14 cloned reference literature-review-automation systems (`lit-review/reference-systems/`) — via parallel agents extracting each system's actual synthesis mechanism and cross-checking it against both `deep-dives.md`'s paper-text summaries and each paper's own reported eval. Found real paper-vs-code fidelity gaps (SurveyX's "attribute forest" doesn't exist in code; SurveyGen's re-ranking formula doesn't match its stated coefficients; InteractiveSurvey's clustering variable is named `hdbscan_model` but instantiates `AgglomerativeClustering`) and a field-wide finding written up in `background/eval-standard-gap.md`: no mature synthesis-quality eval standard exists in this literature (the widely-reused citation-quality metric only reaches ρ≈0.54 against human judgment; the "synthesis"/"critical analysis" construct specifically has zero independently-validated metric anywhere in the corpus). Used this plus an honest assessment that `wiki/synthesis/` was rigorous *scoping* but not yet a rigorous *investigation* (zero code, zero results) to fully restructure the directory: merged the two overlapping, both-unstarted planning docs into `q-synth-plan.md`; pulled in `litdiscover/phase-representation-roadmap.md` as a third parallel corpus-structuring track (`representation-learning-plan.md`, on the user's own instinct it was "a subroutine alternative" to the other two); moved the three-method lineage-construction work in as the LLM-text-native control condition (`example-comparison/`, renamed from `background/lineages/` 2026-07-14); wrote `roadmap.md` as a single entry point with a per-track status table and next action. Closed by verifying the K17-RGC gold set actually exists — not at the path `q-synth-plan.md` had guessed, but at `live-survey-eval/data/gold-sets/K17-RGC_gold.json` (52 entries, all with S2 IDs, 49/52 with DOIs) — clearing Q-SYNTH's first blocking prerequisite. **Next:** build the 1-hop subgraph and run Leiden once, cheaper than waiting on the still-unmet planner/architect sprint-planning steps.

**Wiki / program framing (2026-07-08):** No code changes this session. Captured two strengtheners (LitDiscover traversal visualization, Zeitgeist HDP-based resolution) and two speculative future directions (4th citation motif "coupled fields," HDP as its detection method) in `concepts.md`. Wrote `research-program.md` — plain-language, collaborator-facing overview of the full pipeline with schematics. Ran an ad hoc Shapiro-Wilk test on Zeitgeist's 25 per-community γ_c values (W=0.919, p=0.047, right-skewed) — not yet reflected in the paper, flagged as a possible addition.
