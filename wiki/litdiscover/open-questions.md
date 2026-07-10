# LitDiscover — Open Questions

All pre-submission content questions believed resolved (session 15). EasyChair submission filed 2026-04-21.
Remaining items are logistics / camera-ready only.

---

## Extract/Synthesize Technique Audit (2026-07-10)

**Context:** `extract`/`synthesize` were built before the related-work-landscape research existed
(see `related-work-landscape.md`). The traversal/discovery core is not behind SOTA — nothing in
the landscape table replicates LitDiscover's closed-corpus ground-truth recall validation — but
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
now read (`fulltext/`):

1. **Citation grounding — is any claim ever checked against its cited paper?** AutoSurvey's
   citation-quality metric (`h(c_i, Ref_i)`, an NLI check per claim) is the only reason it can
   claim citation recall/precision numbers at all. **LiRA goes further and is the strongest
   precedent found across all 6 papers:** it defines Citation Quality F1 (CQF1) — precision/recall
   over citation grounding — and beats AutoSurvey substantially on it (0.76/0.73 vs. ≤0.63) via a
   dedicated **Reviewer Agent** that checks intermediate outputs and triggers regeneration on
   failure. Audit: read `_write_theme_section`, the map-reduce path (`map_prompt`/`reduce_prompt`,
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
bounded fix, scope it" — mirroring how the related-work-landscape full-text benchmark worked.

**Status (2026-07-11): audit complete — verdicts below.** All 7 of 7 Tier 1/2 papers were
full-text verified first (see `related-work-landscape.md`'s round-2/round-3 notes), then
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

---

## Submission logistics (before June 30)

| Item | Issue | Status |
|---|---|---|
| Xiaobai's ORCID | Need for camera-ready `\orcid{}` block | ⏳ Ask PI |
| JCDL 2026 city | `\acmConference` currently says "Texas, USA" | ⏳ Verify exact city |
| Wohlin2014 pages | Using 321–330 (user's recall) | ⏳ Verify in ACM DL |
| PI review | Send PDF to Xiaobai by ~June 8 | ⏳ Not yet sent |

## Pre-submission content (believed resolved, session 15)

| Item | Issue | Believed status |
|---|---|---|
| Q1: Live experiments | K17-RGC ✅, Ge21-HSS ✅, Le25-GLLM ✅ (73.7%) | ✅ Resolved |
| Q2: Fig 7 k=5 vs k=20 | Check `cold_start_results_lowseed.json` | ✅ Believed resolved |
| Q3: Fig 6 non-monotone recall | Add paragraph explaining yield-stopping mechanism | ✅ Believed resolved |
| Q4: Pareto-80 vs Pareto-50 | Demonstrate Pareto-50 fails under yield-based stopping | ✅ Believed resolved |
| Q5: Random seeds > top-5 at round 1 | Run ≥5 trials; report mean ± std | ✅ Believed resolved |
| Q9: γ < 2 in Fig 1 | Add KS goodness-of-fit sentence | Low priority |
| Q10: Error bars Figs 5–6 | Run multiple trials for random/contaminated conditions | Low priority |
| Q11: [CITATION NEEDED] locations | Fill yellow-highlighted citations | ✅ Believed resolved |
| Q15: §5 yield lines overlap | Add sentence: threshold doesn't affect final recall | ✅ Believed resolved |

---

## Engine feature requests, from external use (2026-07-09) — 2 of 4 resolved same day

**✅ Resolved via the 2026-07-09 staged-workflow rework** (see `decisions.md`):
- The keyword-pre-filter idea → formalized as `litdiscover prefilter`.
- The related-work-mining idea → built as `litdiscover related-work-mine`.

**Still open:**
- `build_papers_json` still doesn't persist authors (see below).
- No Groq screening-backend fallback / no fast-fail on spend-cap errors (see below) — staged
  mode's manual `screen` step reduces the blast radius of this (no more silent 13-round burn),
  but the underlying gap in `screen/llm.py` itself is unchanged.

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
- **The keyword-relevance pre-filter approach worked well as a stand-in for LLM screening**
  and might be worth formalizing as an actual pipeline stage: a cheap deterministic
  keyword/regex triage *before* the expensive LLM screen, to cut obvious noise (in this case,
  ~2000 traversal candidates → ~135 "priority" candidates via a simple term-match) without
  burning API budget on papers that are clearly off-topic. Could reduce screening-round cost
  significantly on broad seed sets.
- **User's own idea while explaining this to Claude:** reading the *related-work prose* of
  the nearest-art papers (not just their raw reference list) surfaces framing/grouping and
  discussed-but-uncited context that pure citation-graph traversal can't recover. Might be
  worth a `litdiscover related-work-mine <paper_id>` mode that fetches full text (arXiv/OA
  where available) and extracts just the related-work section for a human to read, as a
  complement to graph traversal rather than a replacement.
