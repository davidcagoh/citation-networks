# Open Questions

Ordered by project and priority. Check this at the start of each session.

---

## citation-dynamics (ACTIVE)

### DONE: Community physics labelling
**Result:** All 25 communities labelled from top-cited DOIs. Script: `src/label_communities.py`. Labels: `data/analysis/community_labels.csv`.
**Verify:** Communities 13 (Nonlinear Dynamics), 14 (Magnetism), 16 (QHE), 19 (Semiconductor) are less certain — cross-check against APS journal names if needed for the table.

### DONE: Generate §§1–4 figures
**Result:** All four figures generated at `data/figures/fig{1..4}_*.pdf`. Global γ=2.74 (K_min=96), consistent with Barabasi 2.79.

### NEXT: Rewrite §§1 and 8
**Why:** Intro still pitches NST + Time Curves pipeline; §8 discussion references them. Both dropped.
**Status:** Figures confirmed ✅ — ready to rewrite now.
**§1 new pitch:** Zeitgeist hypothesis → community detection (Leiden) → per-community power-law validation → temporal localization. No NST or Time Curves.
**§8 new framing:** What we showed (mixture validated), universal γ interpretation, limitations (APS only, no text features), future (aging model π(C), cross-corpus).

### Aging model π(C)
**Why:** Thesis contribution 3 originally included an aging term. Not in paper scope but needed for thesis chapter.
**Status:** Not started. Post-paper.

---

## LitDiscover (believed resolved — verify before submission)

Session 15 marked LitDiscover complete with all three live experiments done (K17-RGC 100%, Ge21-HSS 100%, Le25-GLLM 73.7%). The items below are believed resolved but the wiki had not been updated at that point. Verify against the actual paper draft before submission.

| Item | Issue | Believed status |
|---|---|---|
| Q1: Live experiments | K17-RGC ✅, Ge21-HSS ✅, Le25-GLLM ✅ (73.7%) | ✅ Resolved session 15 |
| Q2: Fig 7 k=5 vs k=20 | Check `cold_start_results_lowseed.json` | Believed resolved |
| Q3: Fig 6 non-monotone recall | Add paragraph explaining yield-stopping mechanism | Believed resolved |
| Q4: Pareto-80 vs Pareto-50 | Demonstrate Pareto-50 fails under yield-based stopping | Believed resolved |
| Q5: Random seeds > top-5 at round 1 | Run ≥5 trials; report mean ± std | Believed resolved |
| Q9: γ < 2 in Fig 1 | Add KS goodness-of-fit sentence | Low priority |
| Q10: Error bars Figs 5–6 | Run multiple trials for random/contaminated conditions | Low priority |
| Q11: [CITATION NEEDED] locations | Fill yellow-highlighted citations | Believed resolved session 15 |
| Q15: §5 yield lines overlap | Add sentence: threshold doesn't affect final recall, only screening cost | Believed resolved |

---

## RESOLVED (for reference)

**NST §5 (2026-04-17):** Dropped. Spatial PCA not community-separating; temporal Spearman ρ=−0.668 ambiguous. Not worth a paper section.

**Time Curves §6 (2026-04-17):** Dropped. Corpus-level centroid trajectory averages over 446 communities and produces uninformative result. Wrong level of analysis for a multi-community network.

**SG-t-SNE baseline for §5 (2026-04-17):** Moot — §5 dropped.

**Q-SOTA (session 12):** Zeitgeist hypothesis confirmed as a gap. Nearest prior art: Costa & Frigori 2024, Aparício et al. 2024, Castillo-Castillo et al. 2025, Ke et al. 2023 PNAS. NST (Choudhary ICLR 2025) is a tool, not a competitor.

**Q-SYNTH (sessions 17–20):** K17-RGC subgraph built (90 nodes, 7 communities). Caveat: 49/51 gold DOIs are non-APS — document as corpus coverage limitation.
