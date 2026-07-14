# Session Log Archive

Older entries moved out of `session-log.md` to keep it to the 5 most recent sessions.
Reverse-chronological, same as the live log.

---

## 2026-07-06 (session 28) — LitDiscover: engine promoted to standalone PyPI package; citation-dynamics split out; watchdog bug fixed

### What was done

- **Repo restructure decided:** `citation-networks` is now a thin umbrella (wiki + pointers only); every paper/engine gets its own repo, matching the existing `lit-review/` sibling-repo pattern rather than mixing tracking models.
- **`citation-dynamics` promoted to its own repo** (`github.com/davidcagoh/citation-dynamics`, private): extracted full history with `git-filter-repo --subdirectory-filter`, pushed, then detached from `citation-networks` tracking (index-only removal, no working-tree files touched — the dirty `nst` submodule and in-progress LaTeX build artifacts survived untouched). Added a fresh `.gitignore` inside the new repo carrying over the rules that used to live in the parent.
- **`automated-lit-reviews-v2` → `litdiscover` (package + repo, both renamed):** internal Python package renamed `litreview2` → `litdiscover` (all imports, CLI entry point, 80 tests still pass), then the GitHub repo itself renamed `davidcagoh/automated-lit-reviews-v2` → `davidcagoh/litdiscover` (auto-redirects old URL) to match. Fixed every cross-reference: local folder rename, this repo's own README, `robust-literature-discovery`'s README links, parent `.gitignore`.
- **Published to PyPI:** added `LICENSE` (MIT), `.env.example`, and full metadata (readme, classifiers, keywords) to `pyproject.toml`; built + `twine check`'d; uploaded — **live at `pypi.org/project/litdiscover/2.0.0/`**. Tagged `v2.0.0`. Verified via clean-venv smoke test (`pip install litdiscover` resolves to the real PyPI package, not a local path artifact).
- **Found and fixed a real production bug while investigating a doc-staleness flag:** the `launchd` job driving `watchdog.py` (`com.litreview2.watchdog`) had a stale absolute path that never matched the repo's actual location — it had been failing silently every 10 minutes (confirmed via `/tmp/litreview_watchdog.log`, wall of repeated `ModuleNotFoundError`/`FileNotFoundError`). Fixed the path in `watchdog.py`/`watch_jepa_pipeline.py`, rebuilt the plist under a renamed label (`com.litdiscover.watchdog`), reloaded — confirmed running clean.
- **Retired `lightroom-pal`** from the watchdog's project rotation — 60+ screening rounds, converged at 0 included / 1000 excluded / 0 pending. Done, no longer worth monitoring.
- **PyPI token hygiene:** user pasted a raw API token into chat mid-session (now in transcript) — flagged it as exposed, wired `~/.pypirc` from `.env` without ever printing the value, and the user rotated the token afterward (old one now dead; `~/.pypirc` refreshed with the new one).
- **README fix:** Quick Start step 2 implied a Supabase project + `schema.sql` were just sitting there ready; neither is true for a fresh `pip install` — made explicit that a Supabase project must be created first and `schema.sql` isn't bundled in the pip package.
- **Explicit decision: `robust-literature-discovery` stays as-is** — not renamed, not merged with `litdiscover`. It's named after the paper (correct academic-repo convention), and merging would collapse a public/frozen benchmark repo into a private/continuously-evolving production engine.

### State at end of session

`litdiscover` v2.0.0 is live on PyPI and installable by anyone (`pip install litdiscover`) — this closes the "make LitDiscover available for seamless use" goal from earlier in the session. `citation-dynamics` is now independently versioned. Watchdog is running clean again after an unknown period of silent failure.

### What to do next session

1. No blocking action on `litdiscover` distribution — future releases are just bump version → `python -m build` → `twine upload dist/*`.
2. Consider whether `watchdog.py`'s failure window means any of the 3 rotation projects (`self-supervised-pretraining`, `automated-lit-review-methodology`) silently stalled for a while — worth a status check.
3. Continue Zeitgeist/citation-dynamics work in its new standalone repo location.

---

## 2026-07-06 (session 27) — LitDiscover: venue odyssey ends in IP&M submission; repo reorg + cleanup

### What was done

