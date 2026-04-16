# Session Log

Reverse-chronological. Start every session here, then check open-questions.md.

---

## UofT Cluster — permanent reference

SSH (no VPN needed):
```
Host uoft
    HostName cs.toronto.edu
    User daveed
    ForwardAgent yes

Host comps0
    HostName comps0
    User daveed
    ProxyJump uoft
    LocalForward 8888 localhost:8888
```
One-time key setup (eliminates password prompts): `ssh-copy-id uoft && ssh-copy-id -o ProxyJump=uoft comps0`

Cluster env: `source /w/20251/daveed/torch_env/bin/activate`  
Project root: `/w/20251/daveed/citation-dynamics/`  
Upload: `scp <file> comps0:/w/20251/daveed/citation-dynamics/<dest>`

Slurm (partition=gpunodes, 1 GPU, 4 CPU, 16G):
```bash
sbatch train_cluster.slurm          # submit
squeue -u daveed                    # check
tail -f logs/train_<jobid>.out      # stream
scancel <jobid>                     # cancel
```

---

## 2026-04-16 (session 21) — Paper outline; Zeitgeist fitting; Time Curves; NST on cluster

### What was done

- **Paper target:** COMPLEX NETWORKS 2026 (Springer, ~Aug deadline)
- **Paper outline:** `writings/paper_draft_sections.md` — §§1–8 outline with TODOs; outline-only, no premature prose
- **Phase 2b — Zeitgeist fitting (`src/phase2b_zeitgeist_fit.py`):**
  - 446 Leiden communities; 25 have ≥30 nodes covering 99.8% of papers
  - **With K_min scan + 500 boots:** γ_c ∈ [2.099, 3.268], mean=2.500, std=0.246 — consistent with Barabasi (2016) §4.13 which gets γ=2.79 for this corpus type. Communities have genuinely heterogeneous exponents.
  - 100% of large communities pass KS power-law test
  - Temporal IQR: mean 18.4y, median 17y; 68% have IQR<20y; medians span 1950–2017
  - Results: `data/analysis/zeitgeist_community_fits.csv`, `zeitgeist_summary.txt`
- **Phase 4 — Time Curves (`src/phase4_timecurves.py`):**
  - Implemented: MDS init + SMACOF + temporal smoothing + cusp/loop detection; ~200 lines numpy+scipy
  - Proxy run verified (structural features, stress=0.000294); 0 cusps/loops expected in proxy mode
  - Full run awaits NST embeddings
- **Phase 3 — NST training on UofT cluster:**
  - GPU fix: `phase3_nst_train.py` now auto-detects CUDA
  - Job **159670** submitted to gpunodes; email to daveed@cs.toronto.edu on END/FAIL
  - 500K-edge cache pre-uploaded; job skips data prep
- **Makefile:** phases 2b, 4 (timecurves + timecurves-proxy) added; `all` chains hdf5→leiden→nst→timecurves

### Barabasi note
Barabasi (2016) §4.13 fits APS corpus at γ=2.79 (K_min=49, pure power law fails p<10^-4) or γ=3.03 (saturation+cutoff, p=0.69). Global KS failure is direct motivation for the mixture framing. Cite this.

### State at end of session

| Artifact | Location | Status |
|---|---|---|
| Paper outline | `writings/paper_draft_sections.md` | ✅ |
| Zeitgeist fit (scan, 500 boots) | `data/analysis/zeitgeist_community_fits.csv` | ✅ Final |
| Time Curves implementation | `src/phase4_timecurves.py` | ✅ Verified (proxy) |
| NST training | UofT cluster, job 159670 | 🔄 Running |
| NST model + embeddings | `data/exported/aps-nst-*.pt/.npy` | ⏳ Pending |
| Time Curves (NST) | `data/analysis/timecurves_nst_*.npz` | ⏳ Pending NST |

### Next session

