# Is there a mature evaluation standard for synthesis quality? No.

Built 2026-07-14, pulled out of `reference-implementation-survey.md`'s code-plus-paper
audit into its own doc because it's a gap-analysis finding in its own right, not a footnote to the
implementation survey. Relevant to Synthesis-paper positioning specifically because — per
`q-synth-plan.md`'s own framing — AutoSurvey/SurveyX/PROMPTHEUS/etc. are "background, not
competitors": this doc is the evidence for *why* their evaluation methodology doesn't set a bar
Q-SYNTH needs to clear, because no validated bar exists yet for the "synthesis" construct itself.

---

## What a mature standard would require, vs. what exists

| Maturity criterion | Status in this corpus |
|---|---|
| A metric everyone reuses, not reinvents | **Partially met** — AutoSurvey's citation-NLI check and coverage/structure/relevance LLM-judge rubric got literally copied: LiRA's CQF1, SurveyX's extension, SurveyGen-I's 5-axis version |
| Validated correlation with human judgment | **Not met** — AutoSurvey's own meta-eval only reaches Spearman ρ≈0.5429 even with a mixture of judges; SurveyX found human raters *stricter* than the automated judge, especially on Structure; SciReviewGen's ROUGE-based system was preferred by humans only 22.2% of the time vs. 68.9% for ground truth — metric and human preference pointed in opposite directions |
| A shared benchmark/test set (leaderboard-style) | **Not met** — nearly every system builds its own: SciReviewGen's dataset, SurveyGen's 4,205-survey dataset, AutoSurvey's 20 LLM topics (reused by SurveyX but not SurveyGen or SurveyGen-I, which each built their own 6-domain/multi-topic benchmarks), Meow's self-constructed 100-survey set |
| Same judge model/prompt across papers | **Not met** — GPT-4o-mini, GPT-4, Claude-3-haiku, Gemini-1.5-pro all used as judges across different papers, with different rubric axis counts (3-axis vs. 5-axis) |
| A validated ground truth for "good synthesis" itself | **Not met** — every system defers to human-written surveys as gold, but those vary widely in quality/scope with no controls, and no system validates that "matches a human survey" is the right target in the first place |

---

## The specific gap that matters most here

The axis closest to what "synthesis" actually means — as opposed to citation mechanics or
structural templating — is the *least* measured of all. Only two systems in the corpus even
attempt a distinct sub-score for it:

- **SurveyGen-I**'s "Synthesis" sub-dimension showed the single largest gain of any sub-metric in
  the whole corpus (+0.41 over the strongest baseline) — meaning synthesis was the weakest prior
  capability, precisely where the most headroom existed.
- **SurveyX**'s "Critical Analysis" axis, plus its own admission that even after winning on citation
  precision/recall it still trails human reference-relevance (IoU 0.55, LLM-judged relevance 0.7689
  vs. human's 0.9485).

Neither system validates its synthesis/critical-analysis sub-score against human judgment
*separately* from the aggregate score — the one meta-validation effort that exists in this whole
corpus (AutoSurvey's ρ≈0.54) was computed on the overall judge score, not per-axis. So the
construct this field's own papers agree is hardest and least solved is also the one with zero
independent validation of its measurement instrument.

---

## The honest comparison point

This is roughly where machine translation was before BLEU — except less validated. MT accumulated
decades of correlation studies across many language pairs before BLEU became a trusted (if flawed)
proxy for human judgment. Here, each paper runs one meta-validation study, once, on its own
benchmark, and the next paper doesn't re-check it — it reuses the code (AutoSurvey → LiRA → SurveyX)
without re-validating the ρ≈0.54 correlation that code implies. That's citation-count-driven
convergence toward a shared implementation, not validation-driven convergence toward a trustworthy
one.

---

## Implication for Q-SYNTH / the Synthesis paper

Two options this opens up, not mutually exclusive:

1. **Positioning claim**: state explicitly in the Synthesis paper's related-work/background section
   that no validated synthesis-quality standard exists for the LLM-narrative-generation line of
   work — which is exactly the "cite as background, not competitors" framing `q-synth-plan.md`
   already calls for, now with the specific evidence to back the claim rather than asserting it.
2. **A different validation target entirely**: since Q-SYNTH doesn't generate narrative text, it
   isn't exposed to this gap directly — its own success criteria (`q-synth-plan.md`'s "Success
   criteria" section: cluster
   interpretability, temporal-ordering plausibility, expert recognition of foundational papers) are
   a genuinely different, more tractable validation problem than "is this generated prose good
   synthesis." Worth stating that difference explicitly too, since a reviewer familiar with the
   AutoSurvey-style literature might otherwise expect Q-SYNTH to be held to the same (unvalidated)
   bar.
