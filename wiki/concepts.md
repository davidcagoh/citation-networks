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

**Status:** Speculative. Separate future project — revisit after current thesis papers are in submission.

---
