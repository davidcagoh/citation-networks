# Session Log

Reverse-chronological. Start every session here, then check open-questions.md.

---

## 2026-08-01 (session 47, Eval methodology + SYNERGY composition sweep) — new wiki/evaluation.md (by-stage eval-method mapping, SYNERGY vs CLEF TAR); lit-review-bot/paper renamed evals/ (manuscript archived, aps-eval hash-randomization bug fixed across 6 scripts); synergy-eval TDD-built from scratch (55 tests) and run twice against a real SYNERGY review (Hall_2012) — CO's standout status replicated on a second corpus, 2026-07-14's chaining rejection refined from "chaining is bad" to "filtering's value is operator-position-dependent"

**2-tier exp:** Started as a wiki-organization question (where does an eval-methods-by-stage table belong) that surfaced real duplication across `litdiscover.md`/`synthesis.md`, resolved by pulling a new `wiki/evaluation.md` out. That led into verifying SYNERGY (a systematic-review benchmark) actually has a usable citation graph (it does, confirmed against real downloaded data), which led into designing and building a full discovery-operator composition-sweep experiment against SYNERGY's `Hall_2012` review — TDD throughout, real production `litdiscover.discovery.operators` calls via `source="local_corpus"`, not mocked.

<details>

- **`wiki/evaluation.md` (new)** — cross-cutting eval-methodology findings shared by LitDiscover + Synthesis (not Zeitgeist): a by-stage table (Discovery/Screening/Extraction/Synthesis → which eval methods actually apply, ranked worst-to-best-supported), the SYNERGY-vs-CLEF-TAR distinction, and the synthesis-side eval-standard-gap evidence table moved out of `synthesis.md`. `litdiscover.md` and `synthesis.md` both trimmed to point here instead of duplicating.
- **SYNERGY verified against real data, not just its README.** Installed the `synergy-dataset` pip package, downloaded 7 of its 26 reviews (small/medium/large, both CS-domain reviews in the corpus), checked `referenced_works` directly: 60–99% of records carry a real, populated per-paper OpenAlex reference list — not a subset restricted to the review's own candidate pool. `Hall_2012` (CS domain, 8,793 records, 93.8% reference coverage) identified as the strongest candidate for a discovery experiment.
- **`lit-review-bot/paper/` renamed `lit-review-bot/evals/`** (same GitHub repo, `robust-literature-discovery`): `drafts/` (the paused IP&M manuscript, all earlier submission attempts) archived to `_archive/drafts/`; `closed-corpus-eval/` renamed `aps-eval/`; new `synergy-eval/` track added. `.gitignore`/`CLAUDE.md`/`README.md` rewritten; confirmed zero functional impact (all path references were prose/comments, `litdiscover`'s 246 tests still green, APS data symlink still resolves).
- **Fixed a real, previously-flagged-but-unfixed bug**: `aps-eval`'s `make_seeds_random`/`make_seeds_contaminated` called `list(some_set)` before `random.shuffle()` — non-reproducible across processes since Python randomizes string-hash order per process by default. Fixed via `sorted()` for a deterministic pre-shuffle order, across all 6 files carrying a copy of this logic (found while building `synergy-eval`'s own, correctly-written-from-the-start seed strategies). Verified the `top_k` tiebreak fix is a byte-identical no-op on real data (zero ties among any survey's top-10 gold refs) before committing.
- **`synergy-eval/` built via TDD, 55/55 tests green**: `_corpus_loader.py` (OpenAlex records → `CorpusIndex`, edges filtered to in-pool targets only — a closed-corpus experiment, same shape as `aps-eval`), `_local_co_citation.py` (reconstructs `co_citation_operator`'s `FWD∘BWD` mechanism against local `cites`/`cited_by` dicts, since the real operator is hardcoded S2-only), `_seed_strategies.py` (top_k/random/contaminated, written correctly from the start), `_composition.py` (`run_sequence()` — isolated / chained-unfiltered / chained-filtered-by-gold-label composition modes over 5 operators, corpus-agnostic by construction, deliberately not yet shared with `aps-eval`), `_metrics.py` (recall + precision — precision only possible here because `Hall_2012` has explicit `label_included=0` for the whole pool, not just a survey's own bibliography), `_diagnostics.py` (per-stage overlap + simulated yield-stop against production's own `YIELD_THRESHOLD=0.05`).
- **Two staged experiment runs, not one blind sweep** — Step 1 (isolated 5-operator baseline) run and inspected before Step 2 was built at all; Step 2 (126-condition composition sweep) sanity-checked with `--limit 6` before the full run. **Step 1**: CO best recall/precision balance (19–29%/49–65%) — replicates the 2026-07-14 live-survey finding on a second, independent corpus. FWD unexpectedly strong locally (37% recall) vs. dead on live S2 — closed-corpus FWD only reaches an already-topic-filtered pool. **Step 2**: best condition `BWD→FWD→CO→VENUE` chained-unfiltered (76.2% recall/27.2% precision); chaining beats isolated-union almost everywhere, refining (not overturning) the single 2026-07-14 rejected-chaining data point; filtering's effect on precision is operator-position-dependent (helps a lot before high-fan-out `FWD`, costs real finds before low-fan-out `BWD`) — confirmed with exact per-stage multiplier/marginal-gold numbers, not inferred.
- **Caught and fixed a real bug in the diagnostics themselves, before reporting any findings**: the stage-overlap metric was initially computed from `new_candidates`, which is disjoint across stages by construction (each stage dedupes against everything found so far) — so it read `0.0` for every pair regardless of what the operators found. Added `raw_candidates` (pre-dedup) as a separate field, added a regression test, reran.
- **All work committed in both repos as it landed** (not batched at the end): 8 commits in `evals/`, 4 in `citation-networks` (`wiki/evaluation.md` creation + 2 rounds of findings write-ups + this session-wrap).

</details>

**Next:** the `FWD→BWD` contaminated-seed precision dip (52.9%→46.7% with filtering) is currently a single-condition observation, not verified across other sequences/k values — flagged as an open question in `wiki/evaluation.md`, not resolved. `Hall_2012`'s composition sweep hasn't been extended to the other 25 SYNERGY reviews — open whether this needs to become a multi-review claim. Screening-comparison against SYNERGY/CLEF TAR deliberately dropped from scope (LitDiscover's claim is about Discovery, not Screening). Unrelated, still-open from prior sessions: `synthesize`'s citation-grounding check has never been run against a real project; the engine-vs-manual-pipeline `HUMAN_STEER` decision remains undecided.

---

## 2026-07-31 (session 46, LitDiscover discovery-layer consolidation) — new protocol-log.md source of truth for discovery-algorithm configs; survey-vs-related-work-section distinction named and connected to existing relwork.py/synthesis.md work; discovery/ refactored from 11 files to 3 across two repos, fully verified

**2-tier exp:** Started with a source-of-truth request (what discovery configs have been tried, verdict) — built `wiki/litdiscover/protocol-log.md` with operator/mode shorthand codes and a composition table. Pivoted into a conceptual detour (survey vs. related-work-section as distinct genres, connected to `relwork.py`'s existing asymmetric-relation framing) that the user paused on feeling overwhelmed by repo complexity — resolved by walking the actual `discovery/` module map plain-language instead of designing more. That walkthrough surfaced a real, user-driven redesign: all 7-then-8 discovery operators (2 CLI-wired + 5 research-only) unified into one `operators.py`, the `GraphSource`/`S2Source`/`ClosedCorpusSource` class hierarchy dissolved into a `source="s2"|"local_corpus"` argument, `forward_cites.py` found to duplicate `forward_traversal_operator` and dissolved entirely, `verify.py`/`relwork.py` moved to a new `tools/` package. Executed via `EnterPlanMode` given the scope (11→3 files in `discovery/`, cross-repo impact on `paper/`'s already-published 99.6%-recall result) — full plan approved before any edit.

<details>

- **`wiki/litdiscover/protocol-log.md`** (new): two tables — operator/mode shorthand codes (`BWD`/`FWD`/`CO`/`AUTH`/`VENUE`/`RECENCY`/`EMBED`/`KEYWORD`, `WORKFLOW`/`HUBFILTER`/`COMPOSE`/`SCREEN_LLM`/`HUMAN_STEER`) and a composition table of every protocol variant tried with a kept/rejected/undecided verdict + why, populated retroactively from the existing operator-benchmark numbers and manual-pipeline retrospective. Linked from `litdiscover.md` and `INDEX.md`.
- **Survey vs. related-work-section distinction named explicitly**: related-work sections argue asymmetrically for one paper's novelty (extends/contradicts), surveys map a field comprehensively and thematically — the codebase had already half-discovered this without naming it (`relwork.py`'s asymmetric mining vs. `synthesize`'s thematic k-means clustering; `synthesis/synthesis.md`'s prior rejection of thematic clustering for the lineage work). Not acted on — user paused on feeling the repo was "delicate" and beyond current understanding before any design decision was made.
- **Discovery-layer consolidation, the substantive work this session** (`lit-review-bot/litdiscover/litdiscover/discovery/`, 2021→~950 lines, 11→3 files):
  - `operators.py` now holds all 8 discovery operators (`backward_traversal`, `forward_traversal` — both moved from the deleted `traverse.py` — plus the existing `author_expansion`, `venue_expansion`, `recency_search`, `embedding_search`, `co_citation`, and a new `keyword_search_operator` wrapping the deleted `search.py`), `OperatorResult`/new `CorpusIndex` dataclasses, `pareto_hub_threshold`, and `budget.py`'s `run_with_cost`/`recall_per_call` (kept — `paper/`'s benchmark scripts import these directly).
  - `graph_source.py` deleted — its `GraphSource`/`S2Source`/`ClosedCorpusSource` class hierarchy replaced by a `source: Literal["s2","local_corpus"] = "s2"` + `corpus: CorpusIndex | None` argument on each pluggable operator, branching internally. Venue inference (APS DOI-prefix parsing) intentionally *not* ported — `operators.py` now carries zero dataset-specific knowledge; that's the dataset loader's job (`paper/closed-corpus-eval/scripts/_corpus_loader.py`).
  - `forward_cites.py` deleted, not moved — read directly, its `fetch_forward_citations()` was calling the exact same `s2_client.paginate_edges(..., "citations")` primitive `forward_traversal_operator` already wraps, just unfiltered over the whole included set instead of the frontier. Its report-building moved to `reports.py` (`build_forward_cites_report`/`write_forward_cites_edges_csv`, reshaping the operator's flat `OperatorResult` back into the old per-source-paper breakdown), its DB-write logic generalized into `db/client.py::ingest_candidates(client, project_id, candidates, edges)` — reusable by any future operator-output-to-queue CLI command, not forward-cites-specific.
  - `verify.py`/`relwork.py` moved unchanged to a new `litdiscover/tools/` package (neither produces discovery candidates — one's a read-only audit, one's a human-decision-support tool) — no internal import fixes needed, since neither imported anything being deleted.
  - `orchestrator.py` (new) replaces `traverse.py`'s `traverse()` as the CLI's stable entry point, renamed `run()` since forward/backward are "just operators" now — same public contract `core/stages.py` depends on, with `s2_calls`/`wall_seconds` folded into its stats dict via `run_with_cost()` (an intentional, additive shape change, not a regression).
- **Cross-repo risk handled as the plan's own step 0**: a background Explore agent traced every consumer of the 10 touched files *before* any deletion — confirmed `graph_source.py`/`budget.py` have zero usage inside `litdiscover` itself but are imported directly by 10+ scripts across `paper/closed-corpus-eval/` and `paper/live-survey-eval/` (a separate git repo). All 12 consumer scripts updated in lockstep (import paths + `source="local_corpus", corpus=X` call-site pattern), including the canonical `04b_cold_start_lowseed.py` that produced the paper's cited 99.6%-recall number.
- **Full verification, not just "tests pass":** `litdiscover` test suite 246/246 green (rewrote `test_operator_source_param.py`'s `GraphSource`-injection tests into `source="local_corpus"`/`CorpusIndex` tests, absorbing `test_graph_source.py`'s still-valid `ClosedCorpusSource` coverage before deleting that file; renamed `test_forward_cites.py` to test the new `reports.py`/`db.client` functions instead of the dissolved module). Re-ran `04b_cold_start_lowseed.py` against the real 508MB APS dataset and compared against the pre-migration git-committed JSON with identical methodology — the deterministic `top_k` seed strategy came back **byte-identical** (100.0000% recall, 72,395 mean corpus size, exact match), proving zero behavioral change in the actual engine. The `random`/`contaminated` strategies drifted slightly; traced to a **pre-existing, unrelated bug** in the eval script itself (`list(some_set)` before `random.shuffle()`, combined with Python's default per-process hash randomization) — not introduced by this session, flagged for a future fix. CLI smoke-tested: every touched command's deferred in-body imports resolve against the real package.
- **Housekeeping:** confirmed pip-installing `litdiscover` in editable mode was needed to actually exercise the cross-repo import chain (not just parse it) — did so, unrelated `comicbox` dependency-conflict warning ignored (pre-existing, not from this install).

</details>

**Next:** `litdiscover/CLAUDE.md` and `paper/CLAUDE.md` both still describe the pre-consolidation architecture (the "Discovery-Operator Research Framework" section, `ClosedCorpusSource` references) — need syncing to match the new file layout, part of this session-wrap. The eval script's `list(set)`-before-shuffle nondeterminism bug (found, not fixed) would make `random`/`contaminated` seed-strategy numbers non-reproducible on any future rerun, independent of this refactor. The survey-vs-related-work-section fork (output-mode split) is still just a named idea, not designed or scoped — paused at the user's request, not abandoned.

---

## 2026-07-21 (session 45, Wiki consolidation + eval-methodology dive) — litdiscover/synthesis wikis collapsed to one flat file each after too much info spread too thin; reference-systems promoted to repo root; found how competing survey-generation systems actually claim superiority; zeitgeist codebase-map refreshed and a new post-paper direction recorded

**Started as a wiki health check**, then pivoted into a real dive: dug into
`lit-review-bot/projects/automated-lit-review-methodology/` (an old LitDiscover-engine-driven
project) at the user's request to see how competing automated-lit-review-generation systems
(AutoSurvey, LiRA, SurveyX, SurveyGen-I, InteractiveSurvey, etc.) each claim to beat the others.
Found the project's own raw discovery pool was mostly noise (generic high-citation ML papers
pulled in by traversal); the real answer lived in `reference-systems/deep-dives.md`'s per-system
"how it performed" fields. Synthesized the pattern across systems: pick a metric family
(citation-grounding NLI, LLM-judge coverage/structure/relevance, ROUGE, reference-relevance IoU),
build your own benchmark, beat "naive RAG" plus 1-2 named predecessors on your own axes — and the
underlying metrics are almost all inherited from AutoSurvey's own single, never-repeated
meta-validation (ρ≈0.54 against human judgment), not independently re-validated by each borrower.

<details>

- **Archived + promoted based on that finding:** `automated-lit-review-methodology/` moved to
  `lit-review-bot/projects/_archive/` (noise, superseded by `deep-dives.md`);
  `lit-review-bot/reference-systems/` (14 cloned systems + `deep-dives.md`) promoted to the repo
  root — important enough on its own, not just a LitDiscover subfolder. `.gitignore`, both
  READMEs, and cross-references across the wiki updated to match.
- **User flagged the wiki itself was part of the problem** ("too much info... all over the damn
  place... shouldn't it just be notes and roadmap or even one flat file") — mid-restructure of
  `wiki/litdiscover/` at the time, which was ironically about to make one of the files longer
  while "fixing" this. Stopped, asked, collapsed instead.
- **`wiki/litdiscover/`'s five files** (`research-roadmap.md`, `discovery-roadmap.md`,
  `corpus-curation-prior-art.md`, `decisions.md`, `open-questions.md` — 2,261 lines) merged into
  one flat `litdiscover.md`, most-important-first, leading with the thing that now gates
  everything else in the file: whether the manual pipeline (session 44) replaces the engine's
  Discovery stage entirely, which directly contradicted `discovery-roadmap.md` §7 step 0's
  standing (and now stale) instruction to build the §4.0 end-to-end harness "ahead of any further
  work." `manual-pipeline-retrospective.md` kept separate — already tight and the newest,
  most-load-bearing doc in the directory.
- **`wiki/synthesis/`'s nine files** (`roadmap.md`, `q-synth-plan.md`,
  `representation-learning-plan.md`, `background/` ×2, `example-comparison/` ×4 — 2,064 lines,
  nested three directories deep) collapsed the same way into `synthesis.md`. Direct motivation:
  this is exactly where the "no mature synthesis-quality eval standard exists" finding lived
  (`background/eval-standard-gap.md`) — buried enough that it got missed in this session's own
  earlier review of the project (surfaced only when independently rediscovered via `deep-dives.md`
  during the eval-methodology dive above) — now placed prominently near the top instead, and
  cross-linked to `litdiscover.md`'s own independent discovery of the same shape of gap one stage
  earlier (discovery/screening, not just synthesis).
- **Mid-turn git housekeeping:** user asked to pull/push, having not done either in a while.
  Fetch confirmed no upstream divergence (just 8 commits ahead, nothing new on origin) — finished
  the in-progress restructure first rather than pushing a half-done state, then committed and
  pushed both the litdiscover and synthesis consolidations as separate commits.
- **`wiki/zeitgeist/` checked against the same complaint and found not to need it** — 4 flat
  files, 285 lines total, no nesting, each with a distinct job (state snapshot / append-only
  decisions / live todo / archived research note). Real issue was staleness, not structure:
  `codebase-map.md` hadn't been updated since session 21 (2026-04-16) and still showed NST
  training as in-progress and Time Curves as waiting on it, when `decisions.md` already recorded
  both as complete-but-dropped-from-scope as of 2026-04-17. Fixed.
- **New direction recorded, not just a refresh:** user decided Zeitgeist isn't done at the
  §§1–4 paper — a time-axis-aware t-SNE/force-directed layout (not SG-t-SNE's current
  symmetrized, atemporal projection) is now planned as post-paper work, with LitDiscover's own
  traversal rounds named as a possible alternate temporal signal on a recovered subgraph, not just
  publication year. Recorded in `decisions.md` (explicitly not reopening the §§1–4 scope
  decision) and `open-questions.md`, cross-linked to `synthesis.md`'s already-planned Q-SYNTH
  NST-vs-UMAP-vs-SG-t-SNE comparison on the same K17-RGC subgraph rather than standing up new
  infrastructure.

</details>

**Next:** none of session 44's three continuation threads (fresh A-share dataset, manual-pipeline
methodology refinement, lit-review-eval-methodology survey scoping) were started this session —
still open. Zeitgeist's new time-axis-layout thread is unscoped past the idea itself (t-SNE vs.
force-directed not chosen, doesn't live anywhere yet, "LitDiscover round" isn't currently a field
`core/loop.py` persists per included paper). LitDiscover's own top blocker
(`check_citation_grounding()` never run against a real project) remains untouched.

