# citation-dynamics — Open Questions

Check this at the start of each session.

---

## NEXT: Rewrite §§1 and 8
**Why:** Intro still pitches NST + Time Curves pipeline; §8 discussion references them. Both dropped.
**Status:** Figures confirmed ✅ — ready to rewrite now.
**§1 new pitch:** Zeitgeist hypothesis → community detection (Leiden) → per-community power-law validation → temporal localization. No NST or Time Curves.
**§8 new framing:** What we showed (mixture validated), universal γ interpretation, limitations (APS only, no text features), future (aging model π(C), cross-corpus).

## LaTeX §4 table
**Why:** Paper needs a community table: top-10 communities, columns: n, γ_c, KS p, yr median, IQR, physics label.
**Source:** `data/analysis/community_labels.csv`
**Status:** Not yet written.

## Uncertain community labels (cids 13, 14, 16, 19)
**Why:** Four of the 25 large communities were less confidently identified from top-cited DOIs.
**Action:** Cross-check against APS journal names if needed for the table.

---

## RESOLVED (for reference)

**NST §5 (2026-04-17):** Dropped. Spatial PCA not community-separating; temporal Spearman ρ=−0.668 ambiguous.

**Time Curves §6 (2026-04-17):** Dropped. Corpus-level centroid trajectory averages over 446 communities → uninformative.

**Q-SOTA (session 12):** Zeitgeist hypothesis confirmed as a gap. Nearest prior art: Costa & Frigori 2024, Aparício et al. 2024, Castillo-Castillo et al. 2025, Ke et al. 2023 PNAS.

**Q-SYNTH (sessions 17–20):** K17-RGC subgraph built (90 nodes, 7 communities). Caveat: 49/51 gold DOIs are non-APS — document as corpus coverage limitation.

**Aging model π(C):** Not in paper scope. Post-paper thesis chapter.
