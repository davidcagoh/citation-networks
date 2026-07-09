# LitDiscover — Open Questions

All pre-submission content questions believed resolved (session 15). EasyChair submission filed 2026-04-21.
Remaining items are logistics / camera-ready only.

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