- **Venue hunt (one day, four venues):** JCDL 2026 deadline (June 30) confirmed missed and never submitted → reformatted for **JASIST** → switched to **ACM TOIS** (best documented acceptance/turnaround stats: 24% acceptance, ~2mo/round) → **TOIS abandoned** after discovering its ~20-page minimum (excl. refs) on the actual ScholarOne form; paper is a focused 12pp contribution, not worth padding → final target: **Information Processing & Management (IP&M)**, chosen on genuine content fit (spans system-level + human-centered research, matching an algorithm-with-empirical-validation paper) rather than stats alone.
- **IP&M reformat:** `paper-drafts/ipm-submission/litdiscover_ipm.tex` — `elsarticle` class, `authoryear` option (critical gotcha: omitting it silently renders numeric `[1]` citations even with `\citet`/`\citep` in source; only caught by checking rendered PDF text, not compile success), `elsarticle-harv` bibstyle (verified IP&M's actual Guide for Authors specifies APA author-date, not the commonly-assumed Vancouver numbered style). Added required CRediT authorship statement + GenAI-use declaration before references.
- **Submission-portal surprises handled:** IP&M turned out to require **anonymized peer review** with 4 separate files, not one PDF — built `litdiscover_ipm_anonymous.tex/.pdf` (author block + CRediT name stripped, verified via text-search on rendered PDF that nothing leaks), `title_page.md/.pdf`, `highlights.md/.pdf` (5 bullets, all under Elsevier's 85-char limit), and `cover_letter.md/.pdf` (dropped ACM-specific double-blind language, added CRediT + GenAI disclosure per IP&M's actual cover-letter instructions).
- **Xiaobai Sun dropped as co-author** on LitDiscover specifically (no contribution to this paper; her work still cited). She remains co-author on the separate Zeitgeist/citation-dynamics paper — a genuinely joint effort, not conflated.
- **Repo reorg (`lit-review/robust-literature-discovery/`):** archived all dead-end submission attempts (`jcdl-submission/`, `jasist-submission/`, `tois-submission/`) under `paper-drafts/archive/`, so `paper-drafts/` root only ever shows one active LaTeX target. Fixed `.gitignore`'s LaTeX-artifact patterns to be recursive (`paper-drafts/**/*.ext`) — the old patterns only matched the root, which had let `jcdl-submission`'s build artifacts get accidentally committed; untracked those via `git rm --cached`.
- **Broader cleanup:** removed `data-aps/sample/*.mat` (2 orphaned MATLAB relics, referenced only by a script itself archived in the sibling `citation-dynamics` repo), the empty `data-aps/raw/` placeholder, empty `out/` build dirs, a stray unrelated `paper-drafts/.claude/settings.local.json`, and purged the 1.2GB `data-live/cache/papers/` (gitignored, regenerable). Committed the long-pending `paper-wiki/` deletion (confirmed with user: `wiki/` at the outer `citation-networks/` level is canonical since the 2026-04-17 restructure).
- **README overhaul:** added a full directory-structure walkthrough (explains why `data-aps/` and `data-live/` are kept as separate top-level dirs rather than nested under one `data/` — genuinely different data lifecycles) and a License section.
- **Added `LICENSE` (MIT)** — repo is now the public data-availability link referenced in the IP&M submission, so it needed an explicit reuse license.
- **Fixed 3 dead links** in README pointing to the private `automated-lit-reviews-v2` repo (annotated "(private repository)" rather than removing, per user preference) — confirmed via GitHub API (`"private": false`/`404`) which repo was actually public before making any claims.
- **Caught and fixed a real risk:** local repo was 5 commits ahead of `origin/master` — meaning the just-submitted IP&M paper's data-availability link would have pointed reviewers at a stale, pre-reorg repo state. Pushed immediately once caught.
- **Submitted to IP&M** via Elsevier's Editorial Manager (new submission experience, `submit.elsevier.com`), with the repo linked as "Original data."

### State at end of session

LitDiscover is **submitted** to Information Processing & Management. Repo is pushed and in sync with exactly what reviewers can see if they follow the data-availability link. No known open issues.

### What to do next session

1. **No action needed on LitDiscover** until IP&M responds — typical first-decision turnaround ~5–6 months per available (small-sample) data.
2. If a revision is requested, note the portal said LaTeX source isn't needed until revision stage — will need to upload `.tex`/`.bib`/figures at that point, not just PDFs.
3. Continue Zeitgeist/citation-dynamics work (see session 26 below) — unaffected by today's LitDiscover work.

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

---

## 2026-04-17 (session 23) — Community labelling + all §§1–4 figures

- **`src/label_communities.py`** (new): ranks nodes by in-degree within each community, prints top-5 DOI+year, writes `data/analysis/community_labels_template.csv`
- **25 communities labelled** from landmark papers, saved → `data/analysis/community_labels.csv`. Four uncertain labels: cid 13, 14, 16, 19.
- **`src/generate_figures.py`** (new): generates all four §§1–4 figures in one run
- **Global γ fit** (K_min scan [1,100]): xmin=96, γ_global=2.738 — matches Barabasi (2016) γ=2.79 ✅
- Fig 1 (in-degree CCDF), Fig 2 (community sizes, 446 communities), Fig 3 (γ_c histogram, mean 2.50±0.25), Fig 4 (year-median timeline) all generated to `data/figures/`
- Paper draft updated: §3 global fit result, §4.3 final results, figures table, TODOs pared to 3 items

Next at the time: rewrite §1/§8 to drop NST/Time Curves framing, add LaTeX §4 top-10 communities table.

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

### What to do next session (superseded by later sessions)

1. Send PDF to Xiaobai Sun for PI review.
2. Get Xiaobai's ORCID.
3. Verify JCDL 2026 city.
4. Zeitgeist paper — rewrite §1 + §8.

---

## 2026-04-29 (session 26) — Zeitgeist: first full LaTeX draft compiled (10 pages, LNCS)

### What was done

- **Authorship clarified:** LitDiscover = David solo; Zeitgeist = joint with Xiaobai. Updated memory accordingly.
- **LitDiscover tabled:** Xiaobai is MIA. Submission on hold (need her ORCID + PI review). Open questions remain: arXiv upload timing, whether to build a user-facing v2 before going public, authorship decision.
- **`citation-dynamics/writings/zeitgeist_paper.tex`** (new): Full 10-page LNCS paper written from scratch. Sections:
  - §1 Introduction — Zeitgeist hypothesis, mixture model Eq. (1), two testable predictions
  - §2 Related Work — scale-free models, temporal communities, mixture models, gap statement
  - §3 Dataset — N=709,803, L=9,833,191, γ_global=2.74, Pareto stats
  - §4 The Zeitgeist Hypothesis — 4.1 formal statement, 4.2 Leiden (446 communities, Q=0.7883), 4.3 per-community fitting (25/25 KS pass, γ_c ∈ [2.099, 3.268]), 4.4 temporal localization (68% IQR < 20y), top-10 table
  - §5 Discussion — exponent variation interpretation, temporal localization as research generation signature, limitations, future work
- **`citation-dynamics/writings/zeitgeist_refs.bib`** (new): 13-entry bibliography (Barabasi, Clauset, Traag, Ke2023, Aparicio, CostaFrigori, CastilloCastillo, Choudhary, Price×2, Redner, Newman, Waltman, Blondel).
- **Compiled:** `pdflatex` + `bibtex` + 2× `pdflatex` → clean PDF, 0 errors, 10 pages.
  - PDF: `citation-dynamics/writings/zeitgeist_paper.pdf`

### State at end of session

PDF compiled and handed to user for review. No in-flight code changes. Two untracked utility scripts (`forward_cites.py`, `verify_refs.py`) remain uncommitted at repo root.

### What to do next session

1. **Review PDF** — user is checking it; address any content or formatting feedback
2. **Verify bibliography entries** — Aparicio2024, CostaFrigori2024, CastilloCastillo2025 were written from memory; cross-check exact venues/page numbers before submission
3. **LitDiscover roadmap** — decide: (a) arXiv now vs. wait for v2 demo; (b) Xiaobai co-author vs. acknowledgement (requires her agreement); (c) whether to build a wrapper/dashboard for public-facing v2
4. **Commit `forward_cites.py` + `verify_refs.py`** if they're keepers

---

## 2026-07-07 (session 29) — LitDiscover: fixed embedding-model naming bug; added per-stage vetting artifacts + forward-cites/verify commands; IP&M desk-rejected

### What was done

- **User ran litdiscover for real and hit a spend cap.** Root-caused via the run's own cost-breakdown trace: the dominant cost was genuinely the extraction step (full-paper text to `gemini-2.5-flash`, not abstracts), but two embedding calls were also silently 404ing on every attempt — a real bug, though it cost nothing since the calls errored before Gemini processed anything.
- **Fixed the embedding-model naming bug (2 sites):** `litdiscover/screen/llm.py::_get_embedding()` defaulted to `"text-embedding-3-small"` (an OpenAI model name) sent through a client actually pointed at Gemini's OpenAI-compat endpoint; `litdiscover/extract/synthesizer.py::_embed_papers()` defaulted to `"models/gemini-embedding-001"` — the `models/` prefix belongs to the native Gemini SDK, not the OpenAI-compat endpoint (which the working chat calls already call bare, e.g. `"gemini-2.5-flash"`). Both now use bare `"gemini-embedding-001"`. All 30 affected tests still pass.
- **Investigated Mistral OCR (from the unrelated `khanacademy-for-any-course-v2` repo) as a possible cheaper extraction path — ruled out.** That repo's Mistral usage is pure image-to-text OCR on scanned PDFs with zero structured-field extraction; litdiscover already works from clean extracted text, so there's nothing to port. Real levers for extraction cost stay: truncate further, cheaper Gemini tier, or batch multiple papers per call — not acted on this session.
- **Designed and implemented reviewable per-stage artifacts + absorbed two standalone scripts into litdiscover**, via a full plan-mode design pass (plan saved at `~/.claude-main/plans/elegant-inventing-scroll.md`). Rationale: the pipeline (`init`→`run`→`extract`→`synthesize`) was already stage-able (separate CLI commands, DB-persisted state) but nothing produced something to actually *look at* between stages before spending more money on the next one.
  - **Traversal stage (`run`) now writes `<slug>_graph.h5` + `<slug>_papers.json`** instead of a markdown table (markdown was explicitly rejected — nobody reads a linear table of hundreds of papers; the real use case is querying/filtering). The `.h5` format matches the existing convention in `citation-dynamics/src/phase1_build_graph.py` (COO edge list, index-aligned per-node arrays) so it stays compatible with `phase2_leiden_cluster.py`-style tooling. Node scope is **every paper row regardless of status** (not just included) — `edges` FK-references `papers.id` directly, so pre-filtering by status would silently drop real graph structure. An `included` 0/1 vector lets you derive the induced included-only subgraph via `diag(v) @ A @ diag(v)` without needing a separate filtered export.
  - **Extraction stage (`extract`) now writes `<slug>_extraction_report.md`** — this one stayed markdown since it's a genuine linear-read use case (skim for extraction quality before spending on synthesis), flagging `⚠ MISSING EXTRACTION` for included papers with no usable extraction.
  - **Ported `forward_cites.py` and `verify_refs.py`** (previously untracked standalone scripts operating on an exported `.bib` with their own from-scratch S2 client) into `litdiscover/intake/forward_cites.py` and `litdiscover/intake/verify.py` — new `forward-cites`/`verify` CLI commands operating directly on a project's own `papers`/`edges` tables, reusing existing S2 client code (`paginate_edges`, shared rate-limit/retry) instead of re-implementing it. `forward-cites` is report-only by default (what's citing the included set, that traversal's hub-filter/yield-gate might have missed); `--ingest` optionally adds findings to the pending queue. `verify` re-resolves included papers against S2 and flags title drift (VERIFIED/UNCERTAIN/NOT_FOUND) — a read-only diagnostic, never auto-corrects.
  - Added `db/client.py::get_all_papers()`/`get_edges()` (paginated via `.range()`, unlike some existing unpaginated helpers — correctness of a full graph export matters more than a screening-batch helper silently truncating at 1000 rows). Added `h5py` to `pyproject.toml`. New test files `test_reports.py`/`test_forward_cites.py`/`test_verify.py` (13 new tests, including a matrix-mult induced-subgraph check and an order-preservation regression guard for `verify`). Full suite: **97 passed**. Updated `CLAUDE.md` with the new command list and a "Recommended Vetting Workflow" section.
  - Explicitly **out of scope this session:** citation-network-aware synthesis clustering (separate design conversation — see Next below), and deleting the two now-ported root-level scripts (left for the user once verified working).
- **`robust-literature-discovery` (LitDiscover paper) was desk-rejected by IP&M** after the session-27/28 submission: "not suitable for a full review... several existing publications in IP&M and/or other outlets address this stage of research... leverage state-of-the-art baselines and research, especially LLMs... reference the most updated articles from the current year, which you have not done." Reads as a scoping/currency problem (traversal set too shallow/dated), not a fundamental-idea problem.

### State at end of session

Embedding bug fixed and tested but **not yet re-published to PyPI** (current `litdiscover` v2.0.0 on PyPI still has the bug). New vetting-artifact commands and forward-cites/verify are implemented and unit-tested but **not yet smoke-tested against a live Supabase project** — the plan's manual verification step (run against `lightroom-pal`) was left for the user to trigger, since it touches real project state.

### What to do next session

1. **Bump and republish `litdiscover` to PyPI** (v2.0.1) with today's fixes before using the engine for the redo run below — resubmitting IP&M reviewers to an engine that's already known to work correctly.
2. **Redo the `robust-literature-discovery`/LitDiscover paper's underlying lit-review run** to address the IP&M rejection — needs SOTA/LLM-focused baselines and current-year references specifically; consider whether this should also incorporate item 3 or ship first and layer that in.
3. **Citation-network-aware synthesis** — now that the traversal stage exports a real citation graph (`.h5` with COO edges + included vector), design Pass 1 clustering to use graph structure (citation adjacency, not just embedding similarity) instead of embedding-only k-means. Connects to the untested `concept_citation_motifs.md` idea (seminal hub / parallel discovery / context transplantation motifs) — worth revisiting whether motif detection belongs in this redesign.
4. Manually smoke-test `forward-cites`/`verify`/the graph export against a real (low-stakes) project before relying on them for a paid run.

---

## 2026-07-08 (session 30) — Wiki: next-step brainstorm captured, new research-program overview written

**2-tier exp:** Explored strengtheners for LitDiscover (traversal visualization) and Zeitgeist (Hierarchical Dirichlet Process for soft community resolution) plus two speculative future directions (4th citation motif: coupled fields; HDP as its detection method); wrote `wiki/concepts.md` entries for all three and a new `wiki/research-program.md` narrative overview for sharing with a potential collaborator.

<details>

- **Reviewed current wiki state** for the user (project status recap): LitDiscover desk-rejected by IP&M, needs SOTA/LLM-era lit review redo; Zeitgeist first draft compiled, under review; Synthesis on hold, unimplemented.
- **Brainstormed next-step directions**, prompted by the user citing the new LitDiscover graph export (`<slug>_graph.h5` + `<slug>_papers.json`, full visited-node scope + `included` vector) and referencing the Hierarchical Dirichlet Process paper (Teh, Jordan, Beal & Blei 2006) as a way to resolve the "what is a field" problem that hard partitions (Leiden/BlueRed) can't answer.
- **Ran a real analysis on request:** pulled the 25 per-community γ_c values from `citation-dynamics/data/analysis/zeitgeist_community_fits.csv` and ran Shapiro-Wilk — W=0.919, p=0.047 (borderline reject normality at n=25), skew=1.18 (right-skewed), excess kurtosis=1.78. Not currently reflected in the paper; flagged as a possible small addition, not committed.
- **Updated `wiki/concepts.md`:** added motif #4 (coupled fields — e.g. AI-agent memory systems ↔ benchmarks like LoCoMo) to the existing Citation Motifs entry; added new "Hierarchical Dirichlet Process for Field Resolution" entry; added new "Traversal-Native Visualization" entry covering round-by-round animation and reuse of the already-specced (but archived-as-out-of-scope) Time Curves pipeline at Synthesis scale instead of full-corpus scale.
- **Wrote `wiki/research-program.md`** (new file, linked from `INDEX.md`): a plain-language, collaborator-facing narrative of the three pipeline stages (LitDiscover → Zeitgeist → Synthesis) with status + strengthener for each, plus the two speculative extensions and how they connect. Rewrote once already after user feedback — first draft used self-referential meta-language ("one-paragraph pitch") inappropriate for something that might be sent externally; second draft is plainer and adds ASCII pipeline schematics.
- **Clarified with user:** Synthesis (not previously named by the user) is the connective tissue where the LitDiscover and Zeitgeist strengtheners actually combine, not a fourth separate idea.

</details>

---

## 2026-07-09 (session 31) — LitDiscover: engine reworked to staged-by-default workflow; redo run against automated-lit-review-methodology to address IP&M rejection

**2-tier exp:** Shipped a full staged/autopilot rework of the litdiscover engine (TDD, 8 commits, 174 tests) with two real bugs found and fixed via live use, then used the new staged workflow to redo the underlying lit-review corpus behind the desk-rejected LitDiscover paper — added 8 SOTA/current-year seeds, ran traverse+prefilter, and hand-marked 698 candidates (366 included / 344 excluded) to directly address IP&M's "missing SOTA/LLM baselines, missing current-year articles" rejection reason.

<details>

- **Design discussion → plan → implementation.** User wanted litdiscover's `run` to stop auto-chaining traverse→screen unsupervised (root cause of a prior Gemini-spend-cap incident) and replace automated LLM screening with a human+agent eyeball pass over a cheap keyword-prefiltered shortlist, plus a new `related-work-mine` step to study how closest-match papers frame their own prior work. Hashed out design points one at a time (mode default, staged-run semantics, criteria-refinement gating, audit trail) before handing to a `planner` agent, which produced a 7-phase plan; corrected one design point mid-plan (staged `run` = traversal-only, never auto-screens — planner's first draft assumed a full expand+screen cycle).
- **Implemented via `tdd-guide` agent in an isolated worktree**, merged fast-forward into `litdiscover` main (8 commits): `[loop] mode = "staged"` (new default) vs `"autopilot"` (opt-in, byte-for-bit unchanged old behavior, guarded by characterization tests); new `traverse`/`screen`/`prefilter`/`mark`/`related-work-mine` CLI commands; `screening_log` gained `screener_type`/`note`/`mode` columns (migration applied directly to the live `litreview-v2` Supabase project); `watchdog.py` and its launchd job removed (host-side plist teardown still needed manually). 171→174 tests passing; new code 96-100% covered.
- **Smoke-tested for real** by using it to redo `automated-lit-review-methodology` — the project whose lit-review run underlies the desk-rejected LitDiscover paper (IP&M: "several existing publications address this stage of research... leverage SOTA baselines, especially LLMs... reference the most updated articles from the current year, which you have not done"). Full reset (38k stale papers deleted via batched raw SQL — PostgREST's bulk-delete timed out at that scale), then re-seeded with the original 5 + 5 fresh 2025-2026 anchors (AISysRev, LLM4SCREENLIT, DeepSurvey-Bench, etc.) found via web search.
- **`related-work-mine` surfaced 3 more direct SOTA competitors** (AutoSurvey, ChatCite, LitLLM) from one seed's own Related Work section — added as seeds too. Confirmed Gemini's monthly spend cap is exhausted (blocks embedding-based ranking and will block `extract`/`synthesize` later) but doesn't block `traverse` (S2/PDF-only).
- **Found and fixed two real bugs surfaced by this live run** (both committed, both got regression tests): (1) `relwork.py`'s section-heading regex matched "Background"/"Related Work" as a substring anywhere in the PDF text, including mid-prose mentions — caused a real mis-extraction; fixed by requiring the heading alone on its own line, preferring explicit Related/Prior Work over bare Background. (2) `prefilter.py`'s `derive_terms` tokenized the *entire* criteria string including Exclude bullets and boilerplate framing prose, pulling in generic words ("paper", "meets", "must") that matched 94% of candidates — fixed by scoping term derivation to Include-bullet content only, and fixing heading detection (was requiring an exact "Include:" label, silently produced zero terms against real prose-style criteria).
- **Manually eyeballed all 698 prefiltered candidates together** (traverse: 844 pending → prefilter: 698 survivors), batch by batch, applying one consistent litmus test: include if the paper's *contribution* is proposing/evaluating a review-automation method (screening, extraction, stopping, generation) regardless of domain; exclude domain-specific SRs where AI/LLM use is incidental. Caught one real transcription error mid-`mark` (a paper I'd told the user was included got left out of the compiled list) by cross-checking counts before writing — fixed before it landed in the DB.
- **Applied via a one-off Python script** (`apply_mark.py` in scratchpad, not committed) calling `litdiscover mark` in chunks rather than retyping ~700 IDs by hand. Final state: 366 included, 344 excluded, 147 still pending (non-prefilter-survivors, untouched by design).

