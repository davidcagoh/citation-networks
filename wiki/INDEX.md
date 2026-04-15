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

## Project status (2026-04-15)

### LitDiscover — COMPLETE

- Paper: "Robust Literature Discovery from Minimal Seeds: Validating LitDiscover on APS Citation Benchmarks and Live Surveys"
- All editorial tasks done; venue decision pending (ICASR 2026 watch)
- Live results: K17-RGC 100% (56/56), Ge21-HSS 100% (202/202), Le25-GLLM 73.7% (42/57)
- Paper docs frozen in `paper-wiki/`

### citation-dynamics — ACTIVE

- Research complete: NST/TimeCurves pipeline design (see nst-timecurves-comparison.md), SOTA gap confirmed (Zeitgeist hypothesis is novel)
- Implementation blocked pending planner + architect agent outputs (rate limit reset Apr 15 2pm ET)
- Core gap: Zeitgeist validation experiment not yet implemented; NST + Time Curves not yet integrated

### Synthesis — DESIGN PHASE

- Concept: take LitDiscover-recovered paper set → citation-dynamics pipeline → structured lit review output
- Concrete experiment design (Q-SYNTH) must be written to `wiki/synthesis-experiment.md` before implementation

---

## Next priorities

1. **Re-launch planner agent** — sprint plan for Zeitgeist validation + NST/TimeCurves integration (see session-log session 13/14 for full prompt)
2. **Re-launch architect agent** — MATLAB↔Python data handoff design, NST scalability at 709K nodes
3. **Write synthesis-experiment.md** — concrete spec for Q-SYNTH (test case: K17-RGC recovered set)