---

## 2026-07-21 (session 44, Manual pipeline / A-share + eval surveys) — Manual composable-pipeline experiment run end-to-end (keyword search → curate/extract → refine → forward/co-citation) across two new Zotero-backed surveys; china-ashare-strategy-survey synthesis built and reconciled; pipeline retrospective written for a future LitDiscover redesign

**2-tier exp:** Started as ordinary wiki/codebase questions, then pivoted hard: user is exploring a manual, human-steered discovery/curation pipeline as a *candidate replacement* for LitDiscover itself, not an addition to it — motivated by LitDiscover's own finding that co-citation was the only real-signal non-traversal operator while embedding/venue/recency all failed. Built two new project folders (`lit-review-bot/projects/china-ashare-strategy-survey/`, `trading-eval-survey/`) after moving `projects/` out of the litdiscover engine's own repo (was accidentally version-controlled inside the private-but-PyPI-adjacent package repo). Ran the full planned pipeline across both, discovered along the way that a Feishu-competition weekly-search job had already pre-seeded the same Zotero group library with real prior results (`low_vol.py` CAGR=+9.32%/SR=0.85, best-so-far `vol_managed` Score=0.3116) — deliberately not reused (narrow single-regime dataset), but its validated/ruled-out hypotheses carried forward as a literature-cross-checked seed list. Closed by reconciling 5 overlapping short-horizon candidates down to ~3-4 real mechanisms, and writing up 8 concrete findings for a future LitDiscover redesign.

