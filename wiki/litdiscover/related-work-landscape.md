# Related-work landscape — automation systems close to LitDiscover

**Living document — update in place as new close hits surface, don't spawn a new report file
for the next batch. Add rows/tiers here instead.**

**Source:** hand-eyeballed from the 366 `included` papers in `automated-lit-review-methodology`
(litreview-v2 Supabase project, pulled 2026-07-10). Full CSV: `included_366_2026-07-09.csv`.

**Why this exists:** IP&M's desk-rejection said LitDiscover's paper was missing SOTA/LLM
baselines and current-year references. This is the redo's related-work backbone — every system
here does *some* version of what LitDiscover does (discover → filter → synthesize literature
with LLM assistance), so the paper's Related Work section needs to place LitDiscover against all
of them, not just the two or three most obviously similar.

Tiering below is by how much a reader would expect direct comparison, not by citation count.

**Longer-term goal (2026-07-10):** beyond satisfying the IP&M reviewers, the point of this table
is to actually understand the current related-work landscape — motivation, scope, lineage,
architecture, and eval method for each close-hit system — well enough that `rld` (the
`robust-literature-discovery` reproducibility repo) stops being built in the dark. Previously the
paper's related-work section was written without this grounding; this table is meant to make
`rld` complete against what the field has actually already tried, not just against reviewer
feedback on one submission.

**Full-text benchmark verdict (2026-07-10):** pulled full PDFs for 3 of 7 Tier 1/2 papers
(AutoSurvey, ProfOlaf, LitLLMs-are-we-there-yet — archived in `fulltext/`) to check Gemini's
abstract-only extraction against ground truth. **Verdict: worth pulling the remaining 4.**
AutoSurvey's cells were accurate, but ProfOlaf's Evaluation cell was flatly wrong (abstract-only
extraction said "no quantitative benchmark" when the paper has a full LLM-vs-human screening
comparison — see corrected row below), and LitLLMs' architecture cell missed a real nuance
(embedding-based re-ranking beats LLM-prompting re-ranking in their own results). One clear miss
and one partial miss out of three is a high enough error rate to justify full-text passes on
SciReviewGen, LitLLM, LiRA, and Human-Centred Research Automation before finalizing the redo's
Related Work section.

**Full-text pull, round 2 (2026-07-10):** pulled 3 more — SciReviewGen, LitLLM, LiRA (all archived
in `fulltext/`). All three table entries confirmed accurate on re-read. The round-2 pulls surfaced
two things beyond correctness-checking: (1) SciReviewGen and LitLLM independently name the exact
same bottleneck — abstracts-only input causes hallucination/factuality failure — which bears
directly on whether LitDiscover's synthesis (fed only structured extraction fields) has the same
problem in a different shape; (2) **LiRA has a working, benchmarked citation-grounding metric
(CQF1) and Reviewer Agent** that is the single most directly reusable precedent found — see the
Extract/Synthesize Technique Audit in `open-questions.md`.

**Full-text pull, round 3 (2026-07-11):** Human-Centred Research Automation obtained (user
supplied the PDF directly — ACM DL is paywalled, no open-access mirror was findable) and read.
Table entry confirmed accurate, with one new nuance: their own classical-vs-LLM filter comparison
(60–68% for cheap methods vs. 71% for Llama 3.1) is a real data point supporting the economics of
`prefilter`-before-`screen`. **All 7 of 7 Tier 1/2 papers now have full-text verification** — the
related-work-landscape benchmarking pass is complete.

---

## Tier 1 — canonical lineage (must cite, even briefly)

The field's own citation graph: SciReviewGen supplies the training/eval data most others use;
AutoSurvey is the most-cited architecture and the benchmark everyone downstream compares against;
LitLLM/LitLLMs is the same team's two-paper arc; LiRA explicitly benchmarks against AutoSurvey.

