# citation-dynamics — Design Decisions

Choices that have already been made and why. Read this before changing any parameter.

---

## Python-first pipeline; bluered stays MATLAB-only
**Decision date:** 2026-04-16
**Why:** `mat73` can read the sparse matrix `C` from the MATLAB `.mat` files but silently drops all MATLAB string arrays (`doi`, `pubDate`, `authorName`, `affiliationName`), returning `None`. Rebuilding the full graph from CSV + JSON source in Python is cleaner, reproducible, and dependency-free. `bluered` (~20 MATLAB files implementing the blue-red bisection algorithm) has no Python equivalent and stays MATLAB-only.
**Implication:** `src/phase1_build_graph.py` is the canonical entry point. All downstream scripts read from HDF5, not from `.mat`.

---

## Target venue: COMPLEX NETWORKS 2026
**Decision date:** 2026-04-16
**Why:** Network science community understands both the domain question (Zeitgeist) and the methodology (community detection, power laws). Hard deadline forces the paper to completion. Scientometrics was the alternative but slower review cycle and less methodological audience.
**Implication:** ~August CFP deadline. Paper must be submission-ready by then.

---

## Power-law fitting: K_min scan, not fixed K_min=1
**Decision date:** 2026-04-16
**Why:** Fixed K_min=1 gives γ≈1.38, inconsistent with Barabasi (2016) §4.13 (γ=2.79 for APS, K_min=49). Scan over [1,100] gives γ_c ∈ [2.1, 3.3], mean=2.50 — consistent with literature and reveals genuine inter-community variation.
**Implication:** Always use `--xmin_strategy scan --ks_boots 500` for paper runs. K_min=1 is debug-only.

---

## Zeitgeist framing: heterogeneous exponents
**Decision date:** 2026-04-16
**Why:** With proper K_min scan, γ_c varies (2.1–3.3, std=0.246). Different research generations attract citations at different rates AND occupy different temporal windows. Both axes of variation are real.
**Implication:** §4 claims communities differ in temporal position AND citation attraction rate.

---

## §§5–6 (NST + Time Curves) dropped from paper scope
**Decision date:** 2026-04-17
**Why:** Time Curves on the full corpus computes per-year centroids averaged over 446 communities — the corpus-level signal is noise. NST diagnostic figures (spatial PCA, temporal vs year Spearman ρ=−0.668) were not interpretable or compelling. Both were adopted for methodological novelty rather than because they answered a specific research question.
**Implication:** Paper scope is now §§1–4 only. NST embeddings and Time Curves outputs are archived in `data/` but not cited in the paper. The embedding/clustering comparison work is deferred to the signature-patterns thesis chapter — see `wiki/synthesis/methods-comparison.md`.

---

## Paper scope: §§1–4 only
**Decision date:** 2026-04-17
**Sections:**
1. Introduction — Zeitgeist hypothesis
2. Related work
3. Dataset + global degree distribution (γ_global = 2.74)
4. Community mixture decomposition — Leiden, per-community power-law fitting, temporal localization

**Not in scope:** NST embeddings, Time Curves, SG-t-SNE visualization, aging model π(C).

---

## Canonical data lives in `citation-dynamics/data/processed/`; lit-review symlinks there
**Decision date:** 2026-04-12
**Why:** Eliminates 662 MB of duplication. Single canonical copy; symlink is gitignored in lit-review.
**Implication:** If the APS dataset is updated, update `citation-dynamics/data/processed/` only.
