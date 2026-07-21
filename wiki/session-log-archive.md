# Session Log Archive

Older entries moved out of `session-log.md` to keep it to the 5 most recent sessions.
Reverse-chronological, same as the live log.

---

## 2026-07-14 (session 38, LitDiscover) — Experiment 1 (discovery-operator benchmark) actually run live for the first time; co-citation confirmed as the standout operator; composition/chaining attempt failed and was diagnosed; precision tracking added; a fairness gap in the original 73-100% recall headline was found; Experiment 1 paused

**2-tier exp:** Ran `phase-discovery-roadmap.md`'s Experiment 1 (baselines/marginal/ablation) live against all 3 surveys for the first time — co-citation is the one non-traversal operator with real signal (best precision, real ablation drop everywhere), while embedding/venue/recency show ~0% recall and precision on every survey and every run; a subsequent chained-composition attempt made both metrics *worse* (root-caused: unfiltered forward traversal + citation-count frontier ranking → noisy corpus → generic hub papers), and checking precision for the first time on the *original* system's own 73-100% recall validation revealed it implies 0.03-0.45% precision (unscreened graph reachability) — likely relevant to how the IP&M submission frames its headline claim, independent of anything else this session found. Experiment 1 is now marked paused (not abandoned) in the wiki, with a redesign path (budget-normalized comparison, §4.7) scoped for a future session.

<details>

- Built `10_operator_benchmark.py`, `11_redundancy_check.py`, `12_chained_composition.py` in `live-survey-eval/scripts/` — reuse the real production operators (`litdiscover.discovery.operators`/`traverse.py`) and existing gold-sets/seeds, not a reimplementation.
- §4.3 baselines + §4.4 marginal contribution + §4.5 ablation run live against K17-RGC/Ge21-HSS/Le25-GLLM. Co-citation: best precision of anything that fires (10-29%), only operator with a nonzero ablation drop on every survey. Embedding/venue/recency: ~0% new gold, ~0% precision, every survey, every experiment — reproducible negative result.
- §4.6 redundancy pre-check: co-citation vs. 2-round forward traversal — near-zero candidate/gold overlap (not redundant); naive multi-round forward traversal is itself low-ROI (5-12x more candidates than co-citation for less gold).
- Root-caused (via actual web research on S2's docs, not guessing) a 429 pattern: standard S2 API key is 1 req/sec flat across *all* endpoints, not a separate stricter budget for author/recommendations. Fixed `s2_client._s2_wait()`'s margin (1.05s→1.2s) and added tenacity retry-with-backoff to `operators.py`'s four raw calls (previously unprotected, unlike `s2_client.py`'s own `_fetch_edges`). Added a shared `log_retry_attempt()` trace callback so retries are visible live, not silent — also fixed `PYTHONUNBUFFERED` omission that made scripts look hung when they weren't.
- Added precision tracking (`new_gold/candidates`) — never measured before, for these operators or for the original system's own historical recall claims. Full-union precision across the 3 surveys: 0.3-4.7%. Retroactively checked `09_live_validation.py`'s saved multi-round output: implies 0.03-0.45% precision for the 73-100%-recall headline (that eval explicitly never screens).
- Composition experiment (chained execution vs. independent union, H0/H1 framed): the one survey that completed (Ge21-HSS) showed chaining made both recall (12.0%→7.5%) and precision (4.7%→1.1%) worse. Diagnosed cause: unfiltered `forward_traversal_operator` (no Pareto hub filter in the chain) exploded the corpus past 1,000 papers, then ranking by raw `citation_count` for frontier selection handed downstream operators generic mega-cited papers (queried venues included *Science*, *Physical Review Letters* for a human-social-sensing survey) instead of relevant ones.
- This also exposed a fairness problem across the whole day's design: every operator-benchmark experiment gives citation traversal exactly one hop, but the original system's validated recall comes from a multi-round loop — comparing raw recall between the two conflates two different things. The fix (budget-normalized comparison, not raw recall) was already scoped in §4.7 from the start but never built.
- Recovered from a real mid-session incident: a concurrent session (also active in this repo, fixing gold-set data quality) clobbered part of `phase-discovery-roadmap.md` §4.5/§4.6 via a lost-update race (git showed only insertions vs. the last commit, but content added earlier in *this* session had reverted). Reconstructed the lost sections from this conversation's own history rather than re-deriving them.
- Decision: paused Experiment 1 in the wiki (⏸ banner + executive summary at the top of §4) rather than deleting or continuing to patch — real findings preserved, redesign path named, §1-3 (original system docs, prior-art survey) untouched.

