# Citation Networks — Project Wiki

**Start every session:** read session-log.md → check open-questions.md.

---

## Wiki Files

| File | Purpose | Read when |
|---|---|---|
| [session-log.md](session-log.md) | What was done each session + UofT cluster reference | Start of every session |
| [open-questions.md](open-questions.md) | Unresolved issues by project | Deciding what to work on |
| [codebase-map.md](codebase-map.md) | citation-dynamics/ directory, pipeline status, key results | Before touching code |
| [nst-timecurves-comparison.md](nst-timecurves-comparison.md) | NST vs Time Curves research verdict; pipeline design | Before §§5–6 work |
| [synthesis-experiment.md](synthesis-experiment.md) | K17-RGC Q-SYNTH spec and pipeline | Before synthesis work |

### Frozen (LitDiscover — do not edit)
`thesis.md`, `decisions.md`, `argument-map.md`, `figure-roles.md`, `simulation-vs-production.md`

---

## Project status (2026-04-16)

### LitDiscover — COMPLETE (venue pending)
- Paper: "Robust Literature Discovery from Minimal Seeds"
- Live results: K17-RGC 100%, Ge21-HSS 100%, Le25-GLLM 73.7%
- ICASR 2026 watch; no active deadline
- Docs frozen in `paper-wiki/`

### citation-dynamics — ACTIVE
- **Done:** HDF5 pipeline, Leiden (446 communities, Q=0.788), Zeitgeist fitting (γ_c ∈ [2.1, 3.3], 100% KS pass), Time Curves implementation (proxy verified)
- **Running:** NST training, UofT cluster job 159670 (email at daveed@cs.toronto.edu)
- **Next:** Download NST results → run Time Curves → label communities by physics area → write §§5–6
- **Paper target:** COMPLEX NETWORKS 2026

### Synthesis — subgraph built, pending NST
- K17-RGC subgraph: 90 nodes (2 gold APS + 88 neighbors), 7 communities
- Caveat: 49/51 gold DOIs are non-APS; document as corpus coverage limitation
