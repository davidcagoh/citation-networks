# Research Roadmap — validating each pipeline stage on its own terms

**Supersedes `background.md`** (2026-07-14). That file was a read-once explainer of the
discovery/traversal algorithm alone, written for the original paper's argument map. This doc
reframes the whole project as three separately-bettable pipeline stages — **Discovery, Extraction,
Synthesis** — each with: what's implemented today, what bet we've implicitly made by only building
that, what's untried, and how to benchmark it. `decisions.md`/`open-questions.md` remain the live
day-to-day files; this is the standing plan they draw from.

**Why this restructure, now:** we've been treating "the algorithm" as citation traversal, full
stop — but traversal is one discovery *method* among several, and extraction/synthesis were both
built before any of the related-work research existed, i.e. naively scoped and never
benchmarked against ground truth the way discovery has been. All three stages deserve the same
treatment discovery already got: name the bet, name the untested alternatives, define precision
and recall properly, and measure.

---

## 0. Pipeline overview

```
SEED papers (2-5) → DISCOVER → SCREEN (LLM) → EXTRACT → SYNTHESIZE
```

Only **Discovery** has been rigorously benchmarked (6 surveys, closed-corpus + live). Extraction
and Synthesis have never been evaluated against ground truth — see §2 and §3.

---

## 1. Discovery

**Moved to its own file: [`../discovery/roadmap.md`](../discovery/roadmap.md)** (2026-07-14)
— discovery had grown to 5 subsections (current implementation, a 27-method prior-art survey, the
untested-method table, the proposed ablation benchmark, and the simulation-vs-production gap) and
was crowding out Extraction/Synthesis here. Read that file for all discovery planning; this doc
keeps only the cross-stage summary below.

**Summary:** two discovery mechanisms exist today — bidirectional citation traversal and an
LLM-keyword→S2-search escape hatch — validated to 89–98%/73–100% recall across 6 surveys, but
never benchmarked on precision or against untested alternatives (embedding/author/venue/recency
search). A 27-method survey of the field (`deep-dives.md`) found no prior tool does author,
venue, or recency-only search either — a genuine field-wide gap, not just LitDiscover's.

---

## 2. Extraction

**Current state:** single-shot Gemini call per paper (`extract/extractor.py`), fixed 11-field
schema (research_questions, contributions, methodology, system_or_tool, datasets, metrics,
key_results, limitations, future_work, themes, related_to). No validation against ground truth
anywhere — extraction quality is simply trusted.

**Known gap (named 2026-07-13, during the lineage-construction work):** the ad hoc 6-field
template used for `deep-dives.md` (Problem / How it works / How evaluated / How performed /
Relation to prior work / Limitations) proved rich enough to support real downstream analysis
(the citation-audit, the implicit-pairwise pass, the connected-component finding) that the
current 11-field schema was never asked to support. Not yet ported into `extractor.py` — open
scoping question is how much of the gap is a prompt change vs. an `extractions` table migration.

**The deeper gap:** there is no equivalent of discovery's "recall against a known gold
bibliography" for extraction. Nothing checks "did the LLM correctly extract this paper's actual
contributions" — this is the same problem citation-grounding solves for synthesis, one stage
upstream, and currently has no diagnostic at all.

**Proposed benchmark:** the 22-paper `deep-dives.md` corpus already has full-text-verified,
6-field extractions (several caught real errors vs. abstract-only extraction during full-text
verification — see `decisions.md`). Run the current 11-field extractor over the same 22 papers
and diff: what does the richer template capture that the production schema drops? This reuses
already-existing ground truth rather than requiring a fresh manual pass.

---

## 3. Synthesis

**Current state:** 3-pass pipeline — k-means clustering on Gemini paper embeddings (elbow-method
k selection) → per-theme narrative generation (map-reduce for clusters >80 papers) → intro/
conclusion. Citation-grounding diagnostic shipped (`check_citation_grounding()`, 2026-07-11) but
**never run against a real project** — the actual grounding precision number is still unmeasured.

**Representation question moved to its own file, now in Synthesis: [`../synthesis/representation-learning-plan.md`](../synthesis/representation-learning-plan.md)**
(2026-07-14) — what text gets embedded before k-means (`_paper_embed_text()` in
`synthesizer.py`) was never compared against alternatives (abstract, full-text, structured-summary
embeddings). Motivated by `../synthesis/background/lineages/similarity-cluster.md`'s corpus-scale failure (12/32 real
edges survived, 3 fabricated) — Experiment 2 there tests whether that failure is fixable by
changing the representation or is inherent to clustering's bucket-forcing shape.

**Full audit already done, ranked** (`open-questions.md`, 2026-07-10/11 — not repeated here in
full):
1. Citation grounding — confirmed gap, cheap fix, **shipped, unmeasured**.
2. Plan-before-write (single-shot generation, no intermediate claims list/outline) — confirmed
   gap, larger fix, gated on #1's results before it's worth building.
3. Ground-truth cluster-assignment validation — confirmed gap, no cheap ground truth exists
   currently (Zeitgeist's community labels are a different corpus/domain, not reusable).
4. Map-reduce reduce-step loses access to source fields — same root cause as #1, no separate fix
   needed.

**Immediate next step, unchanged from before:** run `litdiscover synthesize` on a real project to
get the actual grounding-precision number. This gates whether #2 and #3 are worth building at
all — no new scoping needed, just execution.

---

## 4. Shared benchmark design across all three stages

The 6 surveys (S1-MIT, S2-UCG, S3-TOPO, K17-RGC, Ge21-HSS, Le25-GLLM) currently ground-truth
**discovery only** (recall against each survey's own reference list). Proposal: reuse the same 6
as an end-to-end benchmark corpus instead of a discovery-only one:

- **Discovery:** existing recall/precision-per-method benchmark — see
  `../discovery/roadmap.md` §4.
- **Extraction:** no natural per-survey ground truth here (extraction is per-paper, not
  per-survey) — the 22-paper deep-dives corpus (§2) is the right ground truth instead. Keep these
  as two separate benchmark sets rather than forcing one corpus to do everything.
- **Synthesis:** each of the 6 source surveys *is itself* a literature review of the same
  topic — its own Related Work / Background section is a natural synthesis ground truth.
  Compare a LitDiscover-generated section against the survey's own prose on the same paper set:
  does it cover the same key papers, similar structure, comparable claims? This is a much softer
  comparison than discovery's exact-recall metric (survey prose isn't a checklist), but even a
  qualitative side-by-side would be the first synthesis evaluation against real human writing
  this project has ever done.

---

## 5. Open decisions before building any of this

- Discovery-specific open decisions (which new method to scope first, precision-per-method
  design) live in `../discovery/roadmap.md` §7.
- Extraction schema migration: confirm scope (prompt-only vs. `extractions` table migration)
  before committing to the 22-paper diff benchmark.
- Confirmed, not open: `check_citation_grounding()` must run against a real project before any
  synthesis redesign work (#2/#3) starts — this was already decided 2026-07-13, restated here so
  it isn't relitigated.
