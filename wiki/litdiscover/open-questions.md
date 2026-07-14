# LitDiscover — Open Questions

All pre-submission content questions believed resolved (session 15). EasyChair submission filed 2026-04-21.
Remaining items are logistics / camera-ready only.

**Discovery/screening open items folded back in here (2026-07-14)** — previously split out to a
promoted `wiki/discovery/` study, then folded back on the reasoning that discovery+screening
*is* LitDiscover's core identity, not a separable phase (unlike Synthesis, which draws on
Zeitgeist's own graph-analysis machinery and is genuinely a disjoint corpus-structuring add-on).
`discovery-roadmap.md` and `corpus-curation-prior-art.md` are flat siblings in this same
directory now, not a subfolder.

---

## IP&M resubmission checklist (2026-07-13) — ✅ item 1 resolved 2026-07-14

`related-work.tex` re-read fresh against IP&M's actual desk-rejection wording ("leverage SOTA
baselines, especially LLMs... reference the most updated articles from the current year") —
confirmed the ProfOlaf-centered rewrite genuinely addresses it (6 papers from 2025-2026 cited).
SWIFT-Review/RobotSearch fixes verified rendering correctly in the compiled `.bbl`.
`Haryanto2024LLAssist` confirmed correct as-is; `Lau2025Elicit` had a real error (wrong author
initial, missing DOI/volume/pages) — fixed via PMC full-text verification. See `decisions.md`'s
2026-07-14 entry for detail. Recompiled clean, 21 pages, 0 errors.

## Extract/synthesize redesign, informed by the lineage-construction comparison (2026-07-13)

