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
