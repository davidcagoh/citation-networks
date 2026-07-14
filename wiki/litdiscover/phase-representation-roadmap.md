# Representation Learning for Paper Organization — phase roadmap

**Split out from `research-roadmap.md` §3 (Synthesis)** (2026-07-14) — same pattern as
`phase-discovery-roadmap.md`: a bet buried in one implementation choice (what text gets embedded
before clustering) deserves its own experimental design rather than staying an unexamined default
inside the Synthesis section.

**Origin:** during the lineage-construction work (2026-07-13), raw thematic-clustering embeddings
proved noisy enough at corpus scale to get deprecated outright (`lineages/similarity-cluster.md`)
— only 12 of 32 real citation edges survived its buckets, plus 3 fabricated edges with no textual
support. That failure is the concrete motivating case for this experiment: is the problem
embeddings *in general*, or specifically what gets embedded?

---

## 1. What's implemented today

`extract/synthesizer.py`'s Pass 1 (`_cluster_papers`):

- **Representation:** `_paper_embed_text()` — `title + themes[] + contributions[0]`, a compact
  per-paper string, not the abstract or full text. Chosen for embedding-cost reasons (~$0.001 for
  320 papers), not for representational quality — no comparison against alternatives was ever run.
- **Embedding model:** `gemini-embedding-001` (768-dim), via `_embed_papers()`.
- **Clustering:** k-means (`_kmeans_cluster`), k auto-selected via elbow method on WCSS
  (`_elbow_k`, k∈[3,10]), Gini-coefficient balance check with retry-at-k+1 if too skewed.
- **Cluster naming:** single global LLM call over the 5 nearest-centroid papers per cluster
  (`_name_all_clusters`) — a downstream labeling step, not part of the representation question
  this experiment asks.

**Known failure mode, already documented at corpus scale:** `lineages/similarity-cluster.md`
(deprecated 2026-07-13) ran a close cousin of this pipeline — thematic clustering into 6 buckets —
over the 22-paper `deep-dives.md` corpus. `lineage-comparison.md` audited it against what those
papers actually cite: only 12/32 real citation edges survived being forced into mutually-exclusive
buckets, 20 were silently dropped for crossing a bucket boundary, and 3 edges (including the
load-bearing SciReviewGen→AutoSurvey edge) had no textual support at all — the clustering
fabricated a relationship. This is the field-scale evidence that raw-signal clustering loses and
invents structure; this experiment asks whether *what's embedded* is the fixable part of that
failure, or whether clustering itself is the wrong shape regardless of representation (a question
`lineage-comparison.md` already answered "no" for citation-lineage reconstruction specifically —
worth keeping in mind as a possible negative result here too).

---

## 2. The bet we've been making, named explicitly

One representation, never compared against alternatives: a short LLM-generated digest
(title+themes+contributions[0]) embedded directly. Three untested alternatives:

| Representation | Status | Why it might organize papers better or worse |
|---|---|---|
| **Current baseline** (title+themes+contributions[0]) | Implemented | Cheap, already in production. Themes/contributions are single free-text LLM outputs from `extractor.py`'s 11-field schema — no structural guarantee they capture the axes that actually distinguish papers (method vs. motivation vs. evaluation). |
| **Abstract embedding** | Not implemented | The obvious cheap alternative — author-written, no LLM-summarization step to introduce drift, but conflates motivation/method/results into one paragraph the embedding model has to disentangle unsupervised. |
| **Full-text embedding** | Not implemented | Richest signal, but also the noisiest — boilerplate (related work, acknowledgments, references) dilutes the topic signal, and most embedding models truncate or need chunking+pooling for full papers, adding its own methodology question. |
| **Structured-summary embedding** | Not implemented | Embed the 6-field deep-dive template (Problem / How it works / How evaluated / How performed / Relation to prior work / Limitations) — same template already validated in `deep-dives.md` for all 22 corpus papers, and rich enough to support the citation-audit and implicit-pairwise work `research-roadmap.md` §2 credits it for. Hypothesis: forcing the LLM to separate motivation from method from evaluation *before* embedding gives the embedding model axes that actually align with how papers are conceptually organized, rather than asking embedding-space geometry to discover that separation from unstructured text alone. |

This is the same shape of question `phase-discovery-roadmap.md` asks about discovery operators —
not "does clustering work" but "which input representation does the actual organizing work, and by
how much."

**The deeper hypothesis, stated precisely (added 2026-07-14, external review):** this isn't really
"do summaries help embeddings" — it's that *representations which explicitly encode a paper's
discourse structure (problem/method/evaluation/limitations, i.e. its scientific role) organize a
field better than representations learned from raw text alone, which conflate all of that into one
undifferentiated signal.* Framing it this way connects the experiment to representation learning,
IR, and ontology induction generally, not just to LitDiscover's synthesis step — worth stating
explicitly in any paper, since "which embedding wins" reads as a heuristic result and "discourse
structure vs. raw text" reads as a principled one.