| Paper | Year / cites | Motivation | Scope | Architecture | Evaluation |
|---|---|---|---|---|---|
| **SciReviewGen** (ACL) | 2023 / 26 | No large dataset existed for training/evaluating automatic review generation | Dataset + baseline eval, not a live tool | 10k literature reviews + 690k cited papers; Fusion-in-Decoder summarization baseline | **Confirmed from full-text read (2026-07-10), table entry was accurate**, plus a load-bearing nuance: their own §5.3 root-causes the hallucination/factuality failures directly to feeding **abstracts-only** (not full text) as source material — "hallucinations tend to occur when the target text contains a large amount of information absent from the source." Directly relevant since LitDiscover's `synthesizer.py` feeds even less than an abstract into generation (only structured extraction fields, per `litdiscover/CLAUDE.md`) — open question for the extract/synthesize audit is whether that's a mitigation (curated signal) or the same bottleneck in a different shape. |
| **AutoSurvey** (NeurIPS) | 2024 / 123 | Survey-writing doesn't scale with publication volume; context-window and parametric-knowledge limits block naive LLM use | Full survey generation, arbitrary AI subfields | Retrieval → outline generation → specialized-LLM subsection drafting → integration/refinement → iterate | **Confirmed from full-text read (2026-07-10), table entry was accurate.** Ablation shows the retrieval step is the load-bearing piece (removing it drops citation recall 83.48%→60.11%), and citation quality stays stable as survey length grows while naive RAG degrades — the closest existing precedent for LitDiscover's own "retrieval structure explains why the algorithm works" argument (§5 of `background.md`). Multi-LLM-as-judge eval, Spearman ρ=0.54 vs. human rankings at best. |
| **LitLLM** (arXiv) | 2024 / 71 | Related-work writing is tedious; existing LLM approaches hallucinate and miss recent work | Related-work section generation from a query abstract | Web search → LLM keyword extraction → re-rank by abstract similarity → single-pass RAG generation | **Confirmed from full-text read (2026-07-10), table entry was accurate** — preliminary 5-researcher user study only, no formal benchmark. Their own Future Work section names the identical bottleneck as SciReviewGen: "This work only considered abstracts... which creates a bottleneck in effective literature review generation" and explicitly wants to move to full-text ingestion. Two independent teams naming the same abstracts-only bottleneck is a strong signal for the extract/synthesize audit. |
| **LitLLMs, are we there yet?** (TMLR) | 2024 / 21 | Same team as LitLLM, deeper: is LLM-assisted review writing actually viable? | Retrieval + generation, decomposed and separately measured | Two-step keyword-extraction retrieval + prompting-based re-ranking (doubles recall vs. naive search) + plan-then-write generation | **Confirmed from full-text read (2026-07-10), with one correction:** the "prompting-based re-ranking" architecture cell is only half the picture — their own Fig 2 shows **embedding-based (SPECTER2) re-ranking outperforms LLM-prompting re-ranking**, and GPT-4-as-reranker is fragile in practice (produces an incomplete ranked list 40%+ of the time, Table 2). Introduces a **rolling, contamination-free eval protocol** using new arXiv papers — directly relevant if LitDiscover's APS-simulation validation faces a similar staleness critique. |
| **LiRA** (AAAI) | 2025 / 5 | Retrieval/screening automation is mature; the *writing* phase (readability, factual accuracy) is under-explored | Full review article writing, not just related-work sections | Multi-agent: outliner, subsection writer, editor, reviewer | **Confirmed from full-text read (2026-07-10), table entry was accurate — and this is the single most directly reusable precedent found across all 6 papers read.** LiRA defines **Citation Quality F1 (CQF1)**, an explicit precision/recall metric for citation grounding (penalizes both irrelevant/hallucinated citations and missing-but-necessary ones), and beats AutoSurvey substantially on it (0.76/0.73 vs. ≤0.63 across two datasets). Its **Reviewer Agent** evaluates intermediate outputs (outline, section) against completeness/transparency/clarity/contribution and triggers up to 3 regeneration rounds if a component fails threshold — this is a working, benchmarked answer to audit item #1 (citation grounding check) and a second concrete precedent (alongside the Outline Drafter Agent) for audit item #2 (plan-before-write). Citation is grounded via full article titles during generation (not placeholder numbers), then post-processed into numbered refs — worth comparing against LitDiscover's short-ID (`P1…Pn`) approach in `synthesizer.py`. |

## Tier 2 — nearest architectural neighbors (deserve a real compare/contrast paragraph)

These two overlap LitDiscover's actual design decisions, not just its problem statement.

