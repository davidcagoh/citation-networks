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

---

## Tier 1 — canonical lineage (must cite, even briefly)

The field's own citation graph: SciReviewGen supplies the training/eval data most others use;
AutoSurvey is the most-cited architecture and the benchmark everyone downstream compares against;
LitLLM/LitLLMs is the same team's two-paper arc; LiRA explicitly benchmarks against AutoSurvey.

| Paper | Year / cites | Motivation | Scope | Architecture | Evaluation |
|---|---|---|---|---|---|
| **SciReviewGen** (ACL) | 2023 / 26 | No large dataset existed for training/evaluating automatic review generation | Dataset + baseline eval, not a live tool | 10k literature reviews + 690k cited papers; Fusion-in-Decoder summarization baseline | Human eval: some machine summaries comparable to human-written; documents hallucination + missing-detail failure modes |
| **AutoSurvey** (NeurIPS) | 2024 / 123 | Survey-writing doesn't scale with publication volume; context-window and parametric-knowledge limits block naive LLM use | Full survey generation, arbitrary AI subfields | Retrieval → outline generation → specialized-LLM subsection drafting → integration/refinement → iterate | Own eval benchmark + iterative refinement loop; open-sourced |
| **LitLLM** (arXiv) | 2024 / 71 | Related-work writing is tedious; existing LLM approaches hallucinate and miss recent work | Related-work section generation from a query abstract | Web search → LLM keyword extraction → re-rank by abstract similarity → single-pass RAG generation | No formal benchmark reported in abstract; positioned as toolkit/demo |
| **LitLLMs, are we there yet?** (TMLR) | 2024 / 21 | Same team as LitLLM, deeper: is LLM-assisted review writing actually viable? | Retrieval + generation, decomposed and separately measured | Two-step keyword-extraction retrieval + prompting-based re-ranking (doubles recall vs. naive search) + plan-then-write generation | Introduces a **rolling, contamination-free eval protocol** using new arXiv papers — directly relevant if LitDiscover's APS-simulation validation faces a similar staleness critique |
| **LiRA** (AAAI) | 2025 / 5 | Retrieval/screening automation is mature; the *writing* phase (readability, factual accuracy) is under-explored | Full review article writing, not just related-work sections | Multi-agent: outliner, subsection writer, editor, reviewer | Benchmarked directly against **AutoSurvey** and MASS-Survey on SciReviewGen + a proprietary dataset; also tests robustness to reviewer-model variation |

## Tier 2 — nearest architectural neighbors (deserve a real compare/contrast paragraph)

These two overlap LitDiscover's actual design decisions, not just its problem statement.

| Paper | Year / cites | Motivation | Scope | Architecture | Evaluation |
|---|---|---|---|---|---|
| **ProfOlaf** (arXiv) | 2025 / 0 | Existing tools support only isolated SLR steps, leaving the rest manual and error-prone | Article collection + selection + topic extraction + Q&A over corpus | **Iterative snowballing with human-in-the-loop filtering** (closest match to LitDiscover's staged mode), LLM-assisted selection; CLI + web app | No quantitative benchmark reported; positioned on rigor/reproducibility, demo video only |
| **Human-Centred Research Automation** (HCAIep) | 2026 / 1 | Agentic automation must preserve trust/transparency per EU AI Act + HCAI principles | Literature **discovery, filtering, and gap identification** — nearly LitDiscover's own three-verb framing | Agentic AI pipeline, human oversight retained at later stages, structured outputs (gaps, directions, candidate solutions) | Pilot only: Llama 3.1 8b, 71.05% accuracy vs. human-led SLR baseline on abstract filtering |

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
