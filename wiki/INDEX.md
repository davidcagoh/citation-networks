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

### citation-dynamics — ACTIVE (implementation phase)

- Sprint plan + architecture complete (sessions 16–17). HDF5 handoff design finalized.
- Phase 1 script (`export_for_python.m`) and Phase 2 script (`zeitgeist_cluster.m`) written — **not yet run** (need MATLAB)
- Phase 5 Q-SYNTH subgraph script (`build_synthesis_subgraph.m`) written — **not yet run**
- NST OGBN-Arxiv demo verified on CPU (169K nodes, 1.16M edges). `deps/nst/REQUIREMENTS.md` created.
- Phase 3 (`aps_adapter.py`) blocked until Phase 1 HDF5 verified

### Synthesis — SPEC COMPLETE, IMPLEMENTATION IN PROGRESS

- `wiki/synthesis-experiment.md` written (K17-RGC test case, Option B 1-hop subgraph)
- 51 gold DOIs extracted to `data/synthesis/k17-rgc-gold-dois.txt`
- `build_synthesis_subgraph.m` written, awaiting MATLAB run

---

## Next priorities

1. **Run Phase 1 in MATLAB** — `export_for_python.m` → verify HDF5 → `python load_aps.py` round-trip
2. **Run Phase 2 in MATLAB** — `zeitgeist_cluster.m` → record Q value + cluster count
3. **Run Phase 5 in MATLAB** — `build_synthesis_subgraph.m` → record C_sub size + gold match count
4. **Start Phase 3** — `src/nst/aps_adapter.py` (once Phase 1 HDF5 confirmed)
