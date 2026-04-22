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

## 2026-04-21 (session 25) — LitDiscover: JCDL 2026 submission formatted and filed

### What was done

- **Venue confirmed:** JCDL 2026 (June 30 AoE deadline, Texas, USA). Full paper, ≤10 pages body, ACM sigconf, double-blind.
- **`paper-drafts/jcdl-submission/`** (new folder under `lit-review/robust-literature-discovery/paper-drafts/`):
  - `litdiscover_jcdl.tex` — IEEEtran → ACM sigconf migration (`\documentclass[sigconf,anonymous,review]{acmart}`); abstract moved before `\maketitle`; conflicting packages removed; `\Description{}` added to all 7 figures; `\acmConference` set to JCDL '26 Texas; CCS concept IDs filled in from ACM CCS tool; real author block (incl. ORCID 0009-0009-7241-6906) commented out for camera-ready.
  - `refs.bib` — patched copy: added `address` to Barabasi2016, `publisher`+`address` to Floros2024, `pages`+`publisher`+`address` to Wohlin2014 (pages: 321–330).
- **Figures regenerated at 300 DPI** via `06_publication_figures.py` (was 150 DPI). All 7 pub figures now at 300 DPI, effective rendered DPI ~300–330 at `\linewidth`.
- **Compile result:** 9 pages, 0 errors, 0 undefined references. PDF metadata shows "Anonymous Author(s)" — clean for double-blind. Single cosmetic overfull \hbox (2.5pt in §5) left unfixed.
- **EasyChair submission record created** at https://easychair.org/conferences/?conf=jcdl26.

### Decisions made

