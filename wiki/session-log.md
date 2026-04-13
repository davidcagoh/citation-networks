# Session Log

Reverse-chronological log of what was done each session. Read this at the start of every new session to resume without re-deriving state.

---

## 2026-04-13 (session 14) — Git tidy: citation-dynamics/ tracked; wiki condensed; .gitignore hardened

### What was done
- **Committed citation-dynamics/ source** to outer repo for the first time (141 files: MATLAB src/, deps/, utils/, writings/, notebooks/, config.py, README.md)
- **Hardened .gitignore**: now excludes citation-dynamics/data/ (663MB), citation-dynamics/deps/+leiden/private/deps/igraph/ (77MB C vendor source), citation-dynamics/utils/*.mat + writings/*.pdf, lit-review/automated-lit-reviews/ (1.5GB), lit-review/automated-lit-reviews-v2/ (nested git repo), *.log, .ipynb_checkpoints/, *.egg-info/
- **Wiki cleanup**: deleted Architecture Design_ LitReview v2.md and N_ROUNDS_Extension.md (stale/merged); condensed session-log pre-session-13; added Venue section to decisions.md; collapsed resolved Q6–Q16 figure fixes into single summary line in open-questions.md; condensed INDEX.md figures section
- No remote configured — push deferred (repo is local-only at present)

### State at end of session
- Working tree clean; one commit (ff07e66) on master
- citation-dynamics/ fully tracked (source only, data excluded)
- Wiki consistent and condensed
- Planner + architect agents still need re-launching after Apr 15 2pm ET rate limit reset

### What to do next session
1. **Re-launch planner agent** (after Apr 15 2pm ET): "Plan Zeitgeist validation experiment + NST/TimeCurves integration" — see session 13 entry for full prompt context
2. **Re-launch architect agent**: "Architect NST-TimeCurves integration design" — same context
3. **Do NOT start implementation** until both have returned with a plan
4. Consider adding a git remote if the repo should be pushed to GitHub

---

## 2026-04-12 (session 13) — NST/Time Curves exploration initiated; TWO AGENTS STILL RUNNING

### What was done
- User confirmed openness to exploring Neural Spacetimes and/or Time Curves as replacement/supplement for SG-t-SNE
- Launched two background agents (results NOT yet in wiki — must check on next session start):
  1. **Explore agent** (a6620dd4869e6f1e0): mapping citation-dynamics/ codebase — directory tree, algorithms implemented, what's complete vs stub
  2. **Research agent** (a8ae71cd38f08a059): Neural Spacetimes vs Time Curves comparison — goal fit, technical compatibility, experimental design, open-source availability
- Working hypothesis (unconfirmed): NST = representation layer, Time Curves = visualization layer, SG-t-SNE replaceable by NST→TimeCurves pipeline. Research agent will confirm or refute.

### Updates within session 13 (explore agent returned)

**Explore agent COMPLETE** — codebase map written to `wiki/codebase-map.md`. Key findings:
- SG-t-SNE: ✅ working via Julia SGtSNEpi bridge
- BlueRed DT-II + Leiden: ✅ both implemented
- Temporal window analysis: ✅ implemented (`query_XY_subgraph`, `analyze_citation_window`)
- **Phase detection (quantitative model)**: ❌ THE CORE GAP
- **Backward influence dedicated pipeline**: ⚠️ partial
- **Zeitgeist validation experiment**: ❌ not implemented

**Research agent COMPLETE** — written to `wiki/nst-timecurves-comparison.md`. Key verdict:
- NST = representation layer (before SG-t-SNE), handles DAG directionality natively
- Time Curves = macro trajectory visualization (after any embedding), loops=phases, cusps=transitions
- SG-t-SNE = keep for spatial layout
- **Novel pipeline: Citation DAG → NST → SG-t-SNE → Time Curves** (no prior work found combining all three)
- NST adaptation: 2-3 days (OGBN-Arxiv demo in repo); Time Curves: reimplement in Python (simple algorithm)
- Planner + architect agents launched to produce experimental roadmap

**Planner + architect agents HIT RATE LIMIT** — zero output. Rate limit resets Apr 15 at 2pm ET.

### ⚠️ NEXT SESSION MUST DO FIRST (after Apr 15 2pm ET)
1. Re-launch planner agent: "Plan Zeitgeist validation experiment" — see session-log for full prompt context
2. Re-launch architect agent: "Architect NST-TimeCurves integration design" — see session-log for full prompt context
3. Both agents need: codebase-map.md + nst-timecurves-comparison.md as context (already in wiki)
4. Do NOT start implementation until both have returned

### What to tell the planner agent (re-launch prompt summary)
- Goal: sprint plan for Zeitgeist validation experiment + NST + Time Curves integration
- Existing: SG-t-SNE, BlueRed, Leiden, temporal windows all in MATLAB
- Missing: Zeitgeist validation (global = mixture of per-cluster power laws), NST (Python/PyTorch), Time Curves (Python reimplement)
- New pipeline: Citation DAG → NST → SG-t-SNE → Time Curves
- Need: ordered phases, files to create, success criteria, LOE per phase

### What to tell the architect agent (re-launch prompt summary)
- Goal: design data handoff (MATLAB ↔ Python), NST scalability for 709K nodes, pipeline orchestration, Time Curves Python reimplement design
- Key questions: MAT vs CSV vs HDF5 for export, mini-batch NST training, MATLAB→Python orchestration strategy

### State at end of session 13 (final)
- Commits: codebase-map.md, nst-timecurves-comparison.md (3ebac11)
- Rate limit hit — planner + architect not run
- All research complete; implementation planning blocked until Apr 15

---

## 2026-04-12 (session 12) — Outer repo init; wiki moved; memory written; SOTA search launched

### What was done
- `git init` at `citation-networks/` root (outer repo, commit `eadf9ef`)
- Moved `paper-wiki/` → `citation-networks/wiki/`; `.gitignore` excludes `lit-review/robust-literature-discovery/` and PDFs
- Added `README.md` at `citation-networks/` root with project structure, Zeitgeist hypothesis, pipeline diagram
- Added `project_citation_networks.md` to `~/.claude-shared/projects/` and indexed in `MEMORY.md`
- Launched background SOTA gap search (2024–2026) covering Q1: temporal citation phases, Q2: LLM synthesis SOTA, Q3: temporal graph embedding advances since Nakis 2024
- Search completed same session; results integrated into `open-questions.md` (Q-SOTA resolved)

### State at end of session
- Outer repo: 3 commits (eadf9ef, ffe6b7e, + this one)
- Wiki tracked; nested RLD repo correctly gitignored
- Q-SOTA resolved: Zeitgeist hypothesis confirmed as a gap; nearest prior art identified; repositioning actions written
- Neural Spacetimes (ICLR 2025) is the key new competitor — thesis needs to address it

---

## Sessions 1–11 — archived

Sessions 1–11 covered: figure redesigns (fig1–fig8), paper rewrite (Abstract, §1, §2, §5, §9), LaTeX compile fix, fig9 dropped, refs [1–23] added, project reorganized (thesis→citation-dynamics/, wiki relocated, outer git init, data deduplication via symlink, citation-dynamics/ README written).

All design choices captured in **decisions.md**. All open/resolved questions in **open-questions.md**. Per-figure status in **figure-roles.md**.