</details>

---

## 2026-07-10 (session 32) — LitDiscover: launchd teardown closed; 366 included papers mined for close-hit competitors; wiki/litdiscover consolidated 8→4 files

**2-tier exp:** Closed out session 31's last open item (watchdog launchd teardown), pulled and analyzed the 366 `included` papers from the IP&M-redo corpus to identify close-hit competing systems for the paper's Related Work section, then restructured `wiki/litdiscover/` from 8 files down to 4 to stop report-accumulation.

<details>

- **Launchd teardown completed:** `com.litdiscover.watchdog` was still loaded and failing every cycle (exit status 2, as expected post-code-removal). Unloaded via `launchctl unload`, deleted the plist (`~/Library/LaunchAgents/com.litdiscover.watchdog.plist`) and the stale `/tmp/litreview_watchdog.log`. Closes the last item from session 31.
- **Pulled all 366 `included` papers** from `automated-lit-review-methodology` (Supabase project `litreview-v2`, id `xudngzdyzxbchpjbvvvd`) via `execute_sql`, saved to `wiki/litdiscover/included_366_2026-07-09.csv`. Noted in passing: Supabase advisor flags RLS disabled on all 6 tables in this project (anon key has full read/write) — not fixed, flagged to user for a later decision.
- **Identified close-hit competitors** — keyword-filtered 237 of 366 as review/screening-automation-adjacent, then narrowed to 15 genuine architectural competitors (systems that discover/filter/synthesize literature end-to-end, not just screening-assist plugins). Pulled full abstracts for all 15 via a second `execute_sql` query.
- **Built a tiered comparison table** (`wiki/litdiscover/related-work-landscape.md`, motivation/scope/architecture/evaluation columns): Tier 1 canonical lineage (SciReviewGen → AutoSurvey → LitLLM → LitLLMs-are-we-there-yet → LiRA, which already cite each other), Tier 2 nearest architectural neighbors deserving real compare/contrast (ProfOlaf — human-in-the-loop snowballing; Human-Centred Research Automation — near-identical "discovery/filtering/gap-identification" framing), Tier 3 one-line-mention sufficient (6 papers), and 2 excluded false positives (Autonomous Knowledge Pipeline, Vakya — different tasks entirely, keyword-match noise).
- **Flagged two paper-relevant findings**: LitLLMs-are-we-there-yet introduces a rolling contamination-free eval protocol specifically to avoid staleness — worth addressing head-on if LitDiscover's APS-simulation validation could face a similar critique; SGSimEval is an eval benchmark, not a competing system, better cited for methodology than lumped into the competitor list.
- **Wiki restructure, user-initiated** ("I don't want to keep generating reports and analyses that accumulate and go stale"): read all 8 `wiki/litdiscover/` files, found 4 were frozen since ~Apr 2026 (pre-IP&M-rejection paper-draft state) and one (`n-rounds-extension.md`) was fully duplicated by a table already in `decisions.md`. Consolidated: `thesis.md` + `simulation-vs-production.md` + `argument-map.md` + `figure-roles.md` → merged into one read-once `background.md`, explicitly marked stale-relative-to-redo; `n-rounds-extension.md` deleted (pure duplicate); `close-hits-comparison.md` renamed to `related-work-landscape.md` and marked as a living document to update in place rather than a one-off report. Net: 8 files → 4 (`background.md` read-once, `decisions.md`/`open-questions.md`/`related-work-landscape.md` live). `wiki/INDEX.md`'s LitDiscover table updated to match. Committed locally (`24e2f4d`), not pushed.

