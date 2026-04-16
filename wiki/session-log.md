# Session Log

Reverse-chronological log of what was done each session. Read this at the start of every new session to resume without re-deriving state.

---

## 2026-04-16 (session 20) — Phases 1/2/5 pipeline runs confirmed; Phase 3 NST adapter written

### What was done

**All pipeline steps from session 19 plan now run successfully:**

| Step | Script | Result |
|---|---|---|
| Phase 1 (HDF5 build) | `build_aps_hdf5.py` | 709,803 nodes, 9,833,191 edges, 99.3% year coverage |
| Phase 1 (round-trip) | `load_aps.py` | PASSED |
| Phase 5 (subgraph) | `build_synthesis_subgraph.py` | 90 nodes (2 gold + 88 neighbors), nnz=189 |
| Phase 2 (full Leiden) | `leiden_cluster.py` | 446 communities, Q=0.7883 → `aps-2022-leiden-1p00.npz` |
| Phase 5 (subgraph Leiden) | `leiden_cluster.py --subgraph` | 7 communities, Q=0.4291 → `k17-rgc-subgraph-leiden-1p00.npz` |

**Phase 3 — NST adapter written and smoke-tested:**

| File | Purpose | Status |
|---|---|---|
| `src/nst/aps_adapter.py` | Builds NST input from HDF5 + Leiden | **Written, self-test PASSED** |
| `src/nst/train_aps.py` | Trains NeuralSpacetime, exports embeddings | **Written, smoke-test PASSED (10 epochs)** |

**Key note — K17-RGC gold DOI match rate:**
Only 2/51 gold DOIs matched in the APS corpus. K17-RGC papers are topology/TDA literature (math/CS journals), not APS physics. The subgraph is 90 nodes. This is expected but worth noting — the synthesis experiment will need to document this as a corpus coverage limitation.

**NST adapter design decisions:**
- Feature dim = 4: [year_norm, log_indegree_norm, log_outdegree_norm, community_norm]
- No pre-trained embeddings (APS has none); structural features only
- Edge weights = cosine similarity of node feature vectors (same convention as OGBN-Arxiv adapter)
- Default: sample 500K / 9.8M edges for training; cache results in `data/exported/`
- Model (default): space_dim=4, time_dim=4, J_encoder=6 → 53,373 parameters — fits CPU

### State at end of session

- `src/nst/aps_adapter.py`: created, PASSED self-test
- `src/nst/train_aps.py`: created, smoke-test (10 epochs, 10K edges) PASSED
- `data/exported/aps-2022-leiden-1p00.npz`: Leiden full-corpus result
- `data/synthesis/k17-rgc-subgraph-leiden-1p00.npz`: Leiden subgraph result

### What to do next session

1. **Run full NST training** (Phase 3):
   ```bash
   source .venv/bin/activate
   python citation-dynamics/src/nst/train_aps.py \
       --num_epochs 500 --batch_size 2000 --max_edges 500000 --display_epoch 50
   # Expect: ~30-60 min CPU; space loss < 0.05 at convergence
   # Output: data/exported/aps-nst-model.pt + aps-nst-embeddings.npy
   ```

2. **Start Phase 4 — Time Curves** (`src/timecurves/timecurves.py`):
   - Python reimplementation: MDS init → stress majorization with temporal ordering penalty
   - ~150–200 lines, numpy+scipy only (see session 16 architect spec)
   - Apply to subgraph first (90 nodes), then to a per-cluster sample

3. **Start Phase 2 zeitgeist scripts** (pure Python, no new dependencies):
   - `src/zeitgeist/zeitgeist_percluster_fit.py` — per-cluster in-degree distribution fitting
   - Goal: confirm each cluster is approximately power-law (Zeitgeist hypothesis)
   - Input: Leiden membership + HDF5 degree data

4. **Commit** `src/nst/` scripts

---

## 2026-04-16 (session 19) — Python pipeline replaces MATLAB for Phases 1/2/5; bluered stays MATLAB

### What was done

