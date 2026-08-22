# citation-dynamics — Open Questions

Check this at the start of each session.

---

## NEW (2026-07-21): time-axis-aware layout — post-paper, not COMPLEX NETWORKS 2026 scope

**Decision:** Zeitgeist isn't done once the §§1–4 paper ships. Implement a proper
t-SNE/force-directed layout with an explicit time axis — not SG-t-SNE's current symmetrized,
atemporal 2D layout, and not NST's spatial-PCA approach that failed to separate communities at
full-corpus scale (ρ=−0.668, §§5–6 dropped 2026-04-17, see `decisions.md`). This is a genuine
revival of that dropped work, not a reversal of the paper-scope decision — the paper stays
§§1–4, this is the next thing after it.

**Possible extension named by the user:** use LitDiscover's own traversal *rounds* (BFS depth /
discovery-cycle number from `core/loop.py`) as an alternate or additional temporal/ordering axis,
instead of relying only on real publication year — worth exploring specifically on a
LitDiscover-recovered subgraph (K17-RGC, per `wiki/synthesis/synthesis.md`'s Q-SYNTH track) where
traversal order is itself a meaningful signal about a paper's position relative to the seed set,
not just when it was published.

**Where this connects:** `nst-timecurves-comparison.md` already has the three-method comparison
(NST / SG-t-SNE / Time Curves) this extends. `wiki/synthesis/synthesis.md`'s Q-SYNTH track already
plans an NST-vs-UMAP-vs-SG-t-SNE comparison on the K17-RGC subgraph specifically — this new
time-axis-layout idea and the LitDiscover-rounds extension belong there as a fourth condition or a
follow-up, not as separate new infrastructure.

**Not yet scoped:** which of t-SNE-with-time or force-directed-with-time to actually build first,
whether it lives in `citation-dynamics/` or gets folded into Q-SYNTH's own pipeline, and how
"LitDiscover round" would be extracted/logged per-paper if used as the axis (not currently a field
`traverse`/`core/loop.py` persists per included paper — would need checking).

---

## NEXT: address PDF review feedback
**Action:** User is reviewing `writings/zeitgeist_paper.pdf`. Address any content or formatting issues next session.

## VERIFY: bibliography entries
**Action:** Before submission, cross-check Aparicio2024, CostaFrigori2024, and CastilloCastillo2025 exact venues and page numbers — written from memory, may need correction.

---

## RESOLVED (for reference)

**Uncertain community labels (2026-04-18):** All four corrected in `data/analysis/community_labels.csv`. cid 13 was "Nonlinear Dynamics" → "Laser-Plasma Physics / High-Intensity Laser Interactions" (RMP papers on laser-QED, strongly coupled plasmas, laser wakefield accelerators). cid 14 → "Spintronics / Anomalous Hall Effect" (AHE distinct from cid 1 spin glasses). cid 16 was "Quantum Hall Effect" → "Quantum Optics / Orbital Angular Momentum of Light" (Allen et al. 1992 PRA OAM paper is top-5; year median 2009 consistent). cid 19 → "Conducting Polymers / SSH Model" (RMP paper is Heeger/SSH solitons, not surface physics).

**§§1 and 8 rewrite (2026-04-18):** Done. §1 pitches Zeitgeist → Leiden → per-community KS → temporal localization; no NST/Time Curves. §8 covers mixture validation, universal γ_c interpretation, limitations (APS-only, structure-only), future (aging model, cross-corpus, LLM labelling). See `writings/paper_draft_sections.md`.

**LaTeX §4 table (2026-04-18):** Done. Top-10 communities by size in `writings/paper_draft_sections.md` §4.

**NST §5 (2026-04-17):** Dropped. Spatial PCA not community-separating; temporal Spearman ρ=−0.668 ambiguous.

**Time Curves §6 (2026-04-17):** Dropped. Corpus-level centroid trajectory averages over 446 communities → uninformative.

**Q-SOTA (session 12):** Zeitgeist hypothesis confirmed as a gap. Nearest prior art: Costa & Frigori 2024, Aparício et al. 2024, Castillo-Castillo et al. 2025, Ke et al. 2023 PNAS.

**Q-SYNTH (sessions 17–20):** K17-RGC subgraph built (90 nodes, 7 communities). Caveat: 49/51 gold DOIs are non-APS — document as corpus coverage limitation.

**Aging model π(C):** Not in paper scope. Post-paper thesis chapter.
