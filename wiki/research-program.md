# Research Program Overview

*Written 2026-07-08 for presenting to a potential collaborator. Narrative summary — for implementation detail, follow the links out to each project's own files.*

---

## The shape of it

Three pillars under one thesis ("Recognizing Signature Patterns and Phases of Time-Varying Networks"), plus two speculative extensions that grew out of working on the pillars. The pillars form a pipeline — each one's output is the next one's input — and the two extensions are upgrades to specific weak points in that pipeline, not separate side quests.

```
LitDiscover (recover a field's papers)
        │
        ▼
Zeitgeist (resolve structure within a citation graph)
        │
        ▼
Synthesis (apply that structure to a LitDiscover-recovered set)
```

---

## Pillar 1 — LitDiscover

**What it is:** An algorithm + shipped tool for recovering the full paper set behind a research topic by traversing citation graphs outward from one or a few seed papers, instead of relying on keyword search. Validated against real survey bibliographies (85–98%+ overlap depending on seed count).

**Status:** Live on PyPI (`pip install litdiscover`), engine works, one real bug fixed but not yet republished. Paper submitted four times (JCDL missed deadline → JASIST → TOIS abandoned on page minimum → IP&M), most recently **desk-rejected** — reviewer wants SOTA/LLM-era baselines and current-year references, i.e. the underlying lit-review run needs a redo, not the core idea.

**Strengthener in hand:** the traversal export now writes a full graph (`<slug>_graph.h5` + `<slug>_papers.json`) with every visited node, not just the included ones, plus a per-node inclusion flag. That makes a **visualized traversal** possible for the first time — animate round-by-round what the algorithm considered and rejected, not just the final recovered set. This is a concrete, demoable strengthener for the paper redo: it turns "trust the recall number" into "watch the algorithm work."

*Detail: `litdiscover/` files, esp. `decisions.md` and `open-questions.md`.*

---

## Pillar 2 — Zeitgeist (citation-dynamics)

**What it is:** The original project with Xiaobai Sun. Hypothesis: a citation network's global power-law degree distribution is actually a **mixture** of distinct power laws, one per research community — each community has its own exponent γ_c and its own temporal window, rather than being one homogeneous scale-free process.

**Status:** First full paper draft compiled (LNCS, 10pp), targeting COMPLEX NETWORKS 2026 (~August). Result on APS (709,803 papers): global γ=2.74, 446 Leiden communities, 25 sampled communities all pass per-community KS fit with γ_c ∈ [2.10, 3.27] (mean 2.50), 68% temporally compact (<20yr IQR). Real, working result — under review by the collaborator (you), not yet a known weakness.

**Strengthener in hand:** the result currently depends on Leiden's **hard partition** — every paper gets exactly one community label. But citation networks don't actually respect that: a paper can genuinely belong to two threads at once, and the resolution parameter that decides "how fine a community is" is chosen by the researcher, not discovered. This matters beyond aesthetics — it's the same failure mode behind proposals that can't cleanly say what "a field" is (see arxiv.org/html/2605.02128v1 as a live example of the problem). A **Hierarchical Dirichlet Process** (Teh, Jordan, Beal & Blei 2006) would replace the hard partition with soft, shared topic mixtures — no pre-committed community count, no forced single label per paper.

*Detail: `citation-dynamics/decisions.md`, `citation-dynamics/codebase-map.md`.*

---

## Pillar 3 — Synthesis

**What it is:** The pipeline that closes the loop — take a paper set LitDiscover recovered, run Zeitgeist-style structural analysis (Leiden clustering, per-community power-law fitting, temporal localization) on it, and check whether the resulting clusters read as real research threads to a domain expert.

**Status:** Spec written (K17-RGC test case: 56 gold papers, 100% recall, from Bobrowski & Kahle 2017), **zero implementation**. On hold until Zeitgeist is submitted — deliberately, so the Zeitgeist result isn't being validated against itself.

**Why it matters to this conversation:** this is where the two pillar-1/pillar-2 strengtheners actually meet. The traversal-visualization export (LitDiscover) is already in the exact graph format Synthesis expects. HDP-based resolution (Zeitgeist) is most likely to show its value at Synthesis's scale (~500–2000 papers, one topic) rather than at Zeitgeist's full-corpus scale (709K papers, 446 communities) — a focused topic is exactly where bridge-papers and soft field boundaries would show up, not get averaged away. Right now this is the most stalled piece of the whole program despite being the connective tissue.

*Detail: `synthesis/experiment-spec.md`, `synthesis/methods-comparison.md`.*

---

## Two things up the sleeve

Not part of the current thesis scope — logged as future directions, revisit once the three pillars above are in submission/revision.

**Citation motifs as innovation-type proxies.** Three (now four) structural patterns in a citation graph as proxies for *how* an idea entered a field: seminal hub (one root, high in-degree), parallel independent discovery (disconnected co-temporal roots converging later), context transplantation (roots citing outside the local domain — imported, not native), and **coupled fields** (two clusters that co-construct each other — e.g. AI-agent memory systems and the benchmarks built to test them, like LoCoMo — dense bidirectional cross-citation that a hard partition either merges or splits without marking as different from an ordinary boundary).

**Why coupled fields ties back to HDP:** hard partitioning erases exactly the signal that makes a coupled-fields pair interesting. Under HDP, a coupled pair should show up as two topics with unusually high *shared* mass across papers — a topic-correlation structure, not a partition. So the HDP strengthener for Zeitgeist and the fourth motif aren't independent ideas; HDP might be the representation that actually makes motif 4 detectable in the first place, and motif 4 might be the concrete demo case that makes HDP's soft-boundary claim legible to a reader.

*Detail: `concepts.md` — "Citation Motifs as Innovation-Type Proxies" and "Hierarchical Dirichlet Process for Field Resolution."*

---

## One-paragraph pitch

Citation networks are usually treated as single homogeneous processes or forced into hard partitions when they're neither — they're mixtures of communities with their own dynamics (Zeitgeist), the tools that recover them undersell what they actually found because they don't show their work (LitDiscover), and the boundaries between fields are often genuinely soft rather than resolvable at all (motifs, HDP). This program has working code and a real result on the first two claims and a concrete, near-term way to test the third.