<details>

- **Zotero set up as the pipeline's reference store**: `zotero-cli` (already installed) pointed at the group library (`6619241`) via `.env` credentials (`ZOTERO_USER_ID`/`ZOTERO_GROUP_ID`/`ZOTERO_API_KEY`, overriding the local-Zotero-app default). Two collections created: "A-Share Strategy Survey" (`8MPXJM4U`, grew from 26→38 items across 4 search rounds) and "Trading Eval Methodology" (`TENHNNC8`, 12 items → 10 after dropping 2 unverifiable citations).
- **Caught 2 likely-hallucinated citations** in a different project's own seed bibliography (`algo-traders/paper/references.bib`) — "Old Habits Die Hard" (Simhi) and "Continuous Position Shrinkage" (Ravagnani) resolve to nothing findable anywhere, and the source paper's own `main.bbl` has no arXiv ID/DOI for either, just a bare `arXiv preprint, 2026` — dropped rather than extracted, flagged to user as ironic given one's own subject is LLM-hallucinated trading strategies.
- **`projects/` moved**: `lit-review-bot/litdiscover/projects/` → `lit-review-bot/projects/` (research-run artifacts don't belong inside the engine's own repo, which is gitignored at the `citation-networks` level and gets published to PyPI as a package — though PyPI itself never shipped `projects/`, so this was a discoverability fix, not a security one, once checked). `litdiscover/CLAUDE.md` updated to say run engine commands from `lit-review-bot/`, not from inside the engine repo.
- **Trading Eval Methodology survey**: seeded from `algo-traders/paper/references.bib` (a sibling crypto-perp project's own eval-methodology bibliography — asset-class-agnostic technique, re-used as seed). Deep-extracted PBO/CSCV (Bailey et al. 2014), Deflated Sharpe Ratio, GT-Score, a walk-forward validation paper, ORCA (regime-correlation crash detection), plus abstract-level notes for Harvey-Liu-Zhu and others. Established a validation-strength framework (synthetic ground-truth > real-data-with-power-check > real-data-proxy-only) — directly informed by session 41's own lesson that isolated-stage eval numbers aren't defensible without end-to-end validation.
- **A-Share Strategy Survey**: 26 pre-existing weekly-job notes synthesized first (ruled out: intermediate-horizon momentum, raw IC as portfolio proxy; carried forward: low-vol/idio-vol core, regime-conditioning, overnight-MAX filter, turnover-crowding, robust covariance estimation, clustering-constrained selection) — explicitly not reusing the prior effort's tuned parameters (bear-window-only), only its signal theses. Then 4 further rounds: (1) thrust re-search (not just gap-filling, per direct user correction) found daily momentum and the single strongest execution-gap evidence in the collection (a paper documenting A-share price-limit "upstream contamination" inflating IC by 18% while cutting Sharpe by 0.44, with a directly-applicable fix for the prior effort's own `low_vol.py`); (2) a third keyword round showed dropping yield (mostly repeats), the stopping signal the user asked to check for; (3) forward citation via the real Semantic Scholar API (not generic search), deliberately targeting old-enough-to-have-citations seminal papers rather than the newest ones, found 4 strong papers including one connecting the low-vol and lottery-preference threads; (4) a co-citation-adjacent pass (true co-citation blocked by a publisher eliding references) found the single most load-bearing methodological result of the whole survey — break-even transaction costs per anomaly (as low as 0.12% for short-horizon effects), a statistical-power fix for China's short samples, and a resolved tension between two papers' conflicting equal-weighted-portfolio findings.
- **Reconciled 5 overlapping short-horizon/retail-driven candidates** (daily momentum, last-hour momentum, overnight-MAX, day-night institutional timing, turnover-crowding) by comparing mechanism/horizon/attribution across already-extracted notes, no new search — resolved to ~3-4 real independent mechanisms; last-hour momentum is genuinely distinct, two pairs likely overlap and need real data (not more literature) to fully resolve.
- **Wrote `wiki/litdiscover/manual-pipeline-retrospective.md`** — 8 concrete findings from actually running this pipeline twice, for whoever redesigns LitDiscover next: a missing "reconcile for redundancy" stage, a forward-citation age-targeting rule, a co-citation fallback-path requirement, independent convergence on LitDiscover's own `cycle_yield` stopping logic, a mandatory citation-verification gate (converges with `verify`'s existing role), a real single-pass-curation false-negative case, graduated extraction depth, and shared-library contamination risk.