</details>

**Next:** if Experiment 1 resumes, build the budget-normalized (recall-per-candidate) comparison scoped in §4.7 before running anything else live — every raw-recall comparison attempted this session turned out to need it. Otherwise, next real blocker across the project is still `synthesize`'s citation-grounding check never having been run against a real project (unchanged, several sessions old).

---

## 2026-07-13 (session 35, LitDiscover) — Related-work lineage audited and found unreliable; two rigorous alternative methods built; paper's Related Work paragraph rewritten from the richer of the two

**2-tier exp:** Caught that `related-work-lineage.md`'s thematic-bucket lineage was constructed by clustering, not citation-tracing — audited it against the source deep-dives and found only 12 of 32 real citation edges represented, plus 3 fabricated edges (including the load-bearing SciReviewGen→AutoSurvey anchor); built two independent, more rigorous lineage-construction methods (O(n) explicit-citation extraction, O(n²) implicit pairwise content-matching) to replace it, discovered the field's real structure is one 19–21-paper connected component rather than six lineages, rewrote `related-work.tex`'s Related Work paragraph directly from the richest method, and fixed two real citation errors (a fabricated DOI, a wrong paper) caught along the way.

<details>

- **Diagram readability fix, first.** The session opened with `related-work-lineage.md`'s single 22-node Mermaid diagram being unreadable; split it into per-lineage diagrams plus a `subgraph`-clustered big-picture view — a real UX fix, but this is what led to noticing Lineage E's chain notation implied false adjacency between papers that don't actually cite each other.
- **User's suspicion confirmed with hard evidence:** dispatched a subagent to extract every explicit in-set citation from all 27 deep-dive entries' own text (`lineages/explicit-citation-graph.md`, formerly `citation-graph-audit-2026-07-13.md`) — found 32 real edges, only 12 represented in the clustered lineage doc, 20 missing (disproportionately cross-lineage, exactly matching the user's suspected pattern: LLAssist→LitLLM, GEAR-Up→LitLLM, ReviewGenie→SWIFT-Review, TriSem-LLM→ASReview, InteractiveSurvey→SLRAgents, plus an unsuspected HCRA→ASReview), and 3 edges drawn with no textual support at all.
- **Built a second method, implicit pairwise content-matching** (`lineages/implicit-pairwise-analysis.md`): date-ordered all 27 papers, checked each against every earlier paper's named limitations for uncited-but-real mechanism-to-gap matches. Found 10 more real edges under a conservative, non-exhaustive pass — ProfOlaf alone implicitly answers named gaps in three separate papers (SLRAgents, ResearchRabbit, LLAssist) without citing any of them.
- **Corrected my own mistake mid-session**, twice: first, reused the disputed A–F lineage buckets as `subgraph` scaffolding in the two new "rigorous" diagrams, smuggling the discredited structure back in as if neutral (caught by the user asking directly); rebuilt both diagrams around actual graph structure (connected components via union-find) instead. This revealed the real finding: the explicit citation graph is essentially **one 19-paper giant component**, not six lineages, with LitLLM and AutoSurvey as its actual hubs (7 incoming edges each) — completely hidden by the bucket split. Second, miscounted isolated papers (said 5, was 6 — forgot ResearchRabbit); fixed after the union-diagram computation caught it.
- **Union of both rigorous methods computed via union-find** (not eyeballed): adding the 10 implicit edges on top of the 32 explicit ones pulls two previously **fully isolated** papers — ResearchRabbit and Scholar Augment — into the giant component (19→21 papers). Only 4 papers remain isolated under both methods combined. This became the strongest evidence in the whole comparison: citation-tracing alone is trustworthy but structurally incapable of recovering these two papers' real relationship to the field, since the information was never in either paper's citation list.
- **Built `lineages/lineage-comparison.md`**, a worked example (ProfOlaf drawn all three ways) plus two derived insights: (1) the three methods' divergence tracks directly to what task each gave its LLM (open synthesis loses/fabricates signal, constrained extraction caps it, constrained comparison amplifies hidden signal — same failure mode `check_citation_grounding()` exists to catch elsewhere in this project); (2) the corpus-scale union finding. Trimmed from 182→110 lines after the user flagged it had become three essays stapled together.
- **Deprecated `similarity-cluster.md` rather than rebuilding it**, after weighing the option directly with the user — rebuilding would either duplicate `explicit-citation-graph.md` or keep forcing a bucket shape now twice shown wrong for this corpus. Kept unedited as the comparison's control condition.
- **Rewrote `related-work.tex`'s "Automated systematic review" paragraph** directly from `implicit-pairwise-analysis.md` (per explicit user instruction, not `similarity-cluster.md`) — ProfOlaf is now the paragraph's centerpiece, implicitly answering three named gaps while still lacking citation-graph traversal and validated recall; compiles clean, 21 pages. Built a new ProfOlaf-centered diagram mockup for Obsidian review before it becomes a real TikZ figure.
- **Citation-accuracy fixes, separate audit:** dispatched 5 parallel subagents to deep-dive tools cited in `related-work.tex`'s *other* paragraph (SWIFT-Review, RobotSearch, ASReview, Elicit, ResearchRabbit) that had never gone through the same verification rigor as the 22 core lineage papers. Found SWIFT-Review's DOI resolved to an unrelated influenza paper (fabricated/mismatched citation) and RobotSearch was cited to the wrong Marshall/Wallace paper entirely — both fixed in `refs.bib`, which was also consolidated from two independently-diverged copies into one canonical file with a symlink. All 5 deep-dives appended to `deep-dives.md` (renamed from `lineage-deep-dives.md`) as a new "verification cohort" section.
- **Housekeeping:** deleted `related-work-figure-mockup.md` (stale) and `included_366_2026-07-09.csv` (superseded); consolidated `related-work-landscape.md`'s audit trail into `decisions.md` before deleting it too.

</details>

**Next:** re-read `related-work.tex` fresh against IP&M's actual desk-rejection wording to confirm it's thoroughly addressed, not just improved (see `open-questions.md`'s new checklist). Then run `check_citation_grounding()` against a real project — still unmeasured, and now also gates whether the proposed extract/synthesize redesign (structured `deep-dives.md`-style extraction fields; `synthesize` incorporating implicit-pairwise-style enrichment, pruned via embedding prefilter, not brute-force O(n²)) is worth the investment.

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

---

## 2026-07-11 (session 34, LitDiscover) — All 22 related-work papers deep-dived + narrative lineage built; citation-grounding check shipped; traversal-explosion workflow lesson learned live

**2-tier exp:** Full-text-verified all 7 original Tier 1/2 papers (catching one flat error and one nuance error vs. Gemini's abstract-only extraction), mined the 366-paper CSV for 15 more genuine LLM-native method papers, ran 16 parallel subagents to deep-dive all of them (3 initially blocked by paywalls, all 3 resolved once the user supplied PDFs directly), then built a narrative "who-answers-whom" lineage doc with a Mermaid diagram and shipped a diagnostic citation-grounding check for `synthesize` based on what the audit found.

<details>

- **Full-text benchmark, round 1–3:** Pulled and read AutoSurvey, ProfOlaf (+cloned repo), LitLLMs-are-we-there-yet, SciReviewGen, LitLLM, LiRA (+cloned repo), and Human-Centred Research Automation (user-supplied PDF, ACM DL paywalled). Corrected ProfOlaf's table entry (had a real quantitative LLM-vs-human screening benchmark; Gemini's extraction said "none"). Cloning LiRA's actual repo caught a second correction: CQF1 is an offline eval metric copied from AutoSurvey's code, not a live in-loop check as the paper's abstract implied.
- **Workflow discipline lesson, lived not just written:** Ran `screen` on a 147-paper pending queue without `prefilter` first — 16% yield, ~84% of that Gemini spend wasted. Logged the rule (`litdiscover/decisions.md`): never `screen` >50 pending without `prefilter` first. The very next `traverse` cycle then added **4,534 new candidates** in one shot with zero live progress indicator, which the user caught and asked about directly — traverse.py now prints a running `(i/N)` counter (shipped, tested against `pytest tests/`, 19/19 passing at the time).
- **Extract/synthesize technique audit completed:** Read `synthesizer.py` (870 lines) end to end against the landscape findings. Verdict: citation grounding (no post-hoc check anywhere) is the confirmed, cheap, high-leverage fix; plan-based generation and cluster ground-truth eval are real but lower priority; map-reduce grounding loss is the same root cause as the citation-grounding gap, not separate.
- **Shipped `check_citation_grounding()`:** precision-only diagnostic (batches cited claims against the `extractions` table already paid for, no new NLI model), wired into `litdiscover synthesize` as on-by-default (`--skip-grounding-check` to opt out), writes `<slug>_grounding_report.md`. 7 new tests, 181/181 passing. **Not yet run against a real project** — the actual grounding number is still unmeasured.
- **CSV mining + 22-paper deep-dive:** Filtered ~200 keyword-matched CSV titles down to 16 new genuine LLM-native method papers (dropping 6 classical/pre-LLM tools to one-line citations, moving SGSimEval to an evaluation-benchmark template). Dispatched one subagent per paper; all 16 completed, including 2 that correctly declined to fabricate content when blocked (Scholar Augment abstract-only, SocLitGen fully paywalled) and 1 that couldn't locate the paper at all (TriSem-LLM). User supplied all 3 PDFs directly — all three now have full 6-field deep-dives, closing every gap.
- **Two new wiki artifacts:** `litdiscover/lineage-deep-dives.md` (22 method deep-dives + Methods/Evaluation-Methods tables, extracted and placed up front) and `litdiscover/related-work-lineage.md` (narrative "who answers whom" lineage across 6 named chains + a Mermaid diagram + a Discussion section naming the field's actual meta-gap: nobody else validates discovery recall against a real published survey's full bibliography — LiRA's own paper names this as its unaddressed future work). Ends with a Related Work section scaffold for the IP&M redo.
- **Cloned 2 competitor repos** (`sr-lab/ProfOlaf`, `lira-workflow/auto-review-writing`) into `lit-review/` (gitignored, reference-only) specifically to ground the audit in code, not just paper prose — this is what caught the LiRA/CQF1 correction above.
- Read the user's own unrelated `260708 literature-review.pdf` (persona-memory systems review) as the structural template for the lineage doc — its named-lineage + benchmark-lineage + Discussion + Next-Steps shape is what `related-work-lineage.md` follows.

</details>

**Next:** the 4,534-candidate pending queue in `automated-lit-review-methodology` still needs `prefilter` (not yet run, per the new discipline). Separately, and higher priority: run `litdiscover synthesize` on a real project to get the actual grounding-check number — that decides whether plan-based generation (audit item #2) is worth building at all. Then draft the IP&M redo's Related Work prose from `related-work-lineage.md`'s scaffold.

---

## 2026-07-14 (session 36, LitDiscover) — IP&M checklist item 1 closed; discovery phase reframed around IR-methodology operator ablation; 5 new discovery operators + budget tooling built via TDD; repo restructured (intake→discovery, litdiscover promoted to repo root)

**2-tier exp:** Closed the IP&M resubmission checklist's first item (verified `related-work.tex` against the actual desk-rejection wording, fixed a real bib error along the way); then, prompted by the user wanting to validate each pipeline stage rather than keep betting solely on citation traversal, rewrote `background.md` into a cross-stage `research-roadmap.md` + split-out `phase-discovery-roadmap.md` whose Experiment 1 section is now a full IR-methodology design (Cranfield gold standard, operator-based ablation/ordering/budget/Pareto curves, paired significance testing) — then executed the first four prerequisites of that plan: decomposed `traverse.py` into swappable operators, decided to defer gold-standard expansion, built all 5 remaining discovery operators (author/venue/recency/embedding/co-citation) via TDD, and built a budget/cost-accounting tool. Also restructured the `litdiscover` repo twice at the user's request (renamed `intake/`→`discovery/`, promoted it from `lit-review/litdiscover` to sit at the `citation-networks` repo root).

<details>

- **IP&M checklist item 1, closed.** Re-read `related-work.tex` fresh against the exact desk-rejection wording ("leverage SOTA baselines, especially LLMs... reference the most updated articles from the current year") — confirmed the ProfOlaf-centered rewrite already addresses it (6 papers from 2025-2026 cited). Closed both bib entries still flagged "not independently verified": `Haryanto2024LLAssist` confirmed correct as-is; `Lau2025Elicit` had a real error (author listed as "Lau, A. and others" — actual authors are Lau, O. and Golder, S., verified via PMC full text), fixed plus added missing volume/issue/pages/DOI. Recompiled clean, 21 pages, 0 errors; verified in the rendered `.bbl` that SWIFT-Review/RobotSearch/Lau2025Elicit all render correctly.
- **`background.md` → `research-roadmap.md` → split into `phase-discovery-roadmap.md`.** First rewrite reframed the project as three separately-bettable pipeline stages (Discovery/Extraction/Synthesis) instead of one algorithm; caught mid-review that I'd over-compressed the old sim-vs-production Pareto-filter-direction content out of the rewrite and restored it as its own subsection. User then asked for a "who else touches discovery, and how" survey pulled from `deep-dives.md`'s 27 methods — added as its own subsection, grouped by mechanism family (citation-graph traversal / keyword-only / embedding-search / LLM-keyword-to-API / re-ranking / no-discovery-step-at-all), which found no prior tool in the 27-method corpus does author, venue, or recency-only search — a field-wide gap, not just LitDiscover's. Discovery then grew too large for one doc; split into `phase-discovery-roadmap.md` (all discovery detail) with `research-roadmap.md` kept as the cross-stage overview.
- **Experiment 1 rebuilt around real IR methodology** (user supplied a detailed operator-ablation design referencing the Cranfield paradigm): reframed as operators-not-pipelines, gold standard (6 existing surveys reused, ~15-20 needed only for the final paired-significance step), operator inventory, baselines, marginal contribution, leave-one-out ablation, ordering experiment, budget-normalized comparison, Pareto curves, paired significance testing, "operators not algorithms" as the actual novelty claim, and the sequential-decision/RL framing explicitly deferred (not this experiment).
- **`traverse.py` decomposed into the operator interface** (§7 step 1): `OperatorResult` dataclass contract; `backward_traversal_operator`, `forward_traversal_operator` (now defaults to unfiltered, `hub_threshold=inf`), `pareto_hub_threshold` as independently callable functions; `traverse()` is now a thin orchestrator with its public signature/return shape unchanged (verified against `core/stages.py`'s call site). 12 new operator-level tests; 189/189 passing.
- **§7 step 2 decided: defer gold-standard expansion.** §4.3-§4.8 (baselines through Pareto curves) don't need statistical power and can run on the existing 6 surveys; only §4.9's paired significance testing needs 15-20. Expanding now would also sit idle since the new operators (step 3) didn't exist yet to use it.
- **§7 step 3: all 5 remaining operators built**, in `litdiscover/discovery/operators.py`. Author/venue/recency built first (code-then-tests); embedding-search (S2 Recommendations API, `/recommendations/v1/papers/forpaper/{id}`) and co-citation retrieval (ResearchRabbit's actual mechanism, minus its undisclosed "AI similarity" signal) built via strict TDD after the user asked for it explicitly — tests written first, confirmed RED (`ImportError`), then implemented to GREEN, no refactor needed. Every operator's S2 API usage verified live before implementing, not guessed — caught that the Recommendations endpoint's response key (`recommendedPapers`) differs from every other S2 endpoint used elsewhere (`data`), which would've been an easy silent bug. 217/217 passing after this step.
- **§7 step 4: budget/cost-accounting tool built via TDD** (`litdiscover/discovery/budget.py`): `run_with_cost()` measures any operator externally (S2-call delta on a new `s2_client._s2_call_count` counter, wall-clock time, candidates returned) with zero changes to the operators themselves; `recall_per_call()` is the actual §4.4/§4.7 metric, pure arithmetic. Caught and fixed one of my own test-design mistakes mid-TDD: the first version of the S2-call-delta test called the real (unmocked) `_s2_wait()`, incurring ~4s of real rate-limit sleep across the test suite — fixed by patching `time.sleep` while keeping the real counting logic. 227/227 passing.
- **Repo restructuring, two rounds, both user-requested mid-session:** (1) renamed `litdiscover/intake/` → `litdiscover/discovery/` via `git mv`, updated every `litdiscover.intake` import across `cli.py`, `core/loop.py`, `core/stages.py`, `extract/extractor.py`, 5 test files, and `CLAUDE.md`; (2) moved the whole `litdiscover` repo from `lit-review/litdiscover` up to sit directly at the `citation-networks` repo root (confirmed no relative-path/symlink dependencies broke first), updated `.gitignore`'s nested-repo entry accordingly. Verified both times: git remote intact, uncommitted work preserved, full test suite green from the new location.

</details>

**Next:** §7's four sequenced prerequisites are all done — the next real milestone is actually executing §4.3-§4.8 (baselines through Pareto curves) against the existing 6-survey gold standard using the now-complete 5-operator set + budget tooling, not just their unit tests. Both the `litdiscover` repo and `citation-networks` had uncommitted work at end of session; committed as part of this wrap (see commit log).

---

## 2026-07-14 (session 37, LitDiscover) — Representation-learning roadmap scoped (Experiment 2), section-level ground truth built for all 3 live surveys, gold-set data-quality bug found and fixed after two failed filter attempts

**2-tier exp:** User wants to test whether structured-summary embeddings organize a research field better than raw-text embeddings (motivated by `similarity-cluster.md`'s documented failure); designed `phase-representation-roadmap.md` as a 4-condition clustering experiment against the 3 live surveys' section structure, built that section-level ground truth by hand-reading all 3 PDFs, and along the way found + root-caused + fixed a real gold-set data-quality bug — after my first two automated fixes turned out to be net-harmful and had to be reverted.

<details>

- **`phase-representation-roadmap.md` created**, split out of `research-roadmap.md` §3 (Synthesis) the same way discovery got its own file. Names the current baseline precisely (`_paper_embed_text()` in `synthesizer.py` embeds `title+themes+contributions[0]`, never compared against alternatives), scopes 4 conditions (baseline / abstract / full-text / structured 6-field deep-dive summary) plus a noted extension ladder (abstract+keywords, field-wise structured embeddings, pairwise-LLM upper bound), and folds in an external-agent's reframe: this is a representation-learning evaluation problem with an established paradigm ladder (retrieval → clustering → taxonomy-recovery → downstream-utility), and the real hypothesis is that discourse-structure-aware representations organize a field better than raw-text ones, not just "summaries help."
- **Ground truth built for all 3 live surveys (Ge21-HSS, Le25-GLLM, K17-RGC)** — read all 3 PDFs in full, hand-mapped each gold reference to the section it's discussed under (flat tags, per explicit user decision — taxonomy-recovery/hierarchical scoring left as an open question, not decided). Saved to `live-survey-eval/data/section-ground-truth/*.json`. Corrected a wrong assumption made mid-roadmap-drafting: the 3 APS closed-corpus surveys (S1-MIT/S2-UCG/S3-TOPO) have **no local PDF** and 387-582 refs each — the opposite of "shorter/more uniform" as first guessed — so piloted on the 3 live surveys instead, which have local PDFs and 56-202 refs.
- **Gold-set data-quality bug found, root-caused, and fixed.** While annotating, found 2-5 gold-set entries per survey (except Le25-GLLM, which resolved 57/57 cleanly) that don't correspond to any reference the survey actually cites. Root cause: all 3 surveys have a `survey_doi`/`survey_s2_id` configured, so `build_gold_set_from_s2()` in `09_live_validation.py` fetches gold references straight from **S2's own `/references` endpoint** — the bad entries are S2's own citation-graph linking errors (a book-series name stored as a "paper," or an unrelated real paper mis-linked entirely), not a bug in this codebase's PDF parsing.
- **Two automated filters attempted and both reverted after live testing proved them net-harmful** — worth remembering as a lesson, not just a footnote: an all-caps/<3-words rejection, then a narrower series-name-phrase substring match, both sounded plausible but each rejected far more *real* references than actual garbage (Goodman's "Snowball sampling", Munkres' "ELEMENTS OF ALGEBRAIC TOPOLOGY", Epstein's "Agent_Zero... (Princeton Studies in Complexity)" all got wrongly caught). Caught this only by testing the filter against the actual affected titles before trusting it, not by trusting the plausible-sounding logic. Reverted both; the only code change that shipped is a generic `FUZZY_THRESHOLD` tightening (88→92) plus honest comments explaining why a content filter was rejected.
- **Actual fix: manual, surgical removal of only the confirmed-bad entries directly from the gold-set JSONs** — Ge21-HSS 202→200, K17-RGC 56→52 — consistent with `build_gold_set`'s existing "manual corrections survive re-runs" contract. `phase-discovery-roadmap.md`'s reported live-survey recall numbers (73.7-100% headline, §4.3's per-operator table) are now stale against the corrected, smaller gold-sets and should be recomputed — small expected effect (6 entries across 258), not urgent, but a known loose end.

</details>

**Next:** recompute the live-survey recall numbers against the corrected gold-sets; then resolve `phase-representation-roadmap.md` §5's remaining open decisions (full-text pooling strategy, k-fixed-vs-elbow, whether to expand past 6 surveys for statistical power — shared with discovery's own §4.2/§4.9) before building the actual Experiment 2 embedding/clustering pipeline.

---

## 2026-07-14 (session 39, LitDiscover) — GraphSource abstraction built and proven live; discovery's canonical result (04b) migrated and promoted with a real, well-diagnosed recall/precision improvement; closed-corpus and live-survey tracks unified onto one operator implementation

**2-tier exp:** User pushed back on an earlier framing that closed-corpus and live-S2 discovery couldn't share code ("but they are the same algorithm no?") — correctly; built a real `GraphSource` abstraction (`S2Source`/`ClosedCorpusSource`) so `backward_traversal_operator`/`forward_traversal_operator`/`pareto_hub_threshold`/`author_expansion_operator`/`venue_expansion_operator` now run identically against either data source (259/259 tests passing, all 227 pre-existing tests unmodified), then used it to migrate all 6 originally-simulated closed-corpus scripts plus a new 7th, discovering along the way that the paper's canonical cold-start result had a real filter-design flaw whose fix changed the headline numbers (93.5%→99.6% mean recall).

<details>

- **Corrected an overstated claim mid-session.** First pass at `phase-discovery-roadmap.md` §1.3 called the closed-corpus/live-S2 split "an online/offline mismatch" that would "likely always be a proxy." User's pushback was right: this conflated a real but ordinary engineering gap (`s2_client.py`'s network calls hardcoded into the operators, no injectable abstraction) with an accidental implementation difference (the two tracks filtered hub papers at different pipeline points, which the closed-corpus data never actually required). Rewrote §1.3 to reflect this before building anything.
- **Built `litdiscover/discovery/graph_source.py`**: `GraphSource` protocol, `S2Source` (thin adapter — delegates to `traverse.py`/`operators.py` via module-attribute lookup specifically so it doesn't break those modules' own existing patched tests, a real subtlety caught mid-implementation), `ClosedCorpusSource` (pure in-memory, DOI-keyed, no network), `_infer_venue_from_doi()`. Four operators retrofitted with optional `source=`, defaulting to `S2Source` — zero behavior change for every existing caller. `pareto_hub_threshold` needed no changes at all (it only ever reads `citation_count` off paper dicts, never touches the network).
- **`eval/04b_cold_start_lowseed.py` (the paper's primary result) migrated and promoted to canonical.** Full 54-condition comparison (3 surveys × 3 seed strategies × k∈{1,2,3,4,5,10}): mean recall 93.5%→99.6%, mean corpus size 205,021→66,023 (3.1x smaller), conditions hitting recall=1.000 3/54→49/54. Root cause, verified by inspecting actual depth/round curves not assumed: the old filter discarded newly-found *candidate* papers based on the candidate's own out-degree — a genuine gold paper could be excluded purely for citing a lot of things itself. The corrected filter (matching production) only decides whether to expand an already-visited *frontier* paper's citers. One legible trade-off: all 4 conditions that got worse are in the `contaminated`-seed strategy at low k — the condition most dependent on wide, indiscriminate exploration within a fixed 2-round budget. Old script/data archived as `*_legacy`, not deleted, fully reversible via git either way.
- **Surfaced a real downstream consequence rather than absorbing it silently:** the corrected engine leaves `05_miss_analysis.py`'s canonical k=5/top-k condition with **zero misses** for all 3 surveys, so `06_publication_figures.py`'s Fig 7 ("miss analysis") has nothing left to plot. Asked the user directly rather than picking a fix; they chose to pause on Fig 7/`06` and revisit after reviewing the rest.
- **Migrated `eval/03`, `sweep/04`, `sweep/07_rounds_sweep.py`, `sweep/08`** to the same engine. `eval/03` and `sweep/08` needed a deliberate design split from `04b`'s migration: both sweep Pareto percentile as an explicit controlled variable, which production's Gini-adaptive calibration would silently override — resolved by computing each threshold directly and passing it straight to `forward_traversal_operator`'s `hub_threshold`, keeping the real candidate-fetching mechanics while bypassing only the threshold-selection policy.
- **Hit a real performance wall, not a correctness one**, and let it change the plan: `eval/03`'s unfiltered strategies at depth 6 push frontiers into the hundreds of thousands, and running that through production's `ThreadPoolExecutor`-per-paper design (built for dozens-to-low-hundreds workloads) took ~30-40 minutes and climbed toward the system's 16GB memory ceiling (56MB free at the point it was killed). User's direct call afterward — "can we just fix them without trying to rerun the full thing?" — reframed the rest of the session: migrate code correctly, verify via the already-validated `04b` pattern, skip full execution unless a specific reason exists to spend that time/API budget. Applied consistently to `sweep/04`, `sweep/08`, and `live-survey-eval/09`.
- **Built `closed-corpus-eval/scripts/eval/07_operator_benchmark.py`** (new) — mirrors `live-survey-eval/10`'s shape, ran successfully end-to-end (single-pass, seconds not minutes), real ablation numbers per survey. Author/venue expansion explicitly out of scope with hard evidence, not just effort-avoidance: the `.mat` file's author/DOI fields use MATLAB's `string` type wrapped in MCOS object encoding; confirmed via `mat73` (a library built specifically for this MATLAB version), which explicitly raises `"MATLAB type not supported: string, (uint32)"` on this exact file.
- **Migrated `live-survey-eval/09_live_validation.py`** to call the real operators via `S2Source`, closing the PDF-first/Gini-calibration drift from production documented in §1.2/§1.3 — not run to completion (real S2 API quota).
- **Deduplicated `live-survey-eval/10`/`11`/`12`**: extracted `10`'s loaders/config/metrics into `_shared.py`; `11`/`12` now `import _shared` normally instead of `importlib.util.spec_from_file_location`-loading `10`'s whole module body. Verified all three import cleanly via `runpy`.
- **Closed the loop on "open items" a stop-hook flagged as unresolved** — Fig 7, the full-run decisions, and the `.mat` blocker were each already explicit user decisions made mid-session, not gaps; rewrote the wiki's closing section to record each as resolved-by-decision with its rationale, so a future session doesn't re-litigate settled questions.

</details>

**Next:** if the paper needs Fig 7 resolved before submission, that's the first decision to revisit (re-anchor to a harder seed condition, or drop it). Otherwise: run `eval/03`/`sweep/08`/`live-survey-eval/09` to completion only if their updated numbers are actually needed; recovering the `.mat` author data needs an official MATLAB export or an upstream tabular source, not more effort on the current approach. The pre-existing top blocker (running `litdiscover synthesize`'s citation-grounding check against a real project) is still unaddressed and now several sessions old.

---
