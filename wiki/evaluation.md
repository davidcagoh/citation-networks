# Evaluation

Cross-cutting eval-methodology findings that apply to more than one pipeline stage/project —
pulled out 2026-07-31 after the same eval-standard-gap finding had been independently
cross-referenced between `litdiscover/litdiscover.md` and `synthesis/synthesis.md` three separate
times (session 45's consolidation, then session 45's own rereading of `deep-dives.md`, then this
session's stage-by-stage disambiguation). Zeitgeist has no stake in this file — it's LitDiscover
(Discovery/Screening/Extraction) + Synthesis only. Stage-specific findings (LitDiscover's own
operator benchmarks, Q-SYNTH's rigor bar) stay in their own project files; this file is only for
what's shared.

---

## Which eval methods actually apply to which claim

LitDiscover's four pipeline stages support four different, separable claims — "we discover
better," "we screen better," "we extract better," "we synthesize better." Sorting every eval
method found across the 27+5-method `../reference-systems/deep-dives.md` corpus (Table 1/2 there)
by which claim it would actually support, not just which claim a paper says it supports:

### Discovery ("we find better candidates")

| Method | Used by | What it actually measures |
|---|---|---|
| RollingEval (Aug/Dec cutoff) | LitLLM / LitLLMs-are-we-there-yet | Contamination-free retrieval+re-rank recall, arXiv-post-cutoff — closest thing to a purpose-built discovery metric in the corpus |
| IoU / semantic / LLM-judged reference relevance | SurveyX | Retrieved references checked against a human-curated reference set — same shape as LitDiscover's own operator-recall benchmark (`litdiscover/protocol-log.md`) |
| Wohlin SLR efficiency metric | ProfOlaf | included/candidates-examined per snowball iteration — efficiency of the search loop itself, closest analog to LitDiscover's own cycle-yield stopping rule |
| SYNERGY (proposed, not yet used by anyone for discovery) | — | See "SYNERGY vs. CLEF TAR" below — would be the first externally validated, shared discovery benchmark in the corpus if its reference field checks out |

**Only 3 borrowed fragments, no purpose-built shared benchmark, nobody externally validates
against a shared corpus.** The thinnest-supported claim category — which tracks with why
LitDiscover's own operator work has had to build its own 3-survey benchmark from scratch
(`litdiscover/protocol-log.md`'s Run log).

### Screening ("we filter better")

Real, decades-old, externally validated standards exist: SYNERGY, CLEF TAR, Clinical Hedges,
Cochrane Crowd, CAMARADES/NIEHS-OHAT (shared corpora) + Cohen's Kappa, confusion-matrix P/R/F1,
WSS@95 (validated statistics, not field-invented ones). **Best-supported claim category in the
whole corpus.** The gap here is comparability, not validity — see below. LitDiscover's own
`screen_batch()` has never been run against any of these (`litdiscover/litdiscover.md`'s Prior Art
section).

### Synthesis ("we write a better review")

CQF1, Multi-LLM-as-Judge, Prometheus-2, SGSimEval, SurveyLens, Tree Edit Distance, KPR, ROUGE,
FRES + SciReviewGen as shared training/eval corpus. Real lineage, real reuse — but the one
meta-validation against human judgment that exists in this whole literature (AutoSurvey's
ρ≈0.54) was never repeated by anyone who copied the metric. The validity gap — full detail below.

### Extraction ("we pull structured facts out better")

IntraBench (IntrAgent) is the only candidate, and it's not really a match — single-paper
content-grounded QA, not structured multi-field extraction fidelity (LitDiscover's own 11-field
schema: research_questions/contributions/methodology/datasets/metrics/key_results/etc.). Scholar
Augment explicitly reports "no accuracy eval" for its own extraction step. **Close to a total
void** — not a validity gap or a comparability gap, just nothing there at all across 27+5 systems.

**Honest ranking, worst-to-best-supported by existing infrastructure:** Extraction (nothing to
borrow) < Discovery (thin borrowed fragments, no shared benchmark) < Synthesis (real lineage,
unvalidated) < Screening (real validated standards, just untested against). If LitDiscover's
actual focus is Discovery, that's exactly the stage with the least existing infrastructure to
lean on.

---

## SYNERGY vs. CLEF TAR — not interchangeable

Both get cited together as "the field's screening benchmarks," but they're structurally different
and support different experiments:

- **CLEF TAR** (CLEF eHealth's Technology Assisted Reviews track): 50 SR topics in 2017 (20
  train/30 test), 80 in 2018, ~130 in 2019. Each topic ships the review title, the Boolean search
  query used, the retrieved document set, and abstract-/full-text-level relevance labels. **No
  citation graph** — the candidate pool is handed to you pre-retrieved. Screening-only; nothing to
  traverse. Task shape is ranking-for-screening-prioritization, not binary classification.

- **SYNERGY** (`github.com/asreview/synergy-dataset`, De Bruin/Ma/Ferdinands/Teijema/Van de Schoot
  2023): 169,288 records from 26 completed systematic reviews, only 2,834 (1.67%) actually
  included — built for extreme class-imbalance stress-testing. Sourced from OpenAlex; per the
  dataset's own docs, **each record carries the OpenAlex IDs of works it cites plus a citation
  count** — a real citation graph, not just metadata. In principle this means SYNERGY could also
  support a discovery-recall experiment: seed LitDiscover's operators from a known subset of one
  of its 26 reviews' included papers, traverse the OpenAlex reference graph the same way
  backward/forward/co-citation traverse S2, and check recall against the rest of that review's
  real included set — a second, externally-published closed corpus for the operator-composition
  work (`litdiscover/protocol-log.md`), not just APS.

**Verified against the raw data (2026-07-31), across 7 of the 26 reviews.** Downloaded via the
`synergy-dataset` pip package (yields full `pyalex.Work` objects, not the GitHub repo's
identifiers-only CSVs) and checked `referenced_works` directly — coverage is consistently strong
across size and domain (60–99% of records have a populated reference list, depending on review;
mean 11–53 references where present). The two CS-domain reviews in the corpus (`Hall_2012`,
`Radjenovic_2013` — closest to LitDiscover's own topic space) have the *highest* coverage, 92–94%.
**The discovery-recall experiment below is viable**, not just theoretical — full per-review table
and the candidate review for the actual experiment (`Hall_2012`) in
`evals/synergy-eval/README.md`.

A screening comparison against these two (`screen_batch()` vs. ASReview's 83%/SWIFT-Review's 54%
WSS@95) would be low-risk and viable today — **deliberately not pursued** (see Open questions
below): LitDiscover's claim is about Discovery, and Screening already has the best-supported eval
infrastructure of the four stages, making its comparability gap the least valuable one to close.

---

## SYNERGY `Hall_2012` results (2026-08-01)

Code: `evals/synergy-eval/` (55/55 tests, TDD throughout). Full config/methodology in
`litdiscover/protocol-log.md`'s Run log; this section is the numbers.

**Step 1 — isolated 5-operator baseline** (BWD/FWD/AUTH/VENUE + CO reconstructed as `FWD∘BWD`,
top_k seeds, k∈{1,2,3}):

| Operator | recall @k=3 | precision @k=3 |
|---|---|---|
| BWD | 3.0% | 75% |
| FWD | 36.6% | 43% |
| AUTH | 4.0% | 50% |
| VENUE | 9.9% | 23% |
| CO | 28.7% | 49–65% |

CO is the best recall/precision balance — **replicates the 2026-07-14 live-survey finding on a
second, independent corpus**, not a fluke of one dataset. FWD is unexpectedly strong here (37%
recall) versus dead on live S2 (+0/+1/+0 gold, 2026-07-14): closed-corpus forward traversal only
reaches papers already inside Hall_2012's own screened pool — on-topic by construction — unlike
open-web forward citations, which reach mostly off-topic citers. FWD's weakness is
corpus-shape-dependent, not universal.

**Step 2 — composition sweep**, 12 hand-picked sequences × 3 modes (isolated / chained-unfiltered
/ chained-filtered-by-gold-label) × 9 seed conditions (126 conditions total):

- **Best condition: `BWD→FWD→CO→VENUE`, chained-unfiltered, k=3 — 76.2% recall, 27.2% precision.**
- **Chaining beats isolated-union almost everywhere** — e.g. `BWD→FWD→AUTH` chained: 50.5% recall
  vs. 11.9% isolated. Refines the single 2026-07-14 rejected chaining result (`FWD unfiltered +
  citation-count frontier`, both recall and precision worse) — that finding was about *that
  specific unfiltered design*, not chaining in general.
- **Filtering's effect on precision has no universal sign — it depends on which operator it
  precedes**, confirmed via per-stage diagnostics (multiplier, marginal gold) at contaminated
  seeds, k=3/2-wrong:

  | Sequence | stage-2 multiplier (unfilt.→filt.) | marginal gold (unfilt.→filt.) | stage-2 precision |
  |---|---|---|---|
  | `BWD→FWD` | 6.58 → 4.67 | 17 → 17 (unchanged) | 21.5% → 60.7% |
  | `FWD→BWD` | 2.83 → 3.75 | 9 → 7 (lost 2) | 52.9% → 46.7% |

  Filtering before `FWD` (a high-fan-out operator) strips noise for free — same true positives,
  far fewer false ones. Filtering before `BWD` (not a multiplier) costs real finds — some of the
  filtered-out non-gold `FWD` candidates were legitimate bridge nodes `BWD` would have profitably
  explored.
- **Two clean negatives**: `FWD→FWD` (repeated forward) is dead everywhere, ~1% recall regardless
  of mode or k. Any sequence ending in `VENUE` craters precision (13–27% vs. 44–80% for
  non-`VENUE` chains) — consistent with `VENUE`'s null isolated result above.
- **Stage overlap** (Jaccard of raw candidates, kitchen-sink chain): `BWD↔CO` and `FWD↔CO` both
  exactly 0% — CO finds nothing redundant with either traversal operator here, a local,
  exact-number replication of `live-survey-eval/11_redundancy_check.py`'s finding that co-citation
  isn't redundant with forward traversal.
- **Simulated yield-stop**: production's existing `core/loop.py` `YIELD_THRESHOLD=0.05` stopping
  rule would already have cut `BWD→BWD`, `FWD→FWD`, and every isolated-mode `VENUE` sequence short
  — no new mechanism needed to avoid those specific dead ends.

**A bug caught and fixed mid-build, not silently corrected**: the overlap diagnostic was
initially computed from `new_candidates` (each stage's contribution *after* dedup against
everything found by earlier stages) — which is disjoint across stages by construction, so it read
`0.0` for every pair regardless of what the operators actually found. Fixed by computing overlap
from `raw_candidates` (pre-dedup) instead; caught via a regression test before any of the numbers
above were reported.

---

## The eval-standard gap (synthesis-side) — read this before citing any survey-generation system as a benchmark

**No mature evaluation standard exists for synthesis/survey-generation quality**, anywhere in the
LLM-narrative-generation literature (AutoSurvey, SurveyX, LiRA, SurveyGen-I, etc.). Positioning
material for both `synthesis/synthesis.md`'s Q-SYNTH and representation-learning tracks — it's the
evidence for why that literature's evaluation methodology doesn't set a bar either track needs to
clear, since no validated bar exists yet for the "synthesis" construct itself.

| Maturity criterion | Status in this corpus |
|---|---|
| A metric everyone reuses, not reinvents | Partially met — AutoSurvey's citation-NLI check + LLM-judge rubric got copied near-verbatim: LiRA's CQF1, SurveyX's extension, SurveyGen-I's 5-axis version |
| Validated correlation with human judgment | **Not met** — AutoSurvey's own meta-eval only reaches Spearman ρ≈0.5429 even with a mixture of judges; SurveyX found human raters *stricter* than the automated judge; SciReviewGen's ROUGE-based system was preferred by humans only 22.2% of the time vs. 68.9% for ground truth — metric and human preference pointed opposite directions |
| A shared benchmark/test set | **Not met** — nearly every system builds its own (SciReviewGen's dataset, SurveyGen's 4,205-survey dataset, AutoSurvey's 20 LLM topics, Meow's self-constructed 100-survey set) |
| Same judge model/prompt across papers | **Not met** — GPT-4o-mini, GPT-4, Claude-3-haiku, Gemini-1.5-pro all used as judges, different rubric axis counts (3-axis vs. 5-axis) |
| A validated ground truth for "good synthesis" itself | **Not met** — every system defers to human-written surveys as gold, but no system validates that "matches a human survey" is the right target in the first place |

**The specific gap that matters most:** the axis closest to what "synthesis" actually means — not
citation mechanics, not structural templating — is the *least* measured of all. Only SurveyGen-I
(its "Synthesis" sub-dimension showed the single largest gain of any sub-metric in the whole
corpus, +0.41 over the strongest baseline — meaning synthesis was the weakest prior capability,
exactly where the most headroom existed) and SurveyX (its "Critical Analysis" axis, plus its own
admission that even after winning on citation precision/recall it still trails human
reference-relevance, IoU 0.55) even attempt a distinct sub-score for it. Neither validates that
sub-score against human judgment *separately* from the aggregate — the one meta-validation effort
that exists in this corpus (AutoSurvey's ρ≈0.54) was computed on the overall judge score, not
per-axis. The construct this field's own papers agree is hardest and least solved is also the one
with zero independent validation of its measurement instrument. Roughly where machine translation
was before BLEU — except less validated: each paper runs one meta-validation study, once, on its
own benchmark, and the next paper reuses the code (AutoSurvey → LiRA → SurveyX) without
re-checking the correlation that code implies. Citation-count-driven convergence toward a shared
implementation, not validation-driven convergence toward a trustworthy one.

**Screening's gap is a different shape — comparability, not validity.** Real, decades-old,
externally validated standards exist for screening (Cohen's Kappa, WSS@95, confusion-matrix P/R/F1
computed against SYNERGY/CLEF TAR/Clinical Hedges) — the gap is that almost nobody outside the
direct ASReview/SWIFT-Review/RobotSearch lineage tests against them, and even within that lineage
older tools never get retroactively re-benchmarked once a newer shared corpus (SYNERGY) appears.
Discovery's gap is thinner still — only 3 borrowed metric fragments exist at all, no shared
benchmark, see the by-stage table above. Three genuinely different failure modes wearing the same
"no eval standard" label — worth keeping distinct rather than citing as one undifferentiated gap.

**Implication:** state explicitly in any Synthesis-facing writing that no validated
synthesis-quality standard exists for the LLM-narrative-generation line of work — the "cite as
background, not competitors" framing this project already uses, now with specific evidence behind
it. Separately: since Q-SYNTH doesn't generate narrative text, it isn't exposed to this gap
directly — its own success criteria (cluster interpretability, temporal-ordering plausibility,
expert recognition) are a genuinely more tractable validation problem than "is this generated
prose good synthesis," worth stating explicitly since a reviewer familiar with the AutoSurvey-style
literature might otherwise expect Q-SYNTH held to that same unvalidated bar.

---

## Open questions

- ~~Pull an actual SYNERGY dataset file and inspect the reference field directly~~ — **done
  2026-07-31**, verified real and usable, see above.
- ~~Check `referenced_works` coverage density across reviews~~ — **done 2026-07-31**, 7/26 checked
  (small/medium/large, both CS-domain reviews), consistently strong, `Hall_2012` identified as the
  best candidate for the actual experiment.
- ~~Design and run the seed-subset/traverse/recall experiment against `Hall_2012`~~ — **done
  2026-08-01**, isolated baseline + 126-condition composition sweep with per-stage diagnostics, see
  results section above. Not extended to the other 25 reviews yet — open if this needs to become a
  multi-review claim rather than a single-review one.
- Explain the `FWD→BWD` contaminated-seed precision dip (52.9%→46.7% with filtering) more
  rigorously than "some non-gold candidates were bridge nodes" — currently a single-condition
  observation, not verified across other sequences/k values.
- ~~Run LitDiscover's `screen_batch()` against SYNERGY/CLEF TAR~~ — **dropped 2026-07-31,
  deliberately not pursued.** LitDiscover's actual claim is about Discovery, not Screening;
  Screening already has the best-supported eval infrastructure of the four stages (real,
  decades-old, externally validated standards — see the by-stage table above), which is exactly
  why closing its comparability gap isn't worth the effort here. If a reviewer asks how
  LitDiscover's screening compares to prior work, ProfOlaf's own human-vs-LLM near-parity finding
  (F1 0.928 vs. 0.927 human, `litdiscover/litdiscover.md` Prior Art) is existing evidence LLM
  screening is competitive — no new number of our own needed.