</details>

**Next:** Decide whether to pull full PDFs for Tier 1+2 (7 papers) vs. working from abstracts only for the redo's Related Work section. Continue the LitDiscover redo — run `traverse` again on the enlarged included set once ready, check/raise the Gemini spend cap before `extract`/`synthesize`. Consider whether to enable RLS on the `litreview-v2` Supabase project (flagged, not yet decided). `forward_cites.py`/`verify_refs.py` at repo root confirmed as intentional scratch copies (user: "probably copied it out to paste into other projects") — not part of this project's tracked code, safe to ignore/leave untracked.

---

## 2026-07-10 (session 33) — LitDiscover: 15-paper related-work comparison table built; robust-literature-discovery repo fully restructured into closed-corpus-eval/live-survey-eval tracks

**2-tier exp:** Built a tiered motivation/scope/architecture/evaluation comparison table for the 15 genuine close-hit competitors identified in session 32's 366-paper sweep, then — at the user's repeated prompting to reconsider the shape, not just rename directories — restructured `robust-literature-discovery` end to end: deleted `inbox-papers/`, split into two self-contained `closed-corpus-eval/`/`live-survey-eval/` tracks (verified via full read of all 12 pipeline scripts that there's zero cross-track coupling), and further split `closed-corpus-eval/scripts/` into `eval/` (produces every paper-claimed number) vs `sweep/` (parameter-justification only, two scripts dead/superseded).

<details>

- **Built `wiki/litdiscover/related-work-landscape.md`'s comparison table** — pulled full abstracts for all 15 Tier 1/2 close-hit papers via Supabase `execute_sql`, tiered them: Tier 1 canonical lineage (SciReviewGen → AutoSurvey → LitLLM → LitLLMs-are-we-there-yet → LiRA, which already cite each other), Tier 2 nearest architectural neighbors deserving real compare/contrast (ProfOlaf — human-in-the-loop snowballing; Human-Centred Research Automation — near-identical "discovery/filtering/gap-identification" framing), Tier 3 one-line-mention (6 papers), 2 excluded false positives. Flagged two paper-relevant findings: LitLLMs' rolling contamination-free eval protocol as a potential preemptive rebuttal to an APS-staleness critique, and SGSimEval as an eval-methodology citation rather than a competitor.
- **Pushed session 32's litdiscover housekeeping commits** (launchd teardown, wiki consolidation) and this session's close-hits-comparison commit to `github.com/davidcagoh/litdiscover` and `github.com/davidcagoh/robust-literature-discovery`.
- **`robust-literature-discovery` full restructure**, done interactively in three passes as the user kept sharpening the target shape:
  1. First pass: deleted `inbox-papers/` (judged redundant with the wiki's now-systematic related-work sweep) and `app-validation-data/` (orphaned output of an already-dead script), renamed `analysis-scripts/`→`scripts/`, `paper-drafts/`→`drafts/`, `data-aps/`→`eval/aps-closed-corpus/`, `data-live/`→`eval/live-survey-eval/`.
  2. User caught that this grouped by "kind of file" rather than real coupling ("now i realize that scripts/ itself is just all eval scripts right??"). Read all 12 pipeline scripts in full end to end to verify: scripts 01–08 (+03b) touch only APS closed-corpus data, `09_live_validation.py` touches only live data, zero cross-references. Restructured into two self-contained tracks — `closed-corpus-eval/` and `live-survey-eval/`, each owning both its own `scripts/` and `data/` — eliminating the artificial shared top-level `scripts/`.
  3. User caught a second distinction: several "eval" scripts are actually hyperparameter-justification/planning, not the paper's actual validation. Classified all 11 closed-corpus scripts by function and split `closed-corpus-eval/scripts/` into `eval/` (01, 02, 03, 04b, 05, 06 — produces every paper-claimed number/figure) and `sweep/` (03b, 04, 07_elbow, 07_rounds, 08 — parameter-justification only; `04` is superseded by `04b`, `07_elbow` is currently inoperable per its own prior documentation).
  - Fixed the `processed/` symlink's relative depth twice (once per directory-depth change), verified resolution each time. Updated path constants in all 12 Python scripts (`_REPO = Path(__file__).parent.parent[.parent]`), 6 `.tex` `\graphicspath` directives, `.gitignore`, `README.md`, `CLAUDE.md`, and `closed-corpus-eval/scripts/README.md`. Verified every script still parses and every referenced path exists on disk before each commit.
  - Explicit decision, discussed and declined: **not** copying `wiki/litdiscover/included_366_2026-07-09.csv` into a `related-work/` subdir under `rld/` — the wiki's `related-work-landscape.md` is the living, continuously-updated research artifact; `rld/drafts/refs.bib`/`bibliography.json` is the frozen, paper-authoritative citation record. Duplicating the CSV would create a second copy that drifts stale.
  - Committed in two commits (`46aaa75` restructure, includes the eval/sweep split as a follow-up within the same commit) and pushed.

</details>

**Next:** Decide whether to pull full PDFs for related-work-landscape.md's Tier 1+2 (7 papers) vs. working from abstracts only for the IP&M redo. Continue the LitDiscover redo — run `traverse` again on the enlarged included set, check/raise the Gemini spend cap before `extract`/`synthesize`. RLS-disabled flag on `litreview-v2` Supabase project still open, not yet decided.
