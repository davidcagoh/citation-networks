# LitDiscover

One file, most-important-first. Replaces `research-roadmap.md` + `discovery-roadmap.md` +
`corpus-curation-prior-art.md` + `decisions.md` + `open-questions.md` (consolidated 2026-07-21,
session 45 — those five files had grown to 2,261 lines across six documents and nobody could tell
what to read first). Full prior detail for anything condensed below is still in git history if
ever needed. `manual-pipeline-retrospective.md` stays a separate file — it's already tight (107
lines) and is the newest, most-load-bearing document in this directory.

Pipeline: `SEED papers (2-5) → DISCOVER → SCREEN (LLM) → EXTRACT → SYNTHESIZE`

**Deciding what to try next on the discovery algorithm itself?** See
[protocol-log.md](protocol-log.md) — every protocol variant/config tried so far, verdict (kept/
rejected/undecided), and why. This file's Discovery section below is status; `protocol-log.md` is
the decision history behind it.

---

## Status right now (2026-07-21)

**The one open question that gates everything else below:** a manual, human-steered pipeline
(keyword search → curate/extract → refine → forward/co-citation, Zotero-backed) is being
dogfooded in parallel as a **candidate replacement for the engine's Discovery stage**, not an
addition to it — see `manual-pipeline-retrospective.md`. Motivated by the engine's own finding
that co-citation was the only non-traversal operator with real signal (below). Until this
resolves, treat all engine-improvement work below as *correct if/when the engine continues*, not
as an active to-do list. Three continuation threads named, not yet started: (1) source a fresh
general A-share dataset to re-test the manual pipeline's reconciled findings against real data;
(2) refine the manual pipeline's own methodology (missing "reconcile for redundancy" stage,
forward-citation age-targeting, co-citation fallback); (3) a separate survey of lit-review-*eval*
methodology itself, to strengthen the case for the manual approach — not yet started, still needs
scoping (existing prior-art work here is about automated *tools*, not eval methodology as its own
question — see Prior Art below).

**Paper:** desk-rejected by IP&M (2026-07-07), redo in progress. Targeting IP&M resubmission —
`related-work.tex` fix confirmed addressed 2026-07-14 (6 papers from 2025-26 cited), 21 pages,
0 errors. Submission logistics still open: Xiaobai's ORCID, exact conference city, Wohlin2014
page numbers, send PDF to Xiaobai for review.

**Top existing blocker, independent of the engine-vs-manual question:**
`check_citation_grounding()` (shipped 2026-07-11) has never been run against a real project — the
actual grounding-precision number is still unmeasured, and gates whether the synthesis redesign
below (plan-before-write, cluster-assignment validation) is worth building at all.

**Housekeeping done today:** `reference-systems/` (14 cloned systems + `deep-dives.md`, the prior-art
source for everything in this file) promoted from `lit-review-bot/reference-systems/` to the repo
root — important enough on its own. `lit-review-bot/projects/automated-lit-review-methodology/`
archived to `_archive/` — its raw discovery pool turned out to be mostly noise (generic
high-citation ML papers pulled in by traversal), and the curated version of that work already
lives in `reference-systems/deep-dives.md`.

---

## Discovery

**Implemented:** two mechanisms — bidirectional citation traversal (backward: PDF-first reference
extraction with S2 fallback; forward: S2 `/citations`; both gated by a Gini-adaptive Pareto hub
filter) and an LLM-keyword→S2-search escape hatch that fires when traversal stalls. Five more
operators shipped 2026-07-14 via TDD: embedding search (S2's own SPECTER Recommendations API),
author expansion, venue expansion, recency-only search, and co-citation retrieval. All eight
(traversal ×2 + these 5 + keyword search) share one `operator(paper_set) -> OperatorResult`
contract, now unified in a single `litdiscover/discovery/operators.py` (consolidated 2026-07-31,
see Decisions below) — `discovery/` is down to 3 files total (`s2_client.py`, `operators.py`,
`orchestrator.py`).

**The methodological finding that matters most:** the original system's headline recall
(89–98% closed-corpus, 73–100% live-survey) had never had its precision checked. Checked
2026-07-14 for the first time: implied precision is **0.03%–0.45%**, because that validation
measures pure graph reachability with zero screening in the loop. Precision's denominator (the
candidate pool) is *produced by* discovery — so a discovery-only recall number or a
screening-only precision number can't be defended alone as evidence of system quality, ever
(this is the same structural point `../synthesis/synthesis.md` makes independently for
survey-generation quality — see Prior Art below). **New primary metric defined but not yet
built:** end-to-end recall/precision/F1 of the real `status=included` set (not raw candidates)
against a survey's true bibliography, budget-capped per run, full seeds→discovered→included
funnel reported alongside the ratio. Blocked on the engine-vs-manual-pipeline decision above, not
on anything technical.

