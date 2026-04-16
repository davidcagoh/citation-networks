# Citation Networks — Project Wiki

Cross-project knowledge base covering citation-dynamics, the synthesis pipeline, and LitDiscover (archived). Updated by LLM; read in any order.

**Start every session here, then go to [session-log.md](session-log.md) to see what was last done.**

> **Wiki scope:** This wiki tracks active cross-project work. LitDiscover paper docs (figures, argument map, simulation notes) are frozen in [`lit-review/robust-literature-discovery/paper-wiki/`](../lit-review/robust-literature-discovery/paper-wiki/INDEX.md) and should not need further edits.

---

## Wiki Files

### Active (citation-dynamics + synthesis)

| File | Purpose | Read when |
|---|---|---|
| [session-log.md](session-log.md) | Reverse-chronological log of what was done each session | Start of every session |
| [open-questions.md](open-questions.md) | Unresolved issues spanning both projects (Q-SYNTH is the current blocker) | When deciding what to work on next |
| [codebase-map.md](codebase-map.md) | citation-dynamics/ directory tree, what's implemented vs stub | Before touching citation-dynamics code |
| [nst-timecurves-comparison.md](nst-timecurves-comparison.md) | NST vs Time Curves research verdict; novel pipeline design | Before starting NST/TimeCurves implementation |

### Frozen (LitDiscover paper — do not edit)

| File | Purpose |
|---|---|
| [thesis.md](thesis.md) | LitDiscover core argument |
| [decisions.md](decisions.md) | LitDiscover design decisions and parameter choices |
| [argument-map.md](argument-map.md) | Section → claim → evidence → figure |
| [figure-roles.md](figure-roles.md) | Per-figure status and argumentative role |
| [simulation-vs-production.md](simulation-vs-production.md) | How APS simulation relates to production LitDiscover |

---

## Project status (2026-04-16)

### LitDiscover — COMPLETE

- Paper: "Robust Literature Discovery from Minimal Seeds: Validating LitDiscover on APS Citation Benchmarks and Live Surveys"
- All editorial tasks done; venue decision pending (ICASR 2026 watch)
- Live results: K17-RGC 100% (56/56), Ge21-HSS 100% (202/202), Le25-GLLM 73.7% (42/57)
- Paper docs frozen in `paper-wiki/`

### citation-dynamics — ACTIVE (Python pipeline replacing MATLAB for Phases 1/2/5)

- **MATLAB blocker resolved for Phases 1, 2, 5**: full Python pipeline written (session 19)
- `src/python/build_aps_hdf5.py` — rebuilds HDF5 from CSV + JSON (replaces Phase 1 MATLAB) — **not yet run**
- `src/python/build_synthesis_subgraph.py` — Phase 5 subgraph (replaces MATLAB) — **not yet run**
- `src/python/leiden_cluster.py` — Leiden clustering via leidenalg (replaces MATLAB dep) — **not yet run**
- `data/exported/` is still empty — HDF5 must be built before any downstream step
- Phase 3 (`aps_adapter.py`) still blocked until HDF5 verified
- **bluered stays MATLAB-only** — no port planned

### Synthesis — SPEC COMPLETE, PYTHON PIPELINE READY TO RUN

- `wiki/synthesis-experiment.md` written (K17-RGC test case, Option B 1-hop subgraph)
- 51 gold DOIs in `data/synthesis/k17-rgc-gold-dois.txt`
- `build_synthesis_subgraph.py` written, awaiting HDF5 from `build_aps_hdf5.py`

---

## Next priorities

1. **Run `build_aps_hdf5.py`** — produces `data/exported/aps-2022-citation-graph.h5`; verify with `load_aps.py` round-trip
2. **Run `build_synthesis_subgraph.py`** — record gold match count + C_sub nnz
3. **Run `leiden_cluster.py --subgraph`** on the subgraph — record n_communities + modularity
4. **Start Phase 3** — `src/nst/aps_adapter.py` (wire HDF5 into NST training loop)