1. **Download NST results** (after job 159670 email):
   ```bash
   scp comps0:/w/20251/daveed/citation-dynamics/data/exported/aps-nst-model.pt \
       comps0:/w/20251/daveed/citation-dynamics/data/exported/aps-nst-embeddings.npy \
       comps0:/w/20251/daveed/citation-dynamics/data/exported/aps-nst-embeddings-meta.npz \
       citation-dynamics/data/exported/
   ```
2. **Run Time Curves:** `make -f citation-dynamics/Makefile timecurves`
3. **Label communities by physics area** — script to extract top-cited papers per community
4. **Set up SSH keys** to eliminate double password prompt (see header above)

---

## 2026-04-16 (session 20) — Python pipeline confirmed; NST adapter written

- All Python pipeline steps confirmed running: HDF5 (709,803 nodes, 9,833,191 edges, 99.3% year coverage), Leiden full corpus (446 communities, Q=0.7883), Leiden subgraph (90 nodes, 7 communities, Q=0.4291)
- `src/phase3_nst_adapter.py` + `src/phase3_nst_train.py` written and smoke-tested (10 epochs PASSED)
- K17-RGC gold DOI match rate: 2/51 in APS corpus (topology/TDA papers are non-APS — corpus coverage limitation)
- Default NST config: feature_dim=4, space_dim=4, time_dim=4, J_encoder=3 → 53K parameters

---

## 2026-04-16 (session 19) — Python pipeline replaces MATLAB for Phases 1/2/5

- MATLAB blocked: `mat73` can't parse MATLAB string arrays (doi, pubDate → None); scipy.io.loadmat also fails on v7.3 HDF5 mats with strings → **decision: rebuild from CSV/JSON source**
- BlueRed stays MATLAB-only (20+ files, no Python equivalent, not worth porting)
- New scripts: `phase1_build_graph.py` (CSV+JSON→HDF5), `phase5_synthesis_subgraph.py`, `phase2_leiden_cluster.py`

---

## 2026-04-16 (sessions 16–18) — Planning phase; NST demo; synthesis spec

- **Session 18:** NST OGBN-Arxiv demo verified on CPU (Apple Silicon, no CUDA); `deps/nst/REQUIREMENTS.md` created; Phase 5 MATLAB subgraph script written (not run — MATLAB required)
- **Session 17:** K17-RGC gold DOIs extracted (51 non-null from 56 JSON entries); Phase 1/2 MATLAB export scripts written
- **Session 16:** Planner+architect agents returned. Key decisions: HDF5 for MATLAB↔Python handoff; Makefile for pipeline orchestration; Time Curves Python reimplementation design (SMACOF + temporal ordering penalty); `wiki/synthesis-experiment.md` written

---

## 2026-04-15 (session 15) — Wiki restructured; LitDiscover marked complete

- Wiki scope expanded to cross-project; paper-wiki frozen (read-only)
- LitDiscover all three live experiments complete: K17-RGC 100% (56/56), Ge21-HSS 100% (202/202), Le25-GLLM 73.7% (42/57); Q11 citations done; PI review done
- citation-dynamics work pending planner+architect outputs

---

## 2026-04-12–14 (sessions 12–14) — Outer repo; SOTA search; NST decision

- Outer `citation-networks/` git repo initialized; wiki moved from paper-wiki
- SOTA gap search confirmed Zeitgeist hypothesis is still a gap (full results in open-questions.md)
- NST (Choudhary et al., ICLR 2025) identified as key competitor/tool; decision: use NST as representation layer, not competitor
- Novel pipeline decided: Citation DAG → NST → SG-t-SNE → Time Curves
- citation-dynamics/ committed to outer repo (141 files, data excluded)

---

## Sessions 1–11 — archived

Figure redesigns, paper rewrites (Abstract + §§1,2,5,9), LaTeX fixes, project reorganization (thesis→citation-dynamics/, wiki relocated, outer git init).