**Context:** the three-method lineage comparison (`../synthesis/example-comparison/`) found that citation-tracing alone
misses real structure, and that structured extraction fields (`deep-dives.md`'s 6-field template)
made every later analysis pass — the audit, the pairwise pass, the union finding — possible.
Two concrete directions for the engine itself, proposed by the user, not yet scoped:

1. **`extract` should produce something closer to `deep-dives.md`'s structure** — Problem /
   How it works / How evaluated / How performed / Relation to prior work / Limitations — instead
   of whatever the current extraction schema captures. Low-risk: the template is already validated
   by real use this session. Needs a scoping pass against the current `extractions` table schema
   (themes/contributions/methodology/key_results) to see how much is a prompt change vs. a
   migration.
2. **`synthesize` should incorporate an implicit-pairwise-style enrichment pass** — check each
   paper's own named limitations against other included papers' mechanisms, the way
   `implicit-pairwise-analysis.md` did for this 27-paper corpus — plus lean on the already-shipped
   `litdiscover related-work-mine` (fetches a close competitor's own Related Work section) more
   directly inside `synthesize` rather than as a separate manual step. **Scaling caveat, don't
   skip this:** the pairwise method was O(n²)-ish even at 27 papers and needed real judgment calls;
   a production project can have 50–300+ included papers, so this needs the embedding-prefilter
   design already discussed this session (rank candidate pairs by embedding similarity first,
   only spend LLM judgment on top-k candidates) — not brute-force all-pairs comparison.

**Sequencing suggestion:** run `check_citation_grounding()` against a real project first (item
#1 of the original Extract/Synthesize Technique Audit below, shipped 2026-07-11, still **not yet
run against a real project**) before scoping either direction above — its whole stated purpose is
to gate whether the next-tier engine work is worth the investment, and it's already built and
free to run.

## Extract/Synthesize Technique Audit (2026-07-10)

**Context:** `extract`/`synthesize` were built before the related-work research existed
(see `../synthesis/example-comparison/similarity-cluster.md`). The traversal/discovery core is not behind SOTA — nothing in
the lineage doc replicates LitDiscover's closed-corpus ground-truth recall validation — but
extract/synthesize plausibly are, since they were built naively without that grounding. This is a
scoped audit plan, not a rewrite and not a replication of any competitor's repo — LitDiscover's
scope (find the literature, with proof) is different from AutoSurvey/LitLLM's scope (write a
survey), so the fix is targeted technique-borrowing, not adopting their whole architecture.

**Resigned fallback (2026-07-10):** if extract/synthesize turn out too hard to fix well, or still
underperform after the fixes below, the personal-workflow fallback is to stop trying to make
LitDiscover write the review itself and instead feed the curated/extracted paper set (~50 docs)
into NotebookLM or similar for the actual synthesis step. Keep this as a real fallback, not a
last resort to feel bad about — LitDiscover's differentiated contribution is the discovery/recall
guarantee, not prose generation.

Four concrete audit questions, each traceable to a specific full-text finding from the 6 papers
now read (PDFs at `../../lit-review-bot/reference-systems/reference-pdfs/`, formerly `fulltext/` — see `decisions.md` for the verification record).

1. **Citation grounding — is any claim ever checked against its cited paper?** AutoSurvey's
   citation-quality metric (`h(c_i, Ref_i)`, an NLI check per claim) is the only reason it can
   claim citation recall/precision numbers at all. LiRA reports beating AutoSurvey on this via
   CQF1 (0.76/0.73 vs. ≤0.63) — **but code-level check (2026-07-11, cloned
   `lira-workflow/auto-review-writing`) found CQF1 is an offline eval metric copied near-verbatim
   from AutoSurvey's own code, not a live in-loop check, and `ReviewerAgent` is a general
   completeness/clarity gate, not citation-specific** (see `decisions.md`'s
   code-level correction). Neither precedent actually runs a live per-claim grounding check during
   generation. Audit: read `_write_theme_section`, the map-reduce path (`map_prompt`/`reduce_prompt`,
   ~`synthesizer.py` line 645–669), and `number_citations.py` in full — confirm there is genuinely
   no post-hoc check that a `[ID]` citation is supported by that paper's extracted fields, and scope
   a CQF1-style metric plus a lightweight reviewer pass (reusing extraction fields already in the
   `extractions` table rather than standing up a new NLI model).
2. **Plan-based generation — single-shot vs. plan-then-write.** Confirmed already (2026-07-10):
   `_write_theme_section`'s single-cluster path (`synthesizer.py` line 698) is one direct "write
   600–900 words, cite every claim" call, no intermediate plan. LitLLMs measured 18–26% fewer
   hallucinated references from adding a plan step, and LiRA's **Outline Drafter Agent** is a
   second, independent precedent for planning before writing (drafts per-section structure +
   supporting-paper assignments before any subsection is written). Audit: would an intermediate
   step ("list N claims + which paper IDs support each, then write") fit cleanly into the existing
   per-theme call, or does it need restructuring the `ThreadPoolExecutor` fan-out in `synthesize()`
   (line 589)?
3. **Ground-truth evaluation of theme/cluster assignment.** ProfOlaf directly measures
   TopicGPT-style assignment against human labels (precision 0.645/recall 0.850) — a real number
   for "is the model's topic grouping trustworthy?" LitDiscover's `_kmeans_cluster`/`_elbow_k`
   (`synthesizer.py` lines 357, 396) have no such check — clustering quality is only ever
   validated by the elbow heuristic, never against human judgment. Audit: is there an existing set
   of included papers with human-assigned themes anywhere (e.g. from `synthesis/` work or
   Zeitgeist's community labels) that could serve as cheap ground truth, or would this need a
   fresh manual pass?
4. **Retrieval structure at scale — does map-reduce lose grounding on large clusters?**
   AutoSurvey's ablation shows retrieval quality (not just "the papers are in context") is what
   makes generation good; large LitDiscover clusters use map-reduce (map: bullet-point synthesis
   per 80-paper chunk, reduce: final write from chunk syntheses) — audit whether the reduce step
   still has access to per-paper source IDs for citation, or only the map step's already-compressed
   bullets (i.e., does compression happen before or after citation attribution is fixed).

Each item ends in a decision, not an automatic rewrite: "confirmed fine, no action" or "small
bounded fix, scope it" — mirroring how the related-work full-text benchmark (`decisions.md`) worked.

**Status (2026-07-11): audit complete — verdicts below.** All 7 of 7 Tier 1/2 papers were
full-text verified first (see `decisions.md`'s full-text-verification entry), then
`litdiscover/extract/synthesizer.py` (870 lines) was read in full end-to-end.

### Verdicts

1. **Citation grounding — CONFIRMED GAP, small bounded fix.** There is genuinely no post-hoc check
   anywhere in the file. `_restore_uuids` is a pure string substitution (short ID → UUID) — it
   never checks that a cited paper's extraction fields actually support the sentence around it.
   Every `[ID]` the model writes is trusted at face value, in both the single-call path
   (`_write_theme_section`'s small-cluster branch, line 698) and the map-reduce path (line 634).
   **Fix scope:** a CQF1-style check is realistic without new infrastructure — for each generated
   section, extract every `[UUID]` + its surrounding sentence, and for each one ask Gemini
   "does this paper's `extractions` row (themes/contributions/methodology/key_results) support
   this claim, yes/no" in a single batched call per section. This reuses data already paid for
   (the `extractions` table) — no new NLI model, no new embedding pass. Rough cost: one extra
   `_call()` per section (there are already up to 4 sections running concurrently, so this fits
   the existing `ThreadPoolExecutor` pattern without restructuring).
2. **Plan-based generation — CONFIRMED GAP, but lower priority than #1.** Both write paths
   (`section_prompt` line 698, `reduce_prompt` line 669) go straight from paper summaries to full
   600–900-word prose in one call — no intermediate claims-list or outline step, unlike LitLLMs'
   plan-then-write or LiRA's Outline Drafter Agent. Note the clustering step (Pass 1) already acts
   as a coarse-grained outline (theme names = section list) — the missing plan is *within* a
   section, not across the whole document. **Fix scope:** larger than #1 — would add a second
   `_call()` per section ("list the N claims this section should make + which paper IDs support
   each"), roughly doubling Pass 2's call count. Worth doing only after #1 ships and its
   grounding-check results show whether ungrounded claims are actually common enough to justify
   the extra cost, rather than guessing upfront.
3. **Ground-truth cluster evaluation — CONFIRMED GAP, no cheap ground truth available.** Checked
   `citation-dynamics/data/analysis/community_labels.csv` (Zeitgeist's human-labeled APS physics
   communities) as a candidate reusable ground truth — **not usable**, it's a different corpus and
   subject domain entirely (physics citation communities, not any litreview project's paper set).
   No existing human-labeled theme assignments exist for any LitDiscover project's included set.
   **Fix scope:** would require a fresh manual pass (a human labeling ~20-30 papers into themes for
   one project, then comparing against `_kmeans_cluster`'s output) — real cost, not a quick add.
   Lowest priority of the four; the Gini-balance check at least catches the worst failure mode
   (one giant cluster), even without a relevance ground truth.
4. **Map-reduce grounding loss — CONFIRMED, but resolved by fixing #1, not a separate mechanism.**
   The map step (line 634) does have full per-paper access and correctly tags `[ID]` citations from
   the original slim summaries. But the reduce step (line 664) only ever sees the map step's
   already-compressed bullets — it has no access back to the original `extractions` fields, and is
   instructed to "preserve inline citations... exactly as they appear," i.e. it trusts whatever the
   map step decided to cite. Any grounding error introduced at the map stage propagates silently
   through the reduce stage. This is the same root cause as #1 (no verification step exists
   anywhere), just visible at a different point in the pipeline — a single grounding-check pass
   applied after the whole section is assembled (not per-stage) would catch this case too, so this
   doesn't need its own fix.

**Priority order if implementing:** #1 first (cheapest, highest leverage, unblocks measuring
whether #2 is even worth it) → #2 (only if #1's numbers show ungrounded claims are common) → #3
(only if a manual ground-truth pass becomes worth the time investment separately).

**Item #1 — shipped (2026-07-11).** `check_citation_grounding()` added to `synthesizer.py`,
wired into `litdiscover synthesize` as on-by-default (`--skip-grounding-check` to opt out).
Precision-only (batches cited claims against the `extractions` table, no new NLI model/embedding
pass), writes `<slug>_grounding_report.md`, never rewrites the review — purely diagnostic. 7 new
tests, 181/181 passing. **Not yet run against a real project** — next actual step is running
`litdiscover synthesize` on a live project and reading the resulting grounding score, which is
what decides whether #2 (plan-based generation) is worth doing at all.

Post-ship code-level check (2026-07-11, see `decisions.md`) found this fix is
actually ahead of both precedents on this specific axis: LiRA's CQF1 and AutoSurvey's
`h(c_i,Ref_i)` are both offline benchmarking metrics computed after generation, not live checks
during synthesis. `check_citation_grounding()` runs on every `synthesize` call — no competitor
codebase examined does this live.

---

## Submission logistics (before June 30)

| Item | Issue | Status |
|---|---|---|
| Xiaobai's ORCID | Need for camera-ready `\orcid{}` block | ⏳ Ask PI |
| JCDL 2026 city | `\acmConference` currently says "Texas, USA" | ⏳ Verify exact city |
| Wohlin2014 pages | Using 321–330 (user's recall) | ⏳ Verify in ACM DL |
| PI review | Send PDF to Xiaobai by ~June 8 | ⏳ Not yet sent |

## Pre-submission content — discovery/recall figures (believed resolved, session 15)

These are the original IP&M submission's discovery-validation content questions — the actual
figures/claims `discovery-roadmap.md` §4.0's end-to-end redesign will eventually need to
reconcile with, not just historical record.

| Item | Issue | Believed status |
|---|---|---|
| Q1: Live experiments | K17-RGC ✅, Ge21-HSS ✅, Le25-GLLM ✅ (73.7%) | ✅ Resolved — **now stale, see gold-set fix below** |
| Q2: Fig 7 k=5 vs k=20 | Check `cold_start_results_lowseed.json` | ✅ Believed resolved |
| Q3: Fig 6 non-monotone recall | Add paragraph explaining yield-stopping mechanism | ✅ Believed resolved |
| Q4: Pareto-80 vs Pareto-50 | Demonstrate Pareto-50 fails under yield-based stopping | ✅ Believed resolved |
| Q5: Random seeds > top-5 at round 1 | Run ≥5 trials; report mean ± std | ✅ Believed resolved |
| Q9: γ < 2 in Fig 1 | Add KS goodness-of-fit sentence | Low priority |
| Q10: Error bars Figs 5–6 | Run multiple trials for random/contaminated conditions | Low priority |
| Q11: [CITATION NEEDED] locations | Fill yellow-highlighted citations | ✅ Believed resolved |
| Q15: §5 yield lines overlap | Add sentence: threshold doesn't affect final recall | ✅ Believed resolved |

**Q1 is the one item this list's "believed resolved" status doesn't survive `discovery-roadmap.md`
§4.0's findings intact.** The 73.7%-type live-survey recall headline is exactly the kind of
discovery-only number §4.0 argues can't be defended alone (it implied 0.03-0.45% precision once
checked, unscreened) — and it's computed against gold-sets since found to have data-quality bugs
(below). Resolve via §4.0's end-to-end harness, not by re-verifying the old number in isolation.

---

## Engine feature requests, from external use (2026-07-09) — 2 of 4 resolved same day

**✅ Resolved via the 2026-07-09 staged-workflow rework** (see `decisions.md`):
- The keyword-pre-filter idea → formalized as `litdiscover prefilter`. Originally surfaced as "a
  cheap deterministic keyword/regex triage before the expensive LLM screen, to cut obvious noise
  (in this case, ~2000 traversal candidates → ~135 'priority' candidates via a simple term-match)
  without burning API budget on papers that are clearly off-topic" — now shipped as its own staged
  CLI command, see `litdiscover/litdiscover/discovery/README.md` / `CLAUDE.md`.
- The related-work-mining idea → built as `litdiscover related-work-mine`.

**Still open:**
- `build_papers_json` still doesn't persist authors (see below).
- No Groq screening-backend fallback / no fast-fail on spend-cap errors (see below) — staged
  mode's manual `screen` step reduces the blast radius of this (no more silent 13-round burn),
  but the underlying gap in `screen/llm.py` itself is unchanged. **Directly relevant to
  `discovery-roadmap.md` §4.0's budget-control requirement** — a run that silently loops on a
  spend-cap error instead of failing fast breaks the "fixed, documented budget per run" checklist
  item.

Original notes preserved below.

First time litdiscover was driven from a *different* project (`adaptive-learner`'s WAILS 2026
related-work search, run against the existing `adaptive-mastery-priorart` Supabase project).
Surfaced real gaps worth fixing before the next external use:

- **`build_papers_json` doesn't persist authors.** The papers table clearly has enough to
  enrich with (S2's `authors` field is fetched at ingest/traverse time), but it's dropped
  before it reaches the JSON export. Had to do 13 individual follow-up S2 GETs by DOI just to
  get author names for citation-ready output. Add `authors` to the export schema.
- **`_papers.json`/`_graph.h5` only get written once, at the very end of `run`.** If a human
  wants to sanity-check screening decisions mid-loop (or the loop dies/gets rate-limited
  partway through, as happened here — Gemini spend cap hit at round 2 of 40), there's no
  artifact to look at without writing a one-off script that reimplements the same
  `get_all_papers`/`build_papers_json`/`write_graph_h5` calls outside the CLI. Either write
  these incrementally every N rounds, or add a `litdiscover export <slug>` command that does
  on-demand what `run` currently only does at completion.
- **No configurable/pluggable screening backend despite `GROQ_API_KEY` sitting in `.env`.**
  `screen/llm.py` is hardcoded to Gemini; the README's claim of Groq as "an alternative
  screening backend" isn't wired up in code. A hard Gemini spend-cap failure (`RESOURCE_EXHAUSTED`)
  burned ~13 rounds retrying identically before being caught and killed manually — no
  automatic backend fallback, and no fast-fail (it just loops at 0% yield until `max_rounds`).
  Worth either wiring the Groq fallback for real, or making a spend-cap/quota error short-circuit
  the loop immediately instead of treating it as a stale round.
- **User's own idea while explaining this to Claude:** reading the *related-work prose* of
  the nearest-art papers (not just their raw reference list) surfaces framing/grouping and
  discussed-but-uncited context that pure citation-graph traversal can't recover. Might be
  worth a `litdiscover related-work-mine <paper_id>` mode that fetches full text (arXiv/OA
  where available) and extracts just the related-work section for a human to read, as a
  complement to graph traversal rather than a replacement.
- **Gold-set data-quality bug found 2026-07-14, during `../synthesis/representation-learning-plan.md`'s
  section-annotation pass on Ge21-HSS:** 2 of 202 entries in
  `live-survey-eval/data/gold-sets/Ge21-HSS_gold.json` carry DOIs pointing to completely
  unrelated papers ("A Meta-analysis: Effect of Stem Cells Transplantation on Rehabilitation
  of Diabetes Mellitus with Limb Ischemia" and "A Review of the Scientific Literature as it
  Pertains to Gulf War Illnesses" — neither has anything to do with human social sensing).
  Not caused by this task; looks like a bad reference-to-DOI resolution somewhere upstream in
  how that gold-set was originally built. Worth checking whether the same resolution step
  produced similar bad entries in the other 5 gold-sets, and whether this affects any
  previously reported discovery-recall numbers (`discovery-roadmap.md` §4) that used
  this gold-set as-is.
  **Update 2026-07-14, after finishing all 3 live-survey annotation passes:** this isn't a
  one-off — K17-RGC's gold set has 4 unresolved entries too (3 near-duplicate/garbled records of
  the same textbook citations — e.g. three separate "Random graphs" entries — plus a bare
  "CAMBRIDGE STUDIES IN ADVANCED MATHEMATICS" series-name fragment with no paper title at all),
  and Le25-GLLM (the one gold-set that resolved 57/57 cleanly) is the exception, not the rule.
  **Root cause found (2026-07-14, audit) — corrected same day after checking which code path
  actually ran:** all 3 live surveys have a `survey_doi`/`survey_s2_id` configured in the
  `SURVEYS` dict (`09_live_validation.py` lines 80-114), so `build_gold_set()` (line 502) always
  calls `build_gold_set_from_s2()` (line 452) first, which succeeded for all 3 — meaning gold
  sets came from **S2's own `/references` endpoint** (`fetch_neighbors(..., "references")`,
  line 483), not from PDF text parsing. The malformed titles ("CAMBRIDGE STUDIES IN ADVANCED
  MATHEMATICS", etc.) are records **S2's own citation graph links as references** of these
  survey papers — an S2-side data artifact.
  **Two automated filters were tried and both reverted, same day, after measuring real
  false-positive cost:** first an all-caps/<3-words rejection, then a narrower
  series-name-phrase substring match. Both sounded plausible but were empirically wrong — a
  live re-fetch showed each one rejecting far more *real, correctly-cited* references than
  actual garbage: short titles (Goodman's "Snowball sampling", Rahwan et al.'s "Machine
  behaviour"), all-caps journal-rendered titles (Munkres' "ELEMENTS OF ALGEBRAIC TOPOLOGY",
  Gershkovich & Rubinstein's "MORSE THEORY FOR MIN-TYPE FUNCTIONS*"), and real book titles
  that legitimately carry their series name in parentheses (Epstein's "Agent_Zero... (Princeton
  Studies in Complexity)") are indistinguishable by title shape from the one genuine garbage
  record found. **No automated filter ships** — `09_live_validation.py` only got a `FUZZY_THRESHOLD`
  tightening (88→92, a generic match-quality improvement unrelated to this specific noise) and
  honest comments on both functions explaining why a content filter was rejected. The actual fix
  was manual, surgical removal of the specific confirmed-bad entries directly from each
  gold-set JSON (Ge21-HSS: 202→200, removed the 2 unrelated-topic mislinks; K17-RGC: 56→52,
  removed the 1 pure series-name record plus 3 entries confirmed absent from the survey's own
  51-item bibliography, fully transcribed during the section-annotation pass). This is
  consistent with `build_gold_set`'s own existing design ("manual corrections... survive
  re-runs") — the fix works *with* that contract, not around it.
  **This is confined to the 3 live surveys, structurally — the 3 APS closed-corpus gold sets
  (`closed-corpus-eval/data/outputs/ground_truth.json`) are built by
  `01_extract_ground_truth.py` directly from the APS citation-edge CSV (a DOI→DOI join on
  structured data), with no S2 API or title-matching step at all — this failure mode cannot
  occur there.** No further audit needed on the APS side.
  **Direction of the effect on already-reported numbers:** these spurious gold entries were
  papers the surveys never actually cite, so traversal could structurally never find them
  correctly — counting them in the denominator made every reported live-survey recall number
  (`discovery-roadmap.md` §1's 73.7-100% headline, §4.3's per-operator table) a slight
  *underestimate*, not an overestimate. **Now that the 6 confirmed-bad entries are removed from
  the gold-set JSONs (Ge21-HSS 202→200, K17-RGC 56→52), those recall numbers are stale and
  should be recomputed** — the true denominator is smaller, so recall will tick up slightly.
  **Should be folded into `discovery-roadmap.md` §4.0's end-to-end harness build rather than
  fixed in isolation** — no point recomputing the old isolated-discovery-recall number against
  the corrected gold-sets only to have §4.0 supersede it anyway. Full per-survey counts in
  `../synthesis/representation-learning-plan.md` §3.2.
