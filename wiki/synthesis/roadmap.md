# Synthesis — Roadmap

**Read this first.** One page: what Synthesis is, what's actually running vs. still blocked, and
the single next action for each track. Everything else in this directory is detail underneath one
of the three tracks below, or background evidence motivating them.

---

## The goal

Given a curated paper set (recovered by LitDiscover), organize it into interpretable structure —
clusters/lineages, temporal emergence, influence hubs — useful to someone writing a literature
review on that topic. **Not** narrative-text generation (that's the AutoSurvey/PROMPTHEUS/SurveyX
line of work — see `background/`, cited as prior art, not a competitor).

Three genuinely different subroutines attempt this, each with its own plan file. They're disjoint
mechanisms answering the same question — worth running independently rather than picking one
prematurely, since `background/lineages/lineage-comparison.md` already showed that no single method
in its own family recovered more than half of a corpus's real structure.

---

## The three tracks

| Track | Mechanism | Plan | Status | Next action |
|---|---|---|---|---|
| **Q-SYNTH** | Graph-native: Leiden community detection + power-law fitting + NST/UMAP/SG-t-SNE embedding, on real citation-graph data (APS `C` matrix) | [`q-synth-plan.md`](q-synth-plan.md) | **Not started, but first blocker cleared 2026-07-14.** Gold set verified (52 papers, `live-survey-eval/data/gold-sets/K17-RGC_gold.json` — not the path originally guessed). Zero code written, zero results. | Build the 1-hop subgraph from the verified gold set and run Leiden once — cheaper than waiting on planner/architect sprint-planning first |
| **Representation learning** | Embedding-native: does a structured 6-field paper summary embed better for clustering than raw/lightly-processed text? 4-condition design (baseline / abstract / full-text / structured summary) | [`representation-learning-plan.md`](representation-learning-plan.md) | **Partially prepped.** Section-level ground truth built for 3 live surveys (2026-07-14); a real gold-set data-quality bug found and fixed along the way. Pipeline itself not yet run. | Resolve 3 open design decisions before running: full-text pooling strategy, k-fixed-vs-elbow, flat-vs-hierarchical scoring (see `representation-learning-plan.md` §9) |
| **LLM-text-native (background/lineages/)** | Explicit citation-graph extraction + implicit mechanism-to-gap matching, both operating on paper *text*, not graph data | [`background/lineages/`](background/lineages/) | **Complete, as a control condition** — this track's own thematic-clustering variant (`similarity-cluster.md`) was run, audited, and deprecated; the two surviving methods (explicit + implicit) already draft LitDiscover's own related-work section. Not an open investigation — it's evidence motivating the other two. | None — this track is done and archived, not blocked |

**Why three, not one:** each targets a different failure mode. Q-SYNTH asks whether respecting
citation *direction* preserves lineage structure that direction-blind methods lose. Representation
learning asks whether *what gets embedded* (structured summary vs. raw text) is the fixable part of
a documented clustering failure. `lineages/` already answered a narrower, adjacent question — is
LLM-text-based clustering (any embedding, any prompt) structurally capable of representing a
field's real citation topology — and found no, a single-membership partition can't represent
papers that are real hubs across multiple lineages (LitLLM/AutoSurvey each cited into 7 times,
split across 3 different buckets in the deprecated version). That finding motivates *why*
representation learning and Q-SYNTH are worth running as separate tracks rather than assuming a
better prompt or a better embedding model fixes clustering on its own.

---

## What "rigor" means for each track before it counts as a real result

- **Q-SYNTH**: passing the domain-expert sanity check (`q-synth-plan.md` §"Success criteria") on
  the actual K17-RGC subgraph — not just running the pipeline, since a plausible-looking cluster
  map with no expert check is exactly the failure mode `lineages/similarity-cluster.md` already
  demonstrated for a different method.
- **Representation learning**: a result on real held-out ground truth (the 3 live-survey section
  structures), not just "structured summaries look more organized" — `q-synth-plan.md` flags the
  same trap for NST (disconfirmed at one scale, untested at the scale that matters) as a caution
  here too: a hypothesis surviving intuition isn't the same as surviving a held-out test.
- **Both together**: if Q-SYNTH and representation learning reach compatible conclusions about
  what structures a field well (e.g. both favor representations/methods that respect some notion of
  directionality or discourse structure over raw proximity), that convergence across genuinely
  disjoint mechanisms is a stronger claim than either result alone — worth checking for once both
  have real results, not assuming in advance.

---

## Background (motivation and prior-art evidence, not open investigation)

- [`background/lineages/`](background/lineages/) — the three LLM-text-native methods (explicit
  citation graph, implicit pairwise matching, deprecated thematic clustering), the worked
  ProfOlaf comparison, and `reference-implementation-survey.md`'s code-grounded audit of 14 cloned
  reference systems (embedding/clustering choices, synthesis mechanisms, paper-vs-code fidelity
  gaps, paper-reported eval/results).
- [`background/eval-standard-gap.md`](background/eval-standard-gap.md) — no mature evaluation
  standard exists for synthesis quality in the LLM-narrative-generation literature; the
  "synthesis"/"critical analysis" axis specifically has no validated instrument anywhere in that
  corpus. Direct positioning material for both Q-SYNTH and the representation-learning track.
