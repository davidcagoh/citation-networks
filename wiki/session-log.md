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

> Archived: sessions 24 and earlier (2026-04-17 and before) moved to session-log-archive.md