---

## 2.5 This is a representation-learning evaluation problem — four paradigms, not one

Standard ML/IR practice for evaluating a representation has four increasingly demanding paradigms,
each answering a different question about what the representation should preserve:

| Paradigm | Question | Method | Where this project sits |
|---|---|---|---|
| **1. Retrieval** | Does the representation retrieve related work? | Recall@k / Precision@k / MAP / nDCG against a gold neighbor set (e.g. citation-adjacency, survey co-membership) | Not this experiment's design, but the cheapest sanity check — worth running first as a smoke test before committing to §3's fuller design, since it needs no section-level ground truth, just the existing flat gold-reference lists. |
| **2. Clustering** | Does the representation group papers into meaningful flat sets? | k-means + ARI/NMI/purity/V-measure against known labels | §3 below, as originally scoped — flat k-means against section labels. |
| **3. Taxonomy/structure recovery** | Does the representation recover a *hierarchical* organization (an existing survey's, a handbook's, a classification tree's)? | Hierarchical clustering/dendrogram induction, scored by tree edit distance, dendrogram purity, ancestor precision, hierarchical F-score, against a real authorial hierarchy | **Arguably the better fit for this project's actual ground truth** — a survey's structure is section→subsection, not a flat partition, and forcing it into flat k-means for §3 discards that hierarchy the same way `similarity-cluster.md`'s mutually-exclusive buckets discarded cross-lineage edges (§1). Flagged as an open decision in §5 rather than silently committing to flat clustering by default. |
| **4. Downstream utility** | Does a better representation make the actual downstream task (writing a literature review) easier? | Expert/LLM-judged review quality (organization, redundancy, missing themes, narrative flow, correctness) comparing full synthesis runs on each representation | The evaluation reviewers will care about most, and the one with the most existing infrastructure to reuse — `check_citation_grounding()` (`research-roadmap.md` §3) already measures one axis of generated-review quality. Natural Phase 2 of this experiment once §3's cheaper clustering-level result narrows the representation field to 1-2 real contenders — not worth running full synthesis end-to-end on all four conditions before that narrowing happens. |

**Sequencing implication:** run paradigm 1 (retrieval, cheap, no new annotation needed) as an
early smoke test, decide between paradigm 2 vs. 3 for the main experiment (§5 open decision),
and treat paradigm 4 as the eventual payoff metric once the representation field is narrowed —
not a fifth thing to build from scratch alongside the rest.

---

## 3. Experiment 2 — Representation Comparison for Paper Organization

**Research question:** do structured, field-separated summaries produce embeddings that recover a
field's real conceptual organization better than embeddings of raw or lightly-processed text?

**Paradigm used below: clustering (§2.5's paradigm 2), as originally scoped.** Read §2.5's
taxonomy-recovery row before committing to this — it's a live open question (§5) whether flat
k-means is the right fit for section-structured ground truth, or whether this section should be
rewritten around hierarchical recovery instead.

### 3.1 Conditions

Four representations, same embedding model (`gemini-embedding-001`, holding the model fixed so
only the input text varies) and same clustering procedure (existing `_kmeans_cluster`/`_elbow_k`,
reused unchanged so this measures representation quality, not a new clustering algorithm):

1. **Baseline** — current production text (`title + themes[] + contributions[0]`).
2. **Abstract** — title + abstract, no LLM processing.
3. **Full-text** — title + full paper text (chunked+pooled; pooling strategy is an open decision,
   §5).
4. **Structured summary (single embedding)** — title + the 6-field deep-dive template, concatenated
   and embedded as one vector, LLM-generated per paper.

**Extensions worth naming now even if not run in the first pass** (external review, 2026-07-14) —
each is a further point on the same ladder from "minimal" to "upper bound," useful for framing the
result even if only conditions 1-4 above ship first:

- **Abstract + keywords** — a stronger cheap baseline between conditions 2 and 4, no LLM
  summarization needed if keywords are already metadata.
- **Structured summary, field-wise embeddings** — instead of concatenating the 6 fields into one
  string (condition 4), embed each field separately and compare papers on a per-field basis (e.g.
  cluster on the Method field alone vs. the Limitations field alone). More ambitious, and the
  natural next step if condition 4 wins clearly — it asks *which field* is doing the organizing
  work, not just whether structure helps in aggregate.
- **Pairwise LLM reasoning** — the upper-bound baseline: skip embeddings entirely, ask an LLM
  directly "does paper A belong in the same group as paper B" for pairwise or listwise judgments.
  Expensive (this is exactly `implicit-pairwise-analysis.md`'s O(n²)-ish approach, `lineages/`),
  but useful as a ceiling to measure how much of the gap between conditions 1 and 4 is recoverable
  at all before assuming embeddings are the right tool for this job in the first place.

### 3.2 Gold standard — reuse the 6 surveys, new ground truth needed

**Decision (per discussion, 2026-07-14): ground truth is the 6 existing surveys** (S1-MIT, S2-UCG,
S3-TOPO, K17-RGC, Ge21-HSS, Le25-GLLM — the same corpus `phase-discovery-roadmap.md` §4.2 uses),
not the 22-paper deep-dives corpus. Reasoning: these are real published surveys with their own
authorial section structure, a stronger and more generalizable "conceptual organization" signal
than the 22-paper corpus's own lineage tags (which were themselves LLM-assisted output, not
independent ground truth).

**What doesn't exist yet and has to be built:** the existing gold-set JSONs
(`live-survey-eval/data/gold-sets/*.json`) are flat reference lists (title/DOI/S2 ID only) — no
section/theme label per reference. This experiment needs, for each survey, a mapping from each
gold reference to the section/theme it's discussed under in the survey's own text. That's a new
manual-annotation pass (read each survey, tag its bibliography by section), not a rerun of
anything that already exists.

**Decision (2026-07-14, corrected from an earlier draft of this doc): pilot on the 3 live surveys
first, not the APS trio.** Checked what's actually available before assuming: the 3 closed-corpus
APS surveys (S1-MIT, S2-UCG, S3-TOPO — *Reviews of Modern Physics* articles) have **no local PDF**
and 387-582 gold references each; the 3 live surveys (K17-RGC, Ge21-HSS, Le25-GLLM) have local
PDFs already (`live-survey-eval/data/validation-surveys/*.pdf`, 9-41 pages) and a more tractable
56-202 gold references each. An earlier version of this section assumed the opposite ("APS
surveys, shorter/more uniform") without checking — corrected here. Annotate the 3 live surveys
first; decide whether to source the APS PDFs and extend to all 6 only after that pilot shows the
metric is worth the larger annotation cost.

**✅ Annotation pass done — done 2026-07-14.** All 3 live surveys section-tagged, saved to
`live-survey-eval/data/section-ground-truth/{K17-RGC,Ge21-HSS,Le25-GLLM}_sections.json`.
First-citation-occurrence rule (a reference gets the section it's first cited in, even if reused
later — same convention across all three). K17-RGC and Le25-GLLM have clean explicit numbered
headers so section assignment was direct; Ge21-HSS is a Nature Perspective in continuous prose
with no subsection headers, so its ref-number ranges were used as a proxy for section boundaries
instead (see the file's own `annotation_method` field for the exact convention, including how
Box 1's tail-numbered refs were folded back into the section they're physically embedded in).

| Survey | Gold refs (at annotation time) | Resolved | Unresolved | Sections found |
|---|---|---|---|---|
| Ge21-HSS | 202 | 197 | 5 | 5 (S0 intro, S1 describing/predicting, S2 empirically-grounded models, S3 outlook, S4 summary) |
| Le25-GLLM | 57 | 57 | 0 | 8 (1 intro, 2.1-2.3 planning/memory/tool, 3.1-3.3 orchestration/efficiency/trustworthy, 4 future) |
| K17-RGC | 56 | 52 | 4 | 10 (1 intro through 10 open problems) |

**Recurring finding, not anticipated going in: 2 of 3 gold-set JSONs contained entries that don't
correspond to any reference the survey actually cites** — confirmed, fixed 2026-07-14, see
`open-questions.md` for the full audit trail. **Gold-set files have since been corrected by hand:
Ge21-HSS 202→200 (removed 2 unrelated-topic mislinks), K17-RGC 56→52 (removed 1 pure
book-series-name record + 3 entries confirmed absent from the survey's own 51-item bibliography,
transcribed in full during this annotation pass).** Two automated content filters were tried and
both reverted after live testing showed they rejected far more real references than actual
noise (short/all-caps titles are routine in real bibliographies — Goodman's "Snowball sampling",
Munkres' "ELEMENTS OF ALGEBRAIC TOPOLOGY" — indistinguishable by shape from the genuine garbage).
**Lesson for this project generally: this class of noise has no reliable automated signature —
it needs the kind of manual, read-the-actual-source-and-check pass this annotation work already
does, not a content heuristic.** The section-ground-truth JSONs in this repo already excluded all
unresolved entries from their `resolved` lists, so they don't need re-annotating; only the
upstream `gold-sets/*.json` files and any recall number computed from them
(`phase-discovery-roadmap.md` §4) needed correcting, and now have been / still need a recall
recompute respectively.

### 3.3 Metrics

Cluster-recovery metrics comparing each representation's k-means output against the survey's own
section assignment (the ground truth from §3.2):

- **Adjusted Rand Index (ARI)** and **Normalized Mutual Info (NMI)** — standard external
  cluster-validity metrics against a known labeling, invariant to cluster-label permutation.
- **Purity** — simplest to explain in a paper, but biased toward large k; report alongside
  ARI/NMI, not instead of.
- **V-measure** — homogeneity/completeness harmonic mean, useful if a representation tends to
  over- or under-split relative to the survey's actual section count.

Internal-only metrics (silhouette score, Davies-Bouldin) are **not** sufficient alone — they
measure geometric tightness, not whether the geometry matches a real field's organization, which
is exactly the gap that let `similarity-cluster.md`'s fabricated edges look fine internally while
being wrong externally. Report them only as a secondary diagnostic, never as the headline number.

### 3.4 Procedure

For each survey in the gold standard:
1. Pull the survey's gold reference list + section labels (§3.2).
2. Generate all four representations per paper (extraction calls needed for baseline/structured
   conditions; abstract/full-text need no LLM call, just retrieval).
3. Embed each representation set independently.
4. Cluster each (k = survey's own actual section count, held fixed across all four conditions per
   survey — isolates representation quality from elbow-method k-selection noise, which is a
   separate question).
5. Score all four against the section ground truth (§3.3).
6. Repeat per survey; report per-survey and aggregate (mean ± spread) across the gold set.

### 3.5 Statistical power — same open question as discovery, not yet decided

`phase-discovery-roadmap.md` §4.2/§4.9 already flagged that 6 surveys is thin for paired
significance testing (Wilcoxon signed-rank wants ~15-20 paired observations for real power) and
left expanding the gold-standard corpus as an open, undecided step. **Same applies here** — if
this experiment's results look like they're worth a significance claim rather than a descriptive
comparison, expanding beyond 6 surveys is the prerequisite, shared infrastructure with discovery's
own §4.9 rather than a separate expansion. Not deciding this now; noting it so it isn't
independently relitigated later.

---

## 4. Scope: this experiment directly evaluates a fix to `synthesizer.py`

Unlike a purely descriptive study, this is explicitly scoped to change production code if a
representation wins clearly. **If structured-summary embeddings outperform the baseline:**

- `_paper_embed_text()` swaps from `title+themes+contributions[0]` to the 6-field structured
  summary — a representation change, not a clustering-algorithm change (`_kmeans_cluster`,
  `_elbow_k`, `_name_all_clusters` stay as-is).
- This is gated on `research-roadmap.md` §2's open extraction-schema question (prompt-only change
  vs. an `extractions` table migration) — the 6-field template isn't currently a schema
  `extractor.py` produces at all, so winning this experiment creates, not resolves, that scoping
  decision. Read §2 before starting the migration, not after.
- If **abstract or full-text** wins instead, no schema migration is needed — just a
  `_paper_embed_text()` rewrite, since those representations don't depend on the deep-dive
  template existing in the extraction pipeline at all.

**If nothing beats the baseline clearly:** that's still a real result — evidence the
`similarity-cluster.md` failure mode is about clustering’s bucket-forcing shape (already suspected,
per §1) rather than representation quality, which would redirect Synthesis's actual fix toward
`research-roadmap.md` §3's item #2 (plan-before-write) instead of a representation swap.

---

## 5. Open decisions before building any of this

1. ✅ **Section-level ground truth for the 3 live surveys — done 2026-07-14** (§3.2). Still open:
   whether to source the 3 APS PDFs and extend to all 6, deferred until the pilot's clustering
   results are in.
1b. **Flat clustering vs. taxonomy recovery (§2.5)** — §3 as written scores flat k-means against
   section labels (paradigm 2). A survey's actual structure is hierarchical (sections contain
   subsections), so paradigm 3 (hierarchical recovery, scored by tree edit distance / dendrogram
   purity / hierarchical F-score) may be the more faithful evaluation of the same ground truth.
   Decide this before or during the annotation pass — the annotation format differs (flat
   section-per-reference tag vs. full section/subsection path per reference), so getting this
   wrong means re-annotating, not just re-analyzing.
2. **Full-text pooling strategy** — chunk+mean-pool, chunk+max-pool, or truncate-to-model-limit;
   affects the full-text condition's fairness relative to the other three, which don't need
   chunking at all. Needs a decision before condition 3 can run, not deferrable to analysis time.
3. **k held fixed at the survey's actual section count (§3.4)** — deliberate choice to isolate
   representation quality from elbow-method noise. Worth flagging as a limitation: production
   `synthesizer.py` uses elbow-selected k, so this experiment's clustering setup is not identical
   to the production path it's meant to fix. A follow-up with elbow-selected k per representation
   would test the two effects (representation choice, k-selection quality) jointly instead of in
   isolation — deferred, not in scope for the first pass.
4. **Statistical power / corpus expansion (§3.5)** — shared open question with
   `phase-discovery-roadmap.md` §4.2/§4.9, not decided in either place yet.