| Paper | Year / cites | Motivation | Scope | Architecture | Evaluation |
|---|---|---|---|---|---|
| **ProfOlaf** (arXiv) | 2025 / 0 | Existing tools support only isolated SLR steps, leaving the rest manual and error-prone | Article collection + selection + topic extraction + Q&A over corpus | **Iterative snowballing with human-in-the-loop filtering** (closest match to LitDiscover's staged mode), LLM-assisted selection; CLI + web app | **Correction from full-text read (2026-07-10): has a real quantitative benchmark, abstract undersold it.** 7-iteration snowball on 1009 retrieved → 108 included (11% overall efficiency). LLM-vs-human screening compared directly: LLM full-content screening F1=0.928 vs. human F1=0.927 — essentially on par, LLM slightly higher precision (0.942 vs 0.931), lower recall (0.915 vs 0.922), i.e. more conservative. Also evaluates topic-modeling (TopicGPT: 45–54% ground-truth topic match) and summarization quality (Likert, faithfulness 4.9/5). **Directly reusable as an external LLM-screening-accuracy benchmark for LitDiscover's own `screen` stage.** |
| **Human-Centred Research Automation** (HCAIep) | 2026 / 1 | Agentic automation must preserve trust/transparency per EU AI Act + HCAI principles | Literature **discovery, filtering, and gap identification** — nearly LitDiscover's own three-verb framing | Agentic AI pipeline, human oversight retained at later stages, structured outputs (gaps, directions, candidate solutions) | **Confirmed from full-text read (2026-07-11, user supplied the PDF directly — ACM DL is paywalled with no open-access mirror), table entry was accurate.** 71.05% figure confirmed exact. Useful nuance not in the abstract: their own head-to-head (Table 2) shows Llama 3.1 (71.05%) beats classical/embedding filters — SentenceBERT 68.49%, TF-IDF 63.83%, BM25 62.83%, FAISS+SciBERT 60.20% — by only 3–11 points, at 10–30s/abstract vs. near-instant for the classical methods. Relevant to LitDiscover's own `prefilter`-before-`screen` tradeoff: a free keyword/embedding pass getting within ~10 points of LLM accuracy is exactly the economics that justify prefiltering before spending on Gemini `screen`. |

## Tier 3 — same subfield, one-line mention sufficient

| Paper | Year / cites | One-line differentiator |
|---|---|---|
| **SurveyGen** (EMNLP) | 2025 / 8 | New 4,200-survey dataset + quality-aware retrieval (QUAL-SG); honest about fully-automatic generation still being weak on citation quality/critical analysis — useful contrast point if LitDiscover claims stronger discovery precision |
| **SurveyGen-I** (IJCNLP-AACL) | 2025 / 2 | Coarse-to-fine retrieval + memory-guided writing, targets long-survey coherence specifically |
| **SGSimEval** | 2025 / 4 | Not a generator — an **evaluation benchmark** for ASG systems with human-preference metrics; potential citation for LitDiscover's own eval methodology, not a competing system |
| **System for SLR using multiple AI agents** (arXiv) | 2024 / 41 | Full pipeline (search string → title filter → abstract filter → per-RQ analysis), open-sourced; closest architectural shape to LitDiscover's traverse→prefilter→screen→extract staging among the 2024 cohort |
| **Scholar Augment** | 2026 / 0 | End-to-end multi-LLM platform, headline metric is 99.32% extraction-time reduction on 592 articles — scope overlaps broadly but optimizes for a different outcome (speed, not discovery recall) |
| **IntrAgent** | 2026 / 1 | Different task (content-grounded retrieval via two-stage Section Ranking + Iterative Reading, own IntraBench benchmark) — cite only if framing "reading behavior mimicry" as a design lineage |

## Excluded from comparison (false positives from keyword match)

- **Autonomous Knowledge Pipeline** (2026) — AI-paper-to-YouTube-video pipeline, not review methodology
- **Vakya** (2026) — generates IEEE papers from GitHub repos, not literature synthesis

---

## What this means for the paper

1. **Related Work needs a lineage paragraph** (Tier 1: SciReviewGen → AutoSurvey → LitLLM →
   LiRA) rather than five isolated citations — this is literally how the subfield already cites
   itself (LiRA names AutoSurvey as a baseline).
2. **Two systems need direct differentiation, not just citation**: ProfOlaf (same human-in-the-loop
   philosophy — the contrast is *what* is human-gated and *when*) and Human-Centred Research
   Automation (nearly identical framing — the contrast is APS-simulation empirical validation vs.
   their HCAI-compliance framing).
3. **LitLLMs' rolling contamination-free eval protocol** is worth addressing head-on if a reviewer
   could raise the same staleness concern against LitDiscover's APS-simulation-based validation.
4. **SGSimEval** is a candidate citation for eval *methodology*, separate from the competitor list.

## Next step

Not yet decided whether to pull full PDFs for Tier 1+2 (7 papers) vs. working from abstracts only
for the redo. Abstracts above are verbatim from Semantic Scholar (`papers.abstract`), not written
by us — flagged as untrusted external data when pulled, quote-checked before reuse in the paper.
