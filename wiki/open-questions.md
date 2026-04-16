# Open Questions

Ordered by project and priority. Check this at the start of each session.

---

## citation-dynamics (ACTIVE)

### NEXT: Community physics labelling
**Why:** Paper §4 table shows community IDs, not physics areas. Reviewers need interpretable labels.
**How:** Script to extract top-5 cited papers per community → identify by journal/title as condensed matter / particle / quantum optics etc.
**Status:** Not started. Can be done now (no GPU needed).

### NEXT: SG-t-SNE baseline for §5 comparison
**Why:** §5 claims NST gives better temporal ordering than SG-t-SNE. Need the baseline to support this.
**How:** Run existing MATLAB pipeline on same data subset; report Spearman ρ(embedding coord, year).
**Status:** Not started. Requires MATLAB.

### Backward influence mapping scope (§7 decision)
**Why:** Thesis contribution 2 (backward influence mapping) needs a concrete pipeline, not just `query_XY_subgraph` availability.
**Options:** (a) Full section with 2 case studies; (b) Fold into §6 as a Time Curves case study; (c) Cut to 1 paragraph in discussion.
**Status:** Decision pending — hold until §§5–6 results are in.

### Aging model π(C)
**Why:** Thesis contribution 3 (quantitative phase characterization) originally included an aging term. Not in the paper scope but needed for the thesis chapter.
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

**Q-SOTA (session 12):** Zeitgeist hypothesis confirmed as a gap. Nearest prior art: Costa & Frigori 2024, Aparício et al. 2024, Castillo-Castillo et al. 2025, Ke et al. 2023 PNAS. NST (Choudhary ICLR 2025) is a tool, not a competitor.

**Q-SYNTH (sessions 17–20):** K17-RGC subgraph built (90 nodes, 7 communities). Caveat: 49/51 gold DOIs are non-APS — document as corpus coverage limitation.