- No production-ready system required for paper validity — live Semantic Scholar experiments in §7 are sufficient to demonstrate operational deployment.
- Wohlin2014 pages used as 321–330 (user's best recollection; verify against ACM DL before camera-ready).
- CCS concepts: Information systems~Information retrieval [500], Information systems~Digital libraries and archives [300], Theory of computation~Graph algorithms analysis [100].

### State at end of session

LitDiscover submission is in good shape. PDF compiles clean at 9 pages with all content, figures, and references. EasyChair record filed. Two items needed before final submission: Xiaobai's ORCID, and PI review pass. No in-flight code changes.

### What to do next session

1. **Send PDF to Xiaobai Sun** for PI review — target send by June 8, ask for 1-week turnaround.
2. **Get Xiaobai's ORCID** — add to commented-out `\orcid{TODO-verify-with-PI}` block in the tex.
3. **Verify JCDL 2026 city** — update `\acmConference` once confirmed (user thinks Texas).
4. **Zeitgeist paper** — rewrite §1 + §8 (was next session's priority from session 24; now deferred).

---

## 2026-04-17 (session 24) — Concepts page + src/ refactor (config + utils)

### What was done

- **`wiki/concepts.md`** (new): seeded with Xiaobai Sun's distribution-fitting framework — three complementary metric families (head / middle / tail-sensitive). Relevance notes added for Zeitgeist KS validation and synthesis sub-community fitting. Paper not yet in preprint.
- **`wiki/INDEX.md`** updated: concepts.md added to file table; synthesis-experiment.md marked on-hold.
- **`src/config.py`** (new): single path registry for all pipeline scripts — `DATA_EXPORTED`, `DATA_ANALYSIS`, `DATA_FIGURES`, `DATA_SYNTHESIS`, `APS_H5`, `APS_LEIDEN`, `APS_FITS`, `APS_LABELS`, `APS_GOLD`, `APS_SUBGRAPH`. Scripts import from here rather than repeating `_HERE / ".."` per-file.
- **`src/utils.py`** (new): shared I/O and statistical helpers — `load_h5`, `load_leiden`, `compute_indegree`, `mle_powerlaw_exponent`, `ks_pvalue`. Removes duplication between `phase2b_zeitgeist_fit.py` and `generate_figures.py`.
- **All active scripts updated** to `from config import ...` + `from utils import ...`:
  - `phase1_build_graph.py`, `phase2_leiden_cluster.py`, `phase2b_zeitgeist_fit.py`
  - `generate_figures.py`, `label_communities.py`, `phase5_synthesis_subgraph.py`
- **Archived to `archive/python/`**: `phase3_nst_adapter.py`, `phase3_nst_train.py`, `phase4_timecurves.py`, `load_aps.py` (NST + Time Curves dropped from scope session 22).
- **`Makefile` updated**: `all` now targets `zeitgeist figures` (was pointing at dead `timecurves`); `figures` target added with proper dependencies; `DATA_FIG` variable added; `clean` now covers analysis + figures outputs; NST/timecurves targets removed.

### State at end of session

`src/` is clean — only live pipeline scripts present. Future analysis scripts should `from config import ...` and `from utils import ...` rather than redeclaring paths or power-law math.

### What to do next session

1. **Rewrite §1** — new pitch: Zeitgeist hypothesis → Leiden → per-community power-law → temporal localization. Remove NST/Time Curves framing entirely.
2. **Rewrite §8** — keep: mixture validated, universal γ interpretation, limitations, future. Remove NST/Time Curves.
3. **LaTeX §4 table** — top-10 communities from `community_labels.csv` (n, γ_c, KS p, yr median, IQR, physics label).

---

## 2026-04-17 (session 23) — Community labelling + all §§1–4 figures

### What was done

- **`src/label_communities.py`** (new): ranks nodes by in-degree within each community, prints top-5 DOI+year, writes `data/analysis/community_labels_template.csv`
- **25 communities labelled** from landmark papers — all identifiable from top-cited DOIs:

  | cid | n | Physics area |
  |-----|---|---|
  | 0 | 93k | Condensed Matter — Electronic Structure / DFT |
  | 1 | 62k | Condensed Matter — Magnetism / Disordered Systems |
  | 2 | 56k | Nuclear Physics |
  | 3 | 55k | Particle Physics — Field Theory / QCD |
  | 4 | 53k | Mesoscopic Physics / Quantum Chaos |
  | 5 | 49k | Quantum Information / Computing |
  | 6 | 47k | AMO Physics / Quantum Optics |
  | 7 | 45k | Astrophysics / Gravitational Waves / Cosmology |
  | 8 | 38k | High-Temperature Superconductivity |
  | 9 | 37k | Cold Atoms / BEC / Laser Cooling |
  | 10 | 33k | Particle Physics — Standard Model / HEP |
  | 11 | 27k | Strongly Correlated Electrons |
  | 12 | 24k | Topological Matter / Graphene |
  | 13–24 | <20k | (see community_labels.csv) |

  Saved → `data/analysis/community_labels.csv`. Four uncertain labels: cid 13, 14, 16, 19.

- **`src/generate_figures.py`** (new): generates all four §§1–4 figures in one run
- **Global γ fit** (K_min scan [1,100]): xmin=96, γ_global=2.738 — matches Barabasi (2016) γ=2.79 ✅
- **Fig 1** (in-degree CCDF, γ=2.74, K_min=96) → `data/figures/fig1_indegree_ccdf.pdf`
- **Fig 2** (community size distribution, 446 communities) → `data/figures/fig2_community_sizes.pdf`
- **Fig 3** (γ_c histogram, 25 communities, mean 2.50±0.25) → `data/figures/fig3_gamma_histogram.pdf`
- **Fig 4** (year-median timeline, sorted by median, IQR bars, labelled) → `data/figures/fig4_timeline.pdf`
- **Paper draft** updated: §3 global fit result, §4.3 final results, figures table, TODOs pared to 3 items

### State at end of session

| Artifact | Status |
|---|---|
| `src/label_communities.py` | ✅ |
| `src/generate_figures.py` | ✅ |
| `data/analysis/community_labels.csv` | ✅ (4 labels need verification) |
| `data/figures/fig{1..4}_*.pdf` | ✅ all four generated |
| `writings/paper_draft_sections.md` | ✅ updated; §§5–8 stubs still present |

### What to do next session

1. **Rewrite §1** — new pitch: Zeitgeist hypothesis → Leiden → per-community power-law → temporal localization. Remove NST/Time Curves framing entirely.
2. **Rewrite §8** — keep: mixture validated, universal γ interpretation, limitations, future. Remove NST/Time Curves.
3. **LaTeX §4 table** — top-10 communities from `community_labels.csv` (n, γ_c, KS p, yr median, IQR, physics label).

---

## 2026-04-17 (session 22) — NST fetched; Time Curves + NST dropped; paper scoped to §§1–4

### What was done

- **NST job 159738** completed on RTX A4000; 500 epochs, 500K edges; downloaded all outputs
  - Final loss 0.0532; temporal order_correct=98.1%; embeddings (709,803 × 8)
- **Makefile fixed:** all paths now absolute via `MAKEFILE_DIR`; works correctly from repo root with `-f`
- **Time Curves full run:** stress=0.006452, 8 cusps, 7 loops — results saved but visualisation not useful
- **NST diagnostic figures run:**
  - Spatial PCA: PC1=43%, PC2=25% — communities not clearly separated
  - Temporal vs year: Spearman ρ=−0.668 — weak/ambiguous ordering signal
- **Major scope decision:** §§5 (NST) and §6 (Time Curves) both dropped from paper
- **Paper rescoped to §§1–4 only:** Zeitgeist hypothesis → Leiden → per-community power-law fitting → temporal localization. This is a complete contribution without NST/Time Curves.

### State at end of session

| Artifact | Location | Status |
|---|---|---|
| NST model + embeddings | `data/exported/aps-nst-*.pt/.npy/.npz` | ✅ (archived, not in paper) |
| Time Curves output | `data/analysis/timecurves_nst_{coords,plot}` | ✅ (archived, not in paper) |
| Paper outline | `writings/paper_draft_sections.md` | ⚠️ Still shows §§5–8 — needs rewrite |
| Zeitgeist fits | `data/analysis/zeitgeist_community_fits.csv` | ✅ Final |

### Next session

1. **Community physics labelling** — script: top-5 cited papers per community → hand-label as condensed matter / particle / etc. Unblocks §4 table.
2. **Generate §§1–4 figures** — global degree dist (Fig 1), community size dist (Fig 2), γ_c histogram (Fig 3), year-median timeline (Fig 4)
3. **Rewrite §§1 and 8** — remove all NST/Time Curves framing from intro and discussion

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
