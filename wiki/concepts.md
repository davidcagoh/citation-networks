# Concepts

Methodological and theoretical ideas relevant to the project — not tied to a specific task, but worth keeping in mind during analysis and writing.

---

## Distribution Fitting: Complementary Metric Families

*From a conversation with Xiaobai Sun, 2026-04-17.*

**The problem with single-metric fitting:** Most distribution fitting work picks one distance metric (KL divergence, Hellinger, etc.) and declares a good fit if it's small. But different metrics are sensitive to different regions of the distribution — using only one metric gives an incomplete picture and can mask poor fit in other regions.

**Xiaobai's framework:** Characterize distance metrics by where they are most sensitive:
- **Head-sensitive** — detects differences where most probability mass is (e.g., KL divergence)
- **Middle** — balanced sensitivity (e.g., Hellinger, Le Cam)
- **Tail-sensitive** — detects differences in the rare/extreme events (e.g., Xiaobai's own formulation, which generalizes the above and tunes sensitivity toward the tails)

**The recommendation:** When claiming a distribution fits data, use *three complementary metrics* — one from each family. Picking three metrics from the same family is redundant; they will agree by construction. Complementarity is what makes the validation informative.

**Relevance to this project:**
- **Zeitgeist fitting (§3):** We currently use KS test to validate power-law fits per community. This is a single metric. Xiaobai's framework suggests adding a tail-sensitive metric alongside KS — power-law fits are most contested in the tail, so head/middle metrics may pass trivially even when the tail is wrong.
- **Synthesis / sub-community fitting:** Same applies if we fit distributions within smaller Leiden clusters (small-N regime makes tail behavior even noisier).
- **Global APS distribution (§2):** γ_global = 2.74. The KS pass (100% of communities) is head/middle evidence; a tail metric would test whether the Zeitgeist story holds in the high-citation extremes.

**Status of Xiaobai's paper:** Not yet in preprint (as of 2026-04-17). Revisit when available.

---

## Citation Motifs as Innovation-Type Proxies

*From a conversation, 2026-04-18. Untested — not in current thesis scope.*

**The idea:** Three structural patterns in a citation graph may correspond to three qualitatively different modes of how an idea enters a field:

1. **Convergent fan-out (seminal hub):** A single originating paper becomes widely cited; a survey amplifies it. Graph shape: one root with high in-degree, diamond/star structure.

2. **Parallel independent discovery:** Multiple co-temporal papers arrive at the same idea without citing each other. Graph shape: several disconnected root nodes that later converge onto shared citing work. Corresponds to Merton-style multiples.

3. **Context transplantation:** The idea predates the local community — it existed elsewhere and was imported. Graph shape: cluster whose root nodes cite papers *outside* the local domain bibliography. Looks like novelty from inside but isn't.

**Operationalization with APS:** Define "domain" as the reference list of a major comprehensive survey. Roots inside the bibliography → patterns 1 or 2. Roots citing outside → pattern 3. Limitation: cross-corpus ancestors (CS, chemistry) are invisible in APS — pattern 3 may be conflated with 2.

**4. Coupled fields (added 2026-07-08):** Two clusters that co-construct each other rather than one containing or feeding the other — e.g. a technique cluster (AI agent memory systems) and its evaluation cluster (benchmarks like LoCoMo). Method papers cite the benchmark to justify evaluation; benchmark papers cite methods to justify what they test against. Graph shape: dense bidirectional cross-citation between two clusters, distinct from an ordinary domain boundary (which is mostly one-directional or sparse). Under a hard partition (Leiden/BlueRed) this either gets merged into one cluster or split with nothing marking the split as qualitatively different from a normal community boundary — the coupling itself is the signal, and hard partitioning throws it away. See the HDP entry below for a representation that might actually surface this instead of erasing it.

**Status:** Speculative. Separate future project — revisit after current thesis papers are in submission.

---

## Hierarchical Dirichlet Process for Field Resolution

*From a conversation, 2026-07-08. Untested — not in current thesis scope.*

**The problem it targets:** "What counts as a field" has no principled answer under the clustering methods currently in use (Leiden, BlueRed). Both force a *hard partition* — every paper gets exactly one community — and both require pre-committing to a resolution/granularity parameter that implicitly decides how fine-grained "a field" is before you've looked at the data. A paper that genuinely bridges two threads gets forced into one bucket, and there's no way to ask "is this boundary real or an artifact of my resolution choice." This is the concrete failure mode behind papers like arxiv.org/html/2605.02128v1, where no clean way exists to say what "a field" is.

**The idea:** Model the corpus with a Hierarchical Dirichlet Process (Teh, Jordan, Beal & Blei, "Hierarchical Dirichlet Processes," 2006 — people.eecs.berkeley.edu/~jordan/papers/hierarchical-dp.pdf) instead of a hard graph partition. HDP is a nonparametric Bayesian mixture model: the number of latent topics/threads is not fixed in advance but inferred from data, each paper gets a *mixture* over topics rather than a single label, and — the load-bearing feature for this use case — topics are shared across groups via a shared base distribution, so different traversals (e.g. two different LitDiscover survey seeds) don't need a prior decision about whether they're "the same field." The model can discover shared latent threads probabilistically instead.

**Relevance to the Coupled fields motif above:** A field pair like memory-systems/LoCoMo would show up under HDP as two topics with unusually high shared mass across papers, rather than as two adjacent hard clusters with a dense cut between them — closer to a topic-correlation structure than a partition. That might be the right level of abstraction for detecting motif #4 specifically, since hard partitioning by construction erases the thing that makes coupled fields interesting.

**Where it could plug in:** Downstream of the LitDiscover graph export (`<slug>_graph.h5` / `<slug>_papers.json`) or the Synthesis subgraph — as an alternative to Leiden in `synthesis/methods-comparison.md`'s clustering comparison, not a replacement for Zeitgeist's Leiden-based power-law analysis (which needs a graph partition, not a soft mixture).

**Status:** Speculative. Separate future project — revisit after current thesis papers are in submission.

---

## Traversal-Native Visualization (LitDiscover graph/round exports)

*From a conversation, 2026-07-08. Untested — not in current thesis scope.*

**What changed:** LitDiscover's `run` command now exports `<slug>_graph.h5` (COO edge list + per-node arrays, same convention as `citation-dynamics/src/phase1_build_graph.py`) and `<slug>_papers.json`, with every visited paper included regardless of status plus an `included` 0/1 vector — not just a pre-filtered "final" subgraph. That means the induced included-only subgraph (`diag(v) @ A @ diag(v)`) and the full visited-but-rejected superset are both derivable from one export, which wasn't possible when the only per-stage artifact was a markdown vetting table.

**What this unlocks:**
- **Round-by-round animation:** with a per-round inclusion vector, animate which nodes entered the graph at each traversal round — makes visible what the algorithm considered and rejected, not just the final gold-adjacent set. This is a diagnostic LitDiscover never had.
- **Reusing the Time Curves pipeline (already specced in `citation-dynamics/nst-timecurves-comparison.md` for the full 709K-node Zeitgeist corpus, archived as out-of-scope there) on a single LitDiscover project's subgraph.** NST → SG-t-SNE → Time Curves was built and proxy-verified (`phase4_timecurves.py`) for full-corpus phase detection; the new h5 export makes it trivial to point the same pipeline at one traversal's output instead, without the special-cased DOI extraction `synthesis/experiment-spec.md` currently requires for K17-RGC.
- **Directly composes with the Synthesis pipeline:** the h5 export is already in the format `synthesis/methods-comparison.md`'s Leiden/BlueRed and NST/SG-t-SNE/UMAP comparisons expect, so any LitDiscover project's output becomes a synthesis test case for free, not just the manually-extracted K17-RGC case.

**Status:** Speculative. Separate future project — revisit after current thesis papers are in submission.

---