</details>

**Next:** three threads the user flagged for continuation, not yet started: (1) source a fresh, general A-share dataset to actually re-test the reconciled candidates against (deliberately not the old competition's narrow bear-window snapshot); (2) revisit/refine the citation-finding methodology itself (forward/co-citation targeting rules, the missing reconciliation stage) — likely informed by the retrospective; (3) a *separate* new project specifically surveying literature-review evaluation methodology itself, to strengthen the case for this whole manual-pipeline approach — distinct from `trading-eval-survey/`, which is about trading-strategy eval, not lit-review eval.

---

## 2026-07-14 (session 43, Repo admin/READMEs) — GitHub housekeeping (deleted automated-lit-reviews, renamed citation-dynamics→zeitgeist, added June-24 collaborator to citation-networks); root + nested READMEs brought current across 5 repos; a real broken symlink from the rename found and fixed; two stale/dead CLAUDE.md files cleaned up

**2-tier exp:** Pure infrastructure/documentation session, no research. GitHub-side cleanup (repo delete/rename/collaborator) triggered a cascade of local staleness: the root `citation-networks` README still described the pre-reorg directory layout, `zeitgeist/README.md` still said "Citation Dynamics" and undersold a completed pipeline as "not built," and the `citation-dynamics`→`zeitgeist` rename had silently broken a real symlink (`lit-review-bot/paper/closed-corpus-eval/data/processed`) that the eval pipeline depends on. Checking the nested `litdiscover`/`paper` READMEs against their own code surfaced two more real inaccuracies (a dead link to the now-deleted `automated-lit-reviews` repo, and screening's actual required env vars — `OPENAI_API_KEY`/`OPENAI_BASE_URL` — missing from the README while a `GROQ_API_KEY` "alternative backend" it advertised is never read by any code in the repo).

<details>

- **GitHub actions (user-confirmed before each):** deleted `automated-lit-reviews` (permanent, superseded by `litdiscover`), renamed `citation-dynamics`→`zeitgeist` (GitHub keeps a redirect), invited `June-24` (Mohammed Junaid Anwar, MScAC AI @ UofT — identity confirmed via `gh api users/June-24` before inviting) to `citation-networks` with Write access, pending acceptance.
- **Local remote sync:** `zeitgeist/`'s local clone `origin` repointed to the new `zeitgeist.git` URL.
- **Root `README.md` rewritten**: replaced the pre-reorg `citation-dynamics/`/`lit-review/` structure diagram with the current `zeitgeist/` + `lit-review-bot/{litdiscover,paper,reference-systems}/` layout, added the three-stage pipeline diagram and a status table sourced from `wiki/research-program.md`/`INDEX.md`, and added a Setup section documenting the three nested-repo clone commands (independent repos chosen over submodules — `litdiscover`/`zeitgeist` are both actively developed in place, including `litdiscover`'s own PyPI publish cycle, which would fight a submodule's pinned-commit pointer).
- **`forward_cites.py`/`verify_refs.py` moved to `utils/`** with a new `utils/README.md` (setup, per-script usage, recommended order) and a docstring note in each script pointing at the project-integrated CLI ports (`lit-review-bot/litdiscover/litdiscover/discovery/{forward_cites,verify}.py` — the `forward-cites`/`verify` commands) so it's clear when to use the standalone scratch version vs. the DB-integrated one.
- **New `lit-review-bot/README.md`**: shell-folder index explaining `litdiscover/`/`paper/`/`reference-systems/` aren't one repo, with each one's actual GitHub repo and role.
- **`zeitgeist/README.md` fully rewritten** (was last touched in April, pre-rename): fixed the title/old-repo-name, replaced the stale MATLAB-era `src/analysis/` structure with the actual `src/phase1-5_*.py` pipeline from `wiki/zeitgeist/codebase-map.md`, corrected "full analysis loop not built" to the actual current status (first LNCS draft compiled, key results table), and added the pipeline-relationship diagram to `lit-review-bot/`.
- **`litdiscover/README.md` fixed**: the `automated-lit-reviews` "see the archived repo" link now correctly says it's no longer on GitHub (pointing at the local `deprecated-bot/` copy instead); the environment-variables section was missing `OPENAI_API_KEY`/`OPENAI_BASE_URL` (verified via `grep` that `screen/llm.py`'s bare `OpenAI()` client actually requires these — a user following the old README's Quick Start would have had `litdiscover screen` fail with no working key) and wrongly advertised `GROQ_API_KEY` as a working "free, fast" screening backend when no code anywhere in the repo reads that variable (confirmed by grep — matches the wiki's already-flagged "Groq screening-backend gap" open question).
- **`paper/README.md` fixed**: stale `citation-dynamics` path in the directory-structure diagram corrected to `zeitgeist`.
- **Real bug found beyond docs: `lit-review-bot/paper/closed-corpus-eval/data/processed` symlink was broken** by the `citation-dynamics`→`zeitgeist` rename (resolved to a nonexistent path) — re-pointed to `../../../../zeitgeist/data/processed` and confirmed it resolves. Gitignored, so no commit needed for the fix itself, but would have silently broken anyone running the eval pipeline fresh.
- **CLAUDE.md cleanup, scoped by actual future utility, not blanket trimming:** `litdiscover/CLAUDE.md` (423 lines, actively-developed repo, dense non-derivable operational knowledge) left untouched. `deprecated-bot/CLAUDE.md` deleted outright — describes a v1 architecture in a repo confirmed inactive and kept for reference only, so it would never guide a future edit. `paper/CLAUDE.md` trimmed (~30 lines cut): removed fully-resolved historical narrative (a 2026-07-06 git-artifact cleanup, a since-fixed `refs.bib` symlink-drift story) already captured in `session-log-archive.md`, kept every still-actionable fact (migration status per script, the unresolved Fig 7 zero-misses decision, the submission-format table explaining why `drafts/archive/` holds 3 dead LaTeX variants).

</details>

**Next:** commit + push this session's changes across `citation-networks` (wiki, root README, `utils/`, `lit-review-bot/README.md`) and separately across the three nested repos that were also edited (`litdiscover/README.md`; `paper/README.md` + `paper/CLAUDE.md`; `zeitgeist/README.md`) — each is its own git repo and needs its own commit. `deprecated-bot/`'s `origin` now points at a deleted GitHub repo (`automated-lit-reviews`), so its `CLAUDE.md` deletion can be committed locally but not pushed — flag this to the user rather than silently leaving it uncommitted or attempting a push that will fail. Research-side blockers are unchanged from session 42: `synthesize`'s citation-grounding check still not run against a real project; `discovery-roadmap.md` §7 step 0 (end-to-end evaluation harness) is still the next real discovery-side work.

---

> Archived: session 42 (2026-07-14) moved to session-log-archive.md

> Archived: session 41 (2026-07-14) moved to session-log-archive.md

> Archived: session 40 (2026-07-14) moved to session-log-archive.md

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

> Archived: session 38 (2026-07-14) moved to session-log-archive.md

> Archived: session 37 (2026-07-14) moved to session-log-archive.md

> Archived: session 36 (2026-07-14) moved to session-log-archive.md

> Archived: session 35 (2026-07-13) moved to session-log-archive.md

> Archived: session 34 (2026-07-11) and earlier moved to session-log-archive.md

> Archived: sessions 33 and earlier (2026-07-10 and before) moved to session-log-archive.md
