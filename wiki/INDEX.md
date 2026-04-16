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

### citation-dynamics — ACTIVE (Phase 3 NST adapter written; training ready)

- Phases 1, 2, 5 pipeline: **all run successfully** (session 20)
  - HDF5: 709,803 nodes, 9,833,191 edges, 99.3% year coverage
  - Leiden full corpus: 446 communities, Q=0.7883
  - Synthesis subgraph: 90 nodes, 7 communities, Q=0.4291
- Phase 3 (NST): `src/nst/aps_adapter.py` + `src/nst/train_aps.py` written and smoke-tested
- **Next**: run full NST training (500 epochs, 500K edges) + start Phase 4 Time Curves
- **bluered stays MATLAB-only** — no port planned

### Synthesis — PIPELINE COMPLETE, TRAINING PENDING

- Subgraph built: 90 nodes (2 gold APS seeds + 88 neighbors)
- Leiden communities: 7
- Caveat: 49/51 K17-RGC gold DOIs are non-APS (math/CS journals) — corpus coverage gap

---

## Next priorities

1. **Run full NST training**: `python src/nst/train_aps.py --num_epochs 500 --max_edges 500000`
2. **Start Phase 4**: `src/timecurves/timecurves.py` (MDS + stress majorization)
3. **Start Phase 2 zeitgeist**: per-cluster power-law fitting to validate Zeitgeist hypothesis
