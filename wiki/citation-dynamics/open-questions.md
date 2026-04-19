# citation-dynamics — Open Questions

Check this at the start of each session.

---

## NEXT: push 2 commits ahead of origin
**Action:** `git push` when ready.

---

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