**Operator benchmark (2026-07-14, live, all 3 surveys, single-pass isolated-operator recall —
not the multi-round production loop):**

| Operator | K17-RGC (n=56) | Ge21-HSS (n=202) | Le25-GLLM (n=57) |
|---|---|---|---|
| backward_traversal | +5 gold | +2 gold | +0 |
| forward_traversal | +0 | +1 gold | +0 |
| **co_citation** | +4 gold | **+19 gold** | +2 gold |
| author_expansion | +0 | +7 gold | +0 |
| embedding_search | +0 | +0 | +0 |
| venue_expansion | +0 | +0 | +0 |
| recency_search | +1 gold | +0 | +0 |

**Co-citation is the only non-traversal operator that adds gold on every survey** — real,
reproducible signal, best precision of anything that fires (10–29%), the one operator with a
nonzero ablation drop everywhere. **Embedding search and venue expansion found zero new gold
anywhere** — a real early negative result, not yet disambiguated from an implementation gap
(intermittent 429s undercounted author/embedding operators during this run; root cause found and
fixed — S2's flat 1 req/sec cap across all endpoints, `_s2_wait()`'s margin was too tight, now
retries with backoff). A follow-up naive chained-composition attempt made both recall *and*
precision worse (unfiltered forward traversal + citation-count frontier selection → noisy corpus
→ generic hub papers) — diagnosed, not fixed; the right redesign is the budget-normalized
end-to-end metric above, not another raw-recall patch. n=3 surveys throughout — every number here
is directional, not statistically powered.

**Field-wide gaps found in the 27+5-method prior-art survey** (author/venue/recency methods,
i.e. §3's untested list, all have real precedent to build from — see Prior Art below for the
grouped findings): no other system does author-only or venue-only search at all; nobody addresses
"papers too new to be graph-reachable" as a named problem; LiRA's own §7 names "integration of
screening and search-criteria definition" as its unaddressed future work — independent
confirmation that discovery-with-recall-guarantees is a genuinely open gap in this literature, not
just an area LitDiscover happened to prioritize.

---

## Extraction

**Implemented:** single-shot Gemini call per paper, fixed 11-field schema
(research_questions/contributions/methodology/system_or_tool/datasets/metrics/key_results/
limitations/future_work/themes/related_to). No validation against ground truth anywhere.

**Known gap:** the ad hoc 6-field template used for `reference-systems/deep-dives.md` (Problem /
How it works / How evaluated / How performed / Relation to prior work / Limitations) proved rich
enough to support real downstream analysis the 11-field schema was never asked to support — not
yet ported, open question is prompt-only change vs. an `extractions` table migration.

**Proposed benchmark, reuses existing ground truth:** the 22-paper `deep-dives.md` corpus already
has full-text-verified 6-field extractions. Run the current 11-field extractor over the same 22
papers and diff what the richer template captures that production drops.

---

## Synthesis

**Implemented:** 3-pass pipeline — k-means clustering on Gemini paper embeddings (elbow-method k)
→ per-theme narrative generation (map-reduce above 80 papers/cluster) → intro/conclusion.
`check_citation_grounding()` shipped 2026-07-11, wired in as on-by-default — **never run against a
real project** (see Status above).

**Audit complete, ranked** (full detail in git history — this is the verdict, not the reasoning):
1. Citation grounding — confirmed gap, cheap fix, **shipped, unmeasured**.
2. Plan-before-write (no intermediate claims-list/outline before full prose) — confirmed gap,
   larger fix, gated on #1's results.