- **Diagnosed MATLAB blocker**: `mat73` can read `C` (scipy sparse, 705 181 × 705 181, 9.7M nnz) from the `.mat` but cannot parse MATLAB string arrays — `doi` and `pubDate` return `None`. `scipy.io.loadmat` also fails on v7.3 HDF5 mats with string arrays.
- **Decision: rebuild from source, skip mat73 for strings.** Read edges from `aps-dataset-citations-2022.csv` (9.8M pairs); read pubDate from JSON metadata. No dependency on the existing `.mat` files.
- **Found JSON metadata**: `aps-dataset-metadata-2022/` exists at `/Users/davidgoh/LocalFiles/2024_duke_thesis_deprecated/cs493/aps-dataset-metadata-2022` — 720 535 JSON files.
- **Decision: bluered stays MATLAB-only.** ~20 MATLAB files, no Python equivalent, manual port not worth the tokens.
- **Installed Python deps** into `.venv`: `leidenalg`, `igraph`, `umap-learn`, `mat73`.

**New Python scripts (all syntax-checked OK):**

| Script | Replaces | Status |
|---|---|---|
| `src/python/build_aps_hdf5.py` | `export_for_python.m` + Phase 1/2 | Written, **not yet run** |
| `src/python/build_synthesis_subgraph.py` | `build_synthesis_subgraph.m` (Phase 5) | Written, **not yet run** |
| `src/python/leiden_cluster.py` | `deps/+leiden/` MATLAB wrapper | Written, **not yet run** |

**Updated:** `src/python/load_aps.py` — now also loads `doi` field from HDF5 (previously ignored).

### How to run next session

**Step 1 — Build HDF5** (≈10–20 min on CPU; reads 9.8M CSV edges + 720K JSON files):
```bash
cd citation-networks
.venv/bin/python citation-dynamics/src/python/build_aps_hdf5.py
# Expect: data/exported/aps-2022-citation-graph.h5
# Check: ~705K nodes, ~9.7M edges, year coverage ~80%+
```

**Step 2 — Verify round-trip:**
```bash
.venv/bin/python citation-dynamics/src/python/load_aps.py
# Expect: "Round-trip test PASSED"
```

**Step 3 — Build Phase 5 subgraph:**
```bash
.venv/bin/python citation-dynamics/src/python/build_synthesis_subgraph.py
# Expect: data/synthesis/k17-rgc-subgraph.npz + k17-rgc-subgraph-dois.txt
# Record: gold matched count (≤51), neighbor count, C_sub nnz
```

**Step 4 — Leiden on subgraph:**
```bash
.venv/bin/python citation-dynamics/src/python/leiden_cluster.py \
    --subgraph citation-dynamics/data/synthesis/k17-rgc-subgraph.npz \
    --out citation-dynamics/data/synthesis
# Expect: k17-rgc-subgraph-leiden-1p00.npz
# Record: n_communities, modularity
```

### State at end of session
- `src/python/build_aps_hdf5.py`: written, not yet run
- `src/python/build_synthesis_subgraph.py`: written, not yet run
- `src/python/leiden_cluster.py`: written, not yet run
- `src/python/load_aps.py`: updated (doi field), not yet run end-to-end
- `data/exported/`: still empty — HDF5 needs to be produced

### What to do next session
1. **Run `build_aps_hdf5.py`** → verify HDF5 exists and round-trip passes
2. **Run `build_synthesis_subgraph.py`** → record gold match count + C_sub nnz
3. **Run `leiden_cluster.py` on subgraph** → record n_communities + modularity
4. **Start Phase 3** (`src/nst/aps_adapter.py`) — wire HDF5 into NST training loop

---

## 2026-04-16 (session 18) — NST demo verified; Phase 5 Q-SYNTH subgraph script written

### What was done

- **Tasks 1 + 2 (Phase 1 + 2 MATLAB)**: Cannot be run from CLI — MATLAB required. Instructions below. VS Code option documented.
- **Task 3 — NST OGBN-Arxiv demo** (`deps/nst/`):
  - Confirmed NST already cloned. PyG and OGB not in default Python env (3.13.1).
  - Installed via pip: `torch-geometric==2.7.0`, `ogb==1.3.6`.
  - Ran `arxiv_embedding/train_real.py --num_epochs 1 --batch_size 1000` successfully on CPU.
  - Dataset downloaded to `/tmp/ogbn-arxiv` (~80 MB). Processed: **169 343 nodes**, **1 165 974 edges** (269 rejected at cosine sim > 0.99).
  - CUDA not available on this machine (Apple Silicon, no GPU).
  - Created `deps/nst/REQUIREMENTS.md` with Python version, CUDA status, install steps, timings.
