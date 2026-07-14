# Discovery — Open Questions

Pulled out of `litdiscover/open-questions.md` (2026-07-14) as part of promoting Discovery to its
own study — see `roadmap.md`'s header. Everything below is specifically about the
traversal/screening phase (recall/precision validation, gold-set data quality, the pre-submission
discovery figures, screening-backend gaps); paper-logistics and synthesis/extraction items stayed
in `litdiscover/open-questions.md`.

---

## Pre-submission content — discovery/recall figures (believed resolved, session 15)

These are the original IP&M submission's discovery-validation content questions — the actual
figures/claims §4.0's end-to-end redesign will eventually need to reconcile with, not just
historical record.

| Item | Issue | Believed status |
|---|---|---|
| Q1: Live experiments | K17-RGC ✅, Ge21-HSS ✅, Le25-GLLM ✅ (73.7%) | ✅ Resolved — **now stale, see gold-set fix below** |
| Q2: Fig 7 k=5 vs k=20 | Check `cold_start_results_lowseed.json` | ✅ Believed resolved |
| Q3: Fig 6 non-monotone recall | Add paragraph explaining yield-stopping mechanism | ✅ Believed resolved |
| Q4: Pareto-80 vs Pareto-50 | Demonstrate Pareto-50 fails under yield-based stopping | ✅ Believed resolved |
| Q5: Random seeds > top-5 at round 1 | Run ≥5 trials; report mean ± std | ✅ Believed resolved |
| Q9: γ < 2 in Fig 1 | Add KS goodness-of-fit sentence | Low priority |
| Q10: Error bars Figs 5–6 | Run multiple trials for random/contaminated conditions | Low priority |
| Q15: §5 yield lines overlap | Add sentence: threshold doesn't affect final recall | ✅ Believed resolved |

**Q1 is the one item this list's "believed resolved" status doesn't survive `roadmap.md` §4.0's
findings intact.** The 73.7%-type live-survey recall headline is exactly the kind of
discovery-only number §4.0 argues can't be defended alone (it implied 0.03-0.45% precision once
checked, unscreened) — and it's computed against gold-sets since found to have data-quality bugs
(below). Resolve via §4.0's end-to-end harness, not by re-verifying the old number in isolation.

---

## Screening-backend gaps (from external use, 2026-07-09) — still open

Surfaced when litdiscover was driven from a different project
(`adaptive-learner`'s WAILS 2026 related-work search):

- **No configurable/pluggable screening backend despite `GROQ_API_KEY` sitting in `.env`.**
  `screen/llm.py` is hardcoded to Gemini; the README's claim of Groq as "an alternative screening
  backend" isn't wired up in code. A hard Gemini spend-cap failure (`RESOURCE_EXHAUSTED`) burned
  ~13 rounds retrying identically before being caught and killed manually — no automatic backend
  fallback, and no fast-fail (it just loops at 0% yield until `max_rounds`). Worth either wiring
  the Groq fallback for real, or making a spend-cap/quota error short-circuit the loop immediately
  instead of treating it as a stale round. **Directly relevant to §4.0's budget-control
  requirement** — a run that silently loops on a spend-cap error instead of failing fast breaks
  the "fixed, documented budget per run" checklist item.

**Resolved via the 2026-07-09 staged-workflow rework** (see `litdiscover/decisions.md`):
- The keyword-pre-filter idea → formalized as `litdiscover prefilter`. Originally surfaced as "a
  cheap deterministic keyword/regex triage before the expensive LLM screen, to cut obvious noise
  (in this case, ~2000 traversal candidates → ~135 'priority' candidates via a simple term-match)
  without burning API budget on papers that are clearly off-topic" — now shipped as its own staged
  CLI command, see `litdiscover/litdiscover/discovery/README.md` / `CLAUDE.md`.

---

## Gold-set data-quality bug (found 2026-07-14) — fix shipped, recall numbers still stale

**Found during `synthesis/representation-learning-plan.md`'s section-annotation pass on
Ge21-HSS:** 2 of 202 entries in `live-survey-eval/data/gold-sets/Ge21-HSS_gold.json` carried DOIs
pointing to completely unrelated papers ("A Meta-analysis: Effect of Stem Cells Transplantation
on Rehabilitation of Diabetes Mellitus with Limb Ischemia" and "A Review of the Scientific
Literature as it Pertains to Gulf War Illnesses" — neither has anything to do with human social
sensing).

**Not a one-off, confirmed after all 3 live-survey annotation passes:** K17-RGC's gold set had 4
unresolved entries too (3 near-duplicate/garbled records of the same textbook citations — e.g.
three separate "Random graphs" entries — plus a bare "CAMBRIDGE STUDIES IN ADVANCED MATHEMATICS"
series-name fragment with no paper title at all). Le25-GLLM (57/57 clean) is the exception, not
the rule.

**Root cause:** all 3 live surveys have a `survey_doi`/`survey_s2_id` configured in the `SURVEYS`
dict (`09_live_validation.py` lines 80-114), so `build_gold_set()` always calls
`build_gold_set_from_s2()` first, which succeeded for all 3 — meaning gold sets came from **S2's
own `/references` endpoint**, not PDF text parsing. The malformed titles are records **S2's own
citation graph links as references** of these survey papers — an S2-side data artifact, not a bug
in this codebase's parsing.

**Two automated filters tried and both reverted, same day, after measuring real false-positive
cost:** an all-caps/<3-words rejection, then a narrower series-name-phrase substring match. Both
sounded plausible but were empirically wrong — a live re-fetch showed each one rejecting far more
*real, correctly-cited* references than actual garbage (Goodman's "Snowball sampling", Munkres'
"ELEMENTS OF ALGEBRAIC TOPOLOGY", Epstein's "Agent_Zero... (Princeton Studies in Complexity)" all
wrongly caught). No automated filter ships — the actual fix was manual, surgical removal of the
confirmed-bad entries directly from each gold-set JSON: Ge21-HSS 202→200, K17-RGC 56→52.
Consistent with `build_gold_set`'s own existing design contract ("manual corrections survive
re-runs").

**Confined to the 3 live surveys, structurally.** The 3 APS closed-corpus gold sets
(`closed-corpus-eval/data/outputs/ground_truth.json`) are built directly from the APS
citation-edge CSV (a DOI→DOI join on structured data), with no S2 API or title-matching step at
all — this failure mode cannot occur there. No further audit needed on the APS side.

**Effect on already-reported numbers:** these spurious gold entries were papers the surveys never
actually cite, so traversal could structurally never find them correctly — counting them in the
denominator made every previously reported live-survey recall number (the 73.7-100% headline,
`roadmap.md` §4.3's per-operator table) a slight *underestimate*. Now that the 6 confirmed-bad
entries are removed (Ge21-HSS 202→200, K17-RGC 56→52), those numbers are stale and should be
recomputed — small expected effect (6 entries across 258 total), not urgent on its own, but
**should be folded into §4.0's end-to-end harness build rather than fixed in isolation** — no
point recomputing the old isolated-discovery-recall number against the corrected gold-sets only
to have §4.0 supersede it anyway.

Full per-survey counts in `../synthesis/representation-learning-plan.md` §3.2.