3. Ground-truth cluster-assignment validation — confirmed gap, no cheap ground truth exists
   (Zeitgeist's community labels are a different corpus/domain).
4. Map-reduce's reduce step loses access to source fields — same root cause as #1, no separate fix.

**Representation question** (does a structured-summary embedding cluster better than raw text
before k-means) moved to `../synthesis/synthesis.md` (Representation learning section) —
motivated by that file's (LLM-text-native section) corpus-scale clustering failure
(12/32 real edges survived, 3 fabricated).

**Immediate next step, unchanged:** run `litdiscover synthesize` on a real project to get the
actual grounding-precision number — gates whether #2/#3 above are worth building at all.

---

## Prior Art

Full per-system deep-dives (27 methods + 5-entry verification cohort, 6-field template each) live
in `../../reference-systems/deep-dives.md` — this section is the synthesized findings, not a
duplicate of the table.

**Discovery mechanisms, grouped:** citation-graph traversal is a two-system family
(ResearchRabbit, ProfOlaf) — LitDiscover's closest cousins. LLM-keyword→search-API is the
dominant family by count. Embedding/semantic retrieval over a fixed or crawled corpus is a third
cluster (AutoSurvey, SurveyX, SocLitGen). A large cluster (LiRA, Meow, Scholar Augment, ASReview,
SWIFT-Review, RobotSearch, Bio-SIEVE, LLAssist, IntrAgent) has **no discovery mechanism at all** —
they presuppose the search problem already solved.

**Screening, grouped:** ProfOlaf is the only system with a direct human-vs-LLM head-to-head near
parity (F1 0.928 vs. 0.927 human) — the strongest evidence in the corpus that LLM screening can
match trained raters under a well-designed protocol. Active-learning re-rankers (ASReview,
SWIFT-Review/Active-Screener) are measured via WSS@95 (ASReview 83%, SWIFT-Review 54%) — the
field's standard screening-efficiency metric. **No system in this 27+5-method corpus reports a
screening precision/recall number against a citation-traversal-fed queue** — the exact gap
Discovery's §4.0 end-to-end metric above closes; running `screen_batch()` against an external
CLEF TAR/SYNERGY dataset would measure the classifier's competence on somebody else's pool, not
whether LitDiscover's own discovery-fed queue produces a good corpus.

**Stopping criteria are the rarest feature in the whole corpus** — only SWIFT-Active Screener
(negative-binomial recall-estimation, stops at ~40% screened for 95% recall) and SocLitGen
(adaptive re-retrieval on low validated-count) have anything formal. LitDiscover's own cycle-yield
gate is a real, measured stopping rule of the same shape, in a field where most comparable tools
(ResearchRabbit, ASReview) have none at all — a genuine, defensible point of novelty.

**The eval-standard gap — same finding as Synthesis's, independently arrived at, now reinforced a
third time.** `../synthesis/synthesis.md` (eval-standard gap section) found no validated synthesis-quality
standard exists (AutoSurvey's citation-NLI + LLM-judge rubric got copied near-verbatim into LiRA/
SurveyX/SurveyGen-I, but only reaches ρ≈0.54 against human judgment, computed once, never
re-validated downstream). This directory's own discovery/screening research found the same shape
of gap one stage earlier: decades-old *relative-recall* methodology exists for discovery-in-
isolation, CLEF TAR/SYNERGY is mature for screening-in-isolation, but nobody validates the two
*together* against a citation-traversal-fed queue. Rereading `deep-dives.md`'s "how it performed"
claims directly (session 45, 2026-07-21) reinforced this a third way: nearly every
survey-generation system's "beats baseline X" claim inherits an unvalidated metric from whichever
paper it borrowed code from, rather than re-validating against human judgment itself — three
independent angles on the same underlying problem: this field has no shared, validated way to
know whether any of these systems actually work.

---

## Decisions

**Discovery layer consolidated, 11 files → 3 (2026-07-31, session 46).** `discovery/` had
accumulated 2 CLI-wired operators in `traverse.py` and 5 more (built for a benchmark, never
wired in) in a separate `operators.py`, plus `graph_source.py` (a `GraphSource`/`S2Source`/
`ClosedCorpusSource` class hierarchy), `budget.py`, `search.py`, and 3 files (`verify.py`,
`relwork.py`, `forward_cites.py`) that weren't discovery operators at all. Merged into
`operators.py` (all 8 operators, `OperatorResult`/new `CorpusIndex` dataclasses,
`pareto_hub_threshold`, budget accounting) + `orchestrator.py` (thin CLI entry point, renamed from
`traverse()` since backward/forward are just 2 of 8 operators now) + unchanged `s2_client.py`.
`GraphSource`'s class-based source-injection replaced by a `source: Literal["s2","local_corpus"]`
argument + `corpus: CorpusIndex` — the closed-corpus benchmark track (`paper/closed-corpus-eval/`)
still works, just without a class wrapper; venue inference (APS-specific) moved out of the engine
entirely into the dataset loader, since `operators.py` should carry zero dataset knowledge.
`forward_cites.py` deleted outright — its lookup was literally `forward_traversal_operator`
unfiltered over the whole included set, not a distinct mechanism; its report-writing moved to
`reports.py`, its DB-write generalized into `db/client.py::ingest_candidates()`. `verify.py`/
`relwork.py` moved to a new `tools/` package (neither produces discovery candidates). Verified,
not just tested: `litdiscover`'s 246 tests green, plus a real regression run of the paper's
canonical `04b_cold_start_lowseed.py` against the actual APS dataset — the deterministic `top_k`
seed strategy came back byte-identical to the pre-migration git-committed result (100.0000%
recall, 72,395 corpus size, exact match), proving the actual engine's behavior is unchanged.
Along the way, found (not fixed) a pre-existing bug in the eval script's own `random`/
`contaminated` seed generation (`list(some_set)` before `random.shuffle()`, combined with
Python's default per-process hash randomization) that makes those two strategies'
numbers non-reproducible on any rerun — unrelated to this refactor. Full account:
`wiki/session-log.md` session 46. Decision source of truth going forward:
`wiki/litdiscover/protocol-log.md`.

**Key parameters** (APS closed-corpus validation): `N_ROUNDS=2` (round 3 adds only 2.4pp for the
worst survey, negligible elsewhere); `PARETO_P=80` in simulation, but production's actual filter
semantics are frontier-paper in-degree with Gini-adaptive percentile (80th/90th/95th), not a fixed
80 — the simulation approximates the real filter, doesn't define it; `YIELD_THRESHOLD=0.05`;
`K_ESCAPE=20`; `SEED_SIZES=[1,2,3,4,5,10]` (user-facing realism — most users provide 1–5 seeds).
Gold set = the survey's bibliography, never the survey paper itself. Metric is called "overlap"
in the paper, "recall" in the scripts (never renamed, low-value churn).

**Naming/distribution:** package is `litdiscover` (renamed from `litreview2`/`LitReview v2` —
"discover" names the process, not the output), live on PyPI, not yet republished past v2.0.0.

**Staged-by-default workflow (2026-07-09):** `run`'s fully-unattended autopilot loop became opt-in
(`mode="autopilot"`); the new default breaks the pipeline into individually-triggered stages
(`traverse`/`prefilter`/`screen`/`mark`) each writing an inspectable artifact. Why: driving the
engine from a different project surfaced that the autopilot loop's failure mode (silent 0%-yield
retry burning ~13 rounds after a spend-cap error) and its screening quality were the same root
problem — nothing gates the loop except the loop itself. A human+agent eyeballing a
keyword-prefiltered list together caught ~60 false positives an LLM screen likely would've missed.
Rule adopted same session: never run `screen` on a pending queue above ~50 papers without
`prefilter` first (violating this once burned an LLM call on an 84%-noise queue).

**Discovery reframed as operators, not pipelines (2026-07-14):** `traverse.py` decomposed into
independently callable, independently ablatable functions sharing one `OperatorResult` contract —
what makes the operator benchmark above possible at all. Embedding search uses S2's own
Recommendations API rather than a self-hosted index (indexing all of S2 ourselves is infeasible).

**Venue history, final target IP&M:** JCDL 2026 deadline missed (never submitted despite an
EasyChair record) → JASIST (reformatted, dropped) → ACM TOIS (reformatted, abandoned — 20-page
minimum this 12-page paper doesn't meet without real padding) → **Information Processing &
Management**, current active target: strongest scope fit (spans system-level and human-centered
research, matching this paper's framing), no page floor, APA author-date citations (confirmed
before reformatting to avoid a repeat of the TOIS surprise).

**Full-text verification of the 7 Tier 1/2 reference papers (2026-07-10/11):** confirmed worth
doing — abstract-only extraction had gotten ProfOlaf's evaluation cell flatly wrong and missed a
real nuance in LitLLMs'. Code-level check (cloning the actual repos) then corrected a paper-text
claim: LiRA's CQF1 is an offline eval metric adapted from AutoSurvey's own code, not a live
in-loop check — meaning `check_citation_grounding()` is actually ahead of both precedents on this
specific axis, once it's actually run (see Status above).

**Related-work lineage: three-method comparison replaced thematic clustering (2026-07-13).**
Thematic-bucket clustering (`similarity-cluster.md`, deprecated) was audited and found to
represent only 12/32 real citation edges with 3 fabricated ones. Two more rigorous methods
(`explicit-citation-graph.md`, `implicit-pairwise-analysis.md`, both in
`../synthesis/synthesis.md`, LLM-text-native section) replaced it as the actual related-work-drafting source.

---

## Open questions

**Submission logistics:** Xiaobai's ORCID, exact JCDL/IP&M conference city, Wohlin2014 page
numbers (currently 321–330 from memory, needs ACM DL verification), send PDF to Xiaobai for
review.

**Engine feature requests, from external use, 2 of 4 still open:**
- `build_papers_json` doesn't persist authors (S2's `authors` field is fetched but dropped before
  JSON export).
- No Groq screening-backend fallback / no fast-fail on spend-cap errors — a hard Gemini quota
  error burned ~13 rounds retrying identically before being caught manually. Directly relevant to
  Discovery's §4.0 budget-control requirement above: a run that silently loops on a spend-cap
  error breaks "fixed, documented budget per run."

**Extract/synthesize redesign directions**, proposed but not yet scoped (both gated on the
engine-vs-manual decision at the top of this file): (1) `extract` producing something closer to
`deep-dives.md`'s 6-field structure instead of the current 11-field schema; (2) `synthesize`
incorporating an implicit-pairwise-style enrichment pass (check each paper's own named limitations
against other included papers' mechanisms) — needs an embedding-prefilter design first, since the
manual version of this was O(n²)-ish even at 27 papers.