- **Task 4 — Phase 5 Q-SYNTH** (`src/synthesis/build_synthesis_subgraph.m`):
  - Reads `data/synthesis/k17-rgc-gold-dois.txt` (51 DOIs).
  - Matches DOIs to corpus via `ismember(gold_dois, doi)`.
  - Expands to 1-hop: `C(gold_idx,:)` (gold→others) + `C(:,gold_idx)` (others→gold).
  - Builds induced subgraph `C_sub = C(sub_idx, sub_idx)`.
  - Saves `data/synthesis/k17-rgc-subgraph.mat` with C_sub, sub_dois, sub_idx, gold_mask, gold_idx, counts.
  - **Not yet run** — requires MATLAB with MAT file loaded.

### MATLAB (Tasks 1 + 2) — how to run when MATLAB is available

**VS Code option**: Install the [MATLAB extension by MathWorks](https://marketplace.visualstudio.com/items?itemName=MathWorks.language-matlab) (extension ID `MathWorks.language-matlab`). It provides syntax highlighting and `Run File` button support. Requires a local MATLAB install or MATLAB Online with the extension's language server. For running `.m` files directly in VS Code, MATLAB must be on PATH.

**Phase 1 — export_for_python.m**:
```
cd citation-dynamics/src/export
% In MATLAB:
run('export_for_python.m')
% Expect: data/exported/aps-2022-citation-graph.h5 (~80 MB)
% Check /edge_row ~9.7M entries, /year ~709K entries
% Then verify round-trip:
python citation-dynamics/src/python/load_aps.py
% Expect: PASSED
```

**Phase 2 — zeitgeist_cluster.m**:
```
cd citation-dynamics/src/zeitgeist
% In MATLAB:
run('zeitgeist_cluster.m')
% Record: Q value, cluster count, top-10 cluster sizes
% Output: data/processed/aps-2022-leiden-clusters.mat
```

**Phase 5 — build_synthesis_subgraph.m** (NEW this session):
```
cd citation-dynamics/src/synthesis
% In MATLAB:
run('build_synthesis_subgraph.m')
% Expect: reports gold matched count (≤51), neighbor count, C_sub nnz
% Output: data/synthesis/k17-rgc-subgraph.mat
```

### State at end of session
- `deps/nst/REQUIREMENTS.md`: created, committed — NST Python/CUDA requirements documented
- `src/synthesis/build_synthesis_subgraph.m`: created — **not yet run** (needs MATLAB)
- `src/export/export_for_python.m`: **not yet run**
- `src/python/load_aps.py`: **not yet run** (needs H5 from Phase 1)
- `src/zeitgeist/zeitgeist_cluster.m`: **not yet run**

### What to do next session
1. **Run Phase 1** in MATLAB: `export_for_python.m` → verify H5 → `python load_aps.py`
2. **Run Phase 2** in MATLAB: `zeitgeist_cluster.m` → record Q + cluster count
3. **Run Phase 5** in MATLAB: `build_synthesis_subgraph.m` → record C_sub size
4. **Start Phase 3**: `src/nst/aps_adapter.py` (once Phase 1 H5 verified)

---

## 2026-04-16 (session 17) — Phase 1 + 2 implementation; Q-SYNTH DOI extraction

### What was done
- **Q-SYNTH spec confirmed**: Option B (1-hop subgraph) agreed. Spec is correct.
- **Gold DOI extraction**: Parsed `K17-RGC_gold.json` → `data/synthesis/k17-rgc-gold-dois.txt`. 56 entries in the gold JSON, **51 non-null DOIs** (5 entries are books/preprints with no DOI). File created.
- **Phase 1 — MATLAB→HDF5 export** (`src/export/export_for_python.m`):
  - Loads `data/processed/aps-2022-author-doi-citation-affil.mat`
  - Converts sparse C via `find(C)` → edge_row / edge_col (int32, 0-indexed)
  - Converts pubDate strings via `datetime()` → year (float32)
  - Writes `data/exported/aps-2022-citation-graph.h5` with `/edge_row`, `/edge_col`, `/year`
  - Metadata attributes: n_nodes, n_edges, source_mat, created
  - **Not yet run** — requires MATLAB with the MAT file accessible
- **Phase 1 — Python loader** (`src/python/load_aps.py`):
  - `load_h5()` → dict of numpy arrays
  - `to_scipy_sparse()` → scipy csr_matrix
  - `to_pyg()` → PyG Data object (edge_index, year, num_nodes)
  - `round_trip_test()` → asserts index bounds, shape, nnz, and PyG consistency
  - Run: `python src/python/load_aps.py [--h5 PATH]`
- **Phase 2 — Full-corpus Leiden** (`src/zeitgeist/zeitgeist_cluster.m`):
  - Loads full C matrix, symmetrizes (A = C + C', binarized via spones)
  - Calls `leiden.cluster(A, 'modularity-ngrb', 'gamma', 1.0, 'seed', 42)`
  - Saves `data/processed/aps-2022-leiden-clusters.mat`: cid (int32[N]), qq, n_clusters, cluster_sizes
  - Reports Q, cluster count, top-10 sizes, singleton count
  - **Not yet run** — pure MATLAB, independent of Phase 1

### NST clone task (not completed this session)
- Task: clone NST repo into `deps/nst/` (gitignored), run OGBN-Arxiv demo, document Python/CUDA requirements
- Blocked: need NST repo URL and GPU access confirmation before cloning
- Deferred to next session

### State at end of session
- `wiki/synthesis-experiment.md`: committed
- `data/synthesis/k17-rgc-gold-dois.txt`: committed (51 DOIs)
- `src/export/export_for_python.m`: committed, **not yet run**
- `src/python/load_aps.py`: committed, **not yet run** (needs H5 from Phase 1)
- `src/zeitgeist/zeitgeist_cluster.m`: committed, **not yet run**
- NST clone: deferred

### What to do next session
1. **Run Phase 1 in MATLAB**: `export_for_python.m` → verify H5 file created, run `load_aps.py` for round-trip
2. **Run Phase 2 in MATLAB**: `zeitgeist_cluster.m` → report cluster count
3. **Clone NST repo** into `deps/nst/` (confirm URL first), run OGBN-Arxiv demo
4. **Start Phase 3**: `src/nst/aps_adapter.py` (once Phase 1 H5 verified)
5. **Start Phase 5 (Q-SYNTH)**: `src/synthesis/build_synthesis_subgraph.m` using `data/synthesis/k17-rgc-gold-dois.txt`

---

## 2026-04-16 (session 16) — Planner + architect returned; synthesis experiment spec written

### What was done
- **Planner agent**: Sprint plan for Zeitgeist validation + NST/TimeCurves integration. 6 phases, 10–12 day critical path, ~25–34 days total with parallelism.
- **Architect agent**: MATLAB↔Python data handoff design, NST scalability at 709K nodes, orchestration strategy, Time Curves Python interface.
- **`wiki/synthesis-experiment.md`**: Q-SYNTH spec written (K17-RGC test case, Option B subgraph, full output format, success criteria).

### Key decisions from planner + architect

**Data handoff format: HDF5** (both agents independently converged on this)
- MATLAB `h5create`/`h5write` → Python `h5py`. Export: COO triplets (edge_row, edge_col) as int32[9.7M] + year as float32[709K]
- ~80 MB export file. Reason: `mat73` already known to fail on MATLAB string arrays (doi, pubDate return None)
- Export script: `src/export/export_for_python.m`; Python loader: `src/python/load_aps.py`

**NST scalability strategy: NeighborLoader mini-batch**
- PyG `NeighborLoader`, batch_size=4096, num_neighbors=[25] → ~1.3 GB GPU budget
- If OOM on full 709K: subsample to 2000–2022 (~300K nodes) as documented fallback
- Must first clone NST repo and verify OGBN-Arxiv demo runs locally before APS adaptation

**Orchestration: Makefile**
- File-based dependency tracking. `make nst` re-runs only the NST step. `make all` runs full pipeline.
- Beats `system()` from MATLAB (Python errors buried) and manual (no reproducibility)

**Time Curves Python interface**
```python
def time_curves(distance_matrix: np.ndarray, labels=None, temporal_weight=0.3, n_iter=300) -> TimeCurvesResult
```
Algorithm: classical MDS init → stress majorization with temporal ordering penalty → cusp/loop detection. ~150–200 lines, numpy+scipy only.

**NST output return path**: HDF5 → MATLAB `h5read` for overlay on SG-t-SNE. Python quick-look via matplotlib during training.

### Phase order (planner output)
```
Phase 1 (Day 1):      Export layer — MATLAB→HDF5. Unblocks all Python work.
Phase 2 (Days 2–5):   Zeitgeist validation — MATLAB only, independent.
Phase 3 (Days 2–5):   NST integration — Python, parallel with Phase 2.
Phase 4 (Days 5–6):   Time Curves — core independent; APS application needs Phase 3.
Phase 5 (Days 3–5):   Q-SYNTH — MATLAB only, independent of Phases 3–4.
Phase 6 (Days 7–9):   Integration + comparison.
```
Critical path: Phase 1 → Phase 3 → Phase 4 → Phase 6 (8–10 days)

### New files to create (complete list from planner)
```
src/export/export_for_python.m        # MATLAB→HDF5 (Phase 1, Day 1 — START HERE)
src/python/load_aps.py                # HDF5→PyG Data
Makefile                              # Pipeline orchestration
src/zeitgeist/zeitgeist_cluster.m     # Full-corpus Leiden
src/zeitgeist/zeitgeist_percluster_fit.m
src/zeitgeist/zeitgeist_mixture_test.m
src/zeitgeist/zeitgeist_temporal.m
src/zeitgeist/zeitgeist_figures.m
src/nst/aps_adapter.py
src/nst/train_aps.py
src/nst/export_for_sgtsne.m
src/nst/compare_embeddings.py
src/timecurves/timecurves.py
src/timecurves/aps_timecurves.py
src/synthesis/build_synthesis_subgraph.m
src/synthesis/run_synthesis_pipeline.m
src/synthesis/generate_synthesis_report.m
data/synthesis/k17-rgc-gold-dois.txt
requirements.txt
```

### Synthesis experiment spec (wiki/synthesis-experiment.md)
- **Input**: 56 K17-RGC gold DOIs + 1-hop APS neighborhood (~500–2K papers)
- **Pipeline**: build_synthesis_subgraph → Leiden → temporal binning → SG-t-SNE → per-cluster stats
- **Output**: cluster map PDF, temporal emergence curves PDF, Markdown report (clusters + representative papers + active period)
- **Success**: ≥70% of clusters interpretable by a TDA domain expert; temporal ordering historically plausible
- **Not started**: STEP 4 holds — no implementation until planner+architect returned and spec agreed

### State at end of session
- Planner sprint plan: complete
- Architect design: complete
- Synthesis experiment spec: written to `wiki/synthesis-experiment.md`
- Implementation: NOT STARTED (per STEP 4 instruction)
- Working tree: clean (synthesis-experiment.md needs to be committed)

### What to do next session
1. **Commit** `wiki/synthesis-experiment.md`
2. **Review spec**: confirm Q-SYNTH Option B (1-hop subgraph) is correct input scope
3. **Start Phase 1** (Day 1): write `src/export/export_for_python.m`, run it, verify Python round-trip
4. **Start Phase 2 in parallel**: `src/zeitgeist/zeitgeist_cluster.m` (full-corpus Leiden — pure MATLAB, independent)
5. **Clone NST repo** into `deps/nst/` (gitignored), run OGBN-Arxiv demo, document dependencies
6. **Extract K17-RGC gold DOIs** from `lit-review/robust-literature-discovery/projects/kahle-simplicial-geometry/` traversal output → `data/synthesis/k17-rgc-gold-dois.txt`

---

## 2026-04-15 (session 15) — Wiki restructured; LitDiscover marked complete

### What was done
- **Wiki restructured**: `wiki/INDEX.md` retitled from "LitDiscover Paper" to "Citation Networks — Project Wiki"; scope is now explicitly cross-project. Active files (session-log, open-questions, codebase-map, nst-timecurves-comparison) separated from frozen LitDiscover docs (thesis, decisions, argument-map, figure-roles, simulation-vs-production).
- **paper-wiki frozen**: Added archive notice to `paper-wiki/INDEX.md`; it is now read-only.
- **Duplicate PDF removed**: Barabasi Network Science PDF deleted from `wiki/`; canonical copy remains in `paper-wiki/`.
- **LitDiscover editorial tasks complete**: All three live experiments done (K17-RGC 100%, Ge21-HSS 100%, Le25-GLLM 73.7%); Q11 citations and PI review done. Venue decision pending.

### State at end of session
- `wiki/` = live cross-project wiki; session-wrap targets this going forward
- `paper-wiki/` = frozen archive; do not edit
- citation-dynamics active work: awaiting planner + architect agent outputs

### What to do next session
1. **Re-launch planner agent**: sprint plan for Zeitgeist validation + NST/TimeCurves integration
2. **Re-launch architect agent**: MATLAB↔Python data handoff, NST scalability at 709K nodes
3. **Write `wiki/synthesis-experiment.md`**: concrete Q-SYNTH spec (test case: K17-RGC recovered set)
4. Do NOT implement anything until planner + architect have returned

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
