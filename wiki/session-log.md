# Session Log

Reverse-chronological. Start every session here, then check open-questions.md.

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

## 2026-07-14 (session 42, LitDiscover/Discovery) — Discovery folded back into litdiscover/ from its brief top-level promotion, on the reasoning that discovery+screening is LitDiscover's core identity, not a separable phase; a large concurrent user-driven repo reorg reconciled across the wiki (citation-dynamics→zeitgeist, lineages→example-comparison, litdiscover code relocated under lit-review-bot/); INDEX.md, concepts.md, research-program.md updated

**2-tier exp:** User pushed back on session 41's Discovery promotion — LitDiscover fundamentally *is* a discovery-and-screening engine, so pulling that research out into its own top-level study (mirroring Synthesis) implied it was separable when it isn't, unlike Synthesis which genuinely draws on independent (Zeitgeist) graph-analysis machinery. Folded `wiki/discovery/` back into `wiki/litdiscover/` as flat sibling files, merged `open-questions.md` back together, and fixed every cross-reference project-wide — then, in parallel, the user independently executed a much larger repo reorg (citation-dynamics/→zeitgeist/, synthesis/background/lineages/→synthesis/example-comparison/, the litdiscover codebase + reference-systems corpus + paper consolidated under a new `lit-review-bot/` shell folder) which required a full reconciliation pass across the wiki, including two apparent-deletion flags (`deep-dives.md`, `fulltext/` PDFs) that turned out to be relocations, not losses, once confirmed by directory listing.

<details>

- **Fold-back executed:** `wiki/litdiscover/discovery/roadmap.md` → `wiki/litdiscover/discovery-roadmap.md`, `wiki/litdiscover/discovery/corpus-curation-prior-art.md` → `wiki/litdiscover/corpus-curation-prior-art.md`, both as flat siblings of `research-roadmap.md`/`decisions.md`/`open-questions.md`, not a subfolder — matching the user's explicit instruction. `discovery/open-questions.md`'s content (pre-submission recall figures, Groq screening-backend gap, gold-set data-quality bug) merged back into `litdiscover/open-questions.md` in place, not left as a pointer stub. Empty `discovery/` directory removed.
- **Every cross-reference fixed, not just the moved files' own internal paths:** `research-roadmap.md`, `decisions.md` (including the §4.0 methodological-principle entry added session 41), `synthesis/representation-learning-plan.md`, and `INDEX.md` all had `../discovery/roadmap.md`-style paths rewritten to the new flat locations. `discovery-roadmap.md`'s own header rewritten to narrate the round-trip honestly (promoted → folded back, with the reasoning) rather than leaving stale "promoted to its own study" framing in place.
- **While doing this, found the user had independently reorganized much more of the repo concurrently:** `wiki/citation-dynamics/` → `wiki/zeitgeist/` (matching a local code-clone rename of the actual `citation-dynamics` repo), `wiki/synthesis/background/lineages/` → `wiki/synthesis/example-comparison/`, and — the big one — the `litdiscover` codebase moved from the repo root into a new `lit-review-bot/` shell folder alongside the 14 cloned reference-systems repos and the RLD paper draft. `wiki/INDEX.md`, `wiki/concepts.md`, and `wiki/research-program.md` had all been deleted from disk at some point in this process (later confirmed: `INDEX.md` was subsequently restored to its last-committed state by the user, the other two stayed gone) — user explicitly asked for all three to be brought current.
- **Two apparent deletions turned out to be relocations, not losses — verified rather than assumed.** `wiki/litdiscover/deep-dives.md` (the single densest research artifact in the project — 22+5+1 full method deep-dives) and `wiki/litdiscover/fulltext/`'s 9 source PDFs showed as deleted in git status with no replacement found via wiki-scoped search. Flagged explicitly in `INDEX.md` rather than silently patched over. User clarified: both live under `lit-review-bot/reference-systems/` (`deep-dives.md`, `reference-pdfs/`) — confirmed via direct directory listing before resolving the flags, not taken on faith. Fixed the two live links in `INDEX.md` to the real relative paths and removed both warning flags.
- **`INDEX.md` fully rewritten**, not just patched: removed the standalone `## Discovery` section, restored the LitDiscover table/status paragraphs to reflect the fold-back, renamed the `citation-dynamics` section to `Zeitgeist` with corrected paths, updated the Synthesis section's `example-comparison/` paths, and added a repo-layout note explaining `lit-review-bot/`'s role (shell folder for the engine + reference-systems corpus + paper) in place of the earlier "appears deleted" warning.
- **`concepts.md` and `research-program.md` refreshed.** `concepts.md`: two stale `citation-dynamics/` code/wiki path references fixed to `zeitgeist/`. `research-program.md`: the LitDiscover section's "where it stands" paragraph rewritten to state the §4.0 end-to-end-evaluation correction in plain language for a non-technical reader (the 73-100% recall headline implying sub-1%-precision finding, and why discovery+screening now have to be validated together); the Synthesis section's paragraph rewritten from "not yet built" to reflect the three now-active tracks (graph-native, embedding-native, text-native control condition) and the field-wide no-mature-synthesis-eval-standard finding.
- **Residual staleness caught on a final sweep, not assumed clean after the main pass:** `synthesis/representation-learning-plan.md` still had 5 live `background/lineages/` references (pre-dating even session 40's rename) plus a `../litdiscover/deep-dives.md` path that needed to become `../lit-review-bot/reference-systems/deep-dives.md`; `INDEX.md` had one leftover "appears deleted" sentence the first rewrite pass missed. Both caught by re-grepping after the "done" point rather than trusting the first pass.

</details>

**Next:** none of this session's changes are committed yet. The pre-existing top blocker is unchanged: `synthesize`'s citation-grounding check has still never been run against a real project. Separately, `discovery-roadmap.md` §7 step 0 (the end-to-end evaluation harness) remains the next real discovery-side work, now sitting in its permanent home in `litdiscover/` rather than a promoted study.

---

## 2026-07-14 (session 41, Discovery) — mature-eval-standard research across the 32-method corpus surfaced a real methodological flaw in Experiment 1's design; phase-discovery-roadmap.md redesigned around an end-to-end primary experiment; Discovery promoted to its own top-level wiki study

**2-tier exp:** Investigated whether the field has a mature evaluation standard for discovery/screening (found: yes for screening in isolation — CLEF TAR/SYNERGY WSS@95 — and a decades-old relative-recall standard for discovery in isolation, but nobody validates the two *together* against a citation-traversal-fed queue), which led directly to a real correction of this project's own Experiment 1 design: isolated discovery-only or screening-only recall/precision numbers aren't defensible, since precision's denominator is discovery-dependent — proven by this project's own earlier finding that a 73-100% recall headline implied 0.03-0.45% precision once anyone checked. Redesigned `phase-discovery-roadmap.md` around a new primary end-to-end experiment (§4.0), demoted the existing operator-ablation work to diagnostic status, then promoted the whole thing to `wiki/discovery/` as its own study, pulling discovery/screening-specific content out of `litdiscover/open-questions.md` and `research-roadmap.md` along the way.

<details>

- **Moved `litdiscover/litdiscover/discovery/README.md`** — a code-facing reference doc (module map, `OperatorResult` contract, all 7 operators, `GraphSource`/`S2Source`/`ClosedCorpusSource`, rate limiting, budget accounting) — from the wiki into the actual `discovery/` package directory it documents, per direct user request ("most appropriate place"). `wiki/INDEX.md` now points there instead of holding a copy.
- **Built `corpus-curation-prior-art.md`** — re-cut `deep-dives.md`'s 32 methods (27 + 5-entry verification cohort) around one question: how does each system discover *and screen* its corpus? Comparison table (discovery mechanism / screening mechanism / stopping criterion / screening validated?), grouped analysis, and a "what this means for LitDiscover" section. Found only 2 of 32 systems (SWIFT-Active Screener, SocLitGen) have anything like a formal stopping criterion at all.
- **User pressure-tested the eval-standard framing across several turns**, each correcting an overclaim: first that no mature eval standard for discovery exists at all (wrong — relative-recall-against-known-item-gold-set is a decades-old systematic-review-methodology standard, just unused by the LLM-native survey-generation cohort); then confirmed via live web search that no independent relative-recall study exists for AutoSurvey/LitLLM/SurveyX specifically, but surfaced a brand-new relevant benchmark (SurveyLens, arXiv 2602.11238) along the way.
- **Dispatched a subagent to fetch SurveyLens's full text and add a `deep-dives.md` entry** in the established 6-bullet template, with a provenance note (found via eval-standard research, not the original 366-paper mining pass). Its headline finding — reference quality is weak across all 11 systems/3 paradigms tested — is a direct, benchmark-backed differentiation angle for LitDiscover.
- **The real methodological turn:** user's own observation that "discovery and screening go hand in hand... precision and recall are two sides of the same coin" was correct and corrected a suggestion I'd just made (benchmarking `screen_batch()` against CLEF TAR/SYNERGY directly) — that would validate the classifier against someone else's candidate pool, not LitDiscover's own discovery-fed queue. This is the same failure mode session 38 already found in the original system's own 73-100% recall headline (0.03-0.45% implied precision, never screened) — now generalized into an explicit principle.
- **Redesigned `phase-discovery-roadmap.md` around it, not a full rewrite.** Kept §1 (implementation audit), §2 (prior-art survey), §3 (the bet), §5 (sim-vs-production gap) intact — still accurate. Inserted new §4.0: the methodological principle, the primary End-to-End Corpus Curation experiment design (run the real staged pipeline against the 3 live surveys, score the actual `included` set — not raw candidates — against real bibliographies, budget-capped, funnel reported), and a 6-item "ironclad/defensible" checklist. §4.1-§4.11 (existing operator-ablation work) explicitly demoted to diagnostic-decomposition status, not deleted — still real, reusable, just never citable alone. No section renumbering, so every existing `§4.x` cross-reference elsewhere in the wiki still resolves. §6 and §7 updated to match (§7 gets a new step 0: build the end-to-end harness first).
- **Promoted the whole thing to `wiki/discovery/`** (mirroring the earlier Synthesis promotion), per direct user request — a full study in its own right now that §4.0 turned it from "one implementation detail" into a rigorous investigation. `git mv`'d `phase-discovery-roadmap.md`→`discovery/roadmap.md` and `corpus-curation-prior-art.md`→`discovery/background/`; fixed every cross-reference found across the wiki (`deep-dives.md`, `decisions.md`, `research-roadmap.md`, `synthesis/representation-learning-plan.md`, `INDEX.md`) except `session-log.md`'s own historical entries, left alone on purpose.
- **Pulled discovery/screening-specific content out of `litdiscover/open-questions.md`** into a new `discovery/open-questions.md`: the pre-submission recall-figure checklist (Q1-Q5, Q9-Q10, Q15 — Q1 now flagged stale against §4.0, not just "resolved"), the Groq screening-backend-fallback gap, and the full gold-set data-quality bug writeup (found 2026-07-14 earlier this same day, root-caused to S2's own `/references` endpoint linking malformed records, fixed by manual removal — Ge21-HSS 202→200, K17-RGC 56→52). Left a general-engine-only trimmed version behind with pointers.
- **Concurrent-session awareness:** a separate session was actively restructuring `wiki/synthesis/` (lineages moved to `synthesis/background/lineages/`, `phase-representation-roadmap.md`→`synthesis/representation-learning-plan.md`, new `synthesis/roadmap.md`/`eval-standard-gap.md`) throughout this session — turned out to be session 40 above, wrapped concurrently. Re-read files before each edit that touched shared state (`INDEX.md`, `phase-discovery-roadmap.md`) to avoid clobbering; all edits applied cleanly with no lost-update incidents this time (contrast session 38's mid-session clobber).

</details>

**Next:** §7 step 0 in `discovery/roadmap.md` — build the end-to-end harness (drives `traverse_once`/`screen_pending` per live survey, scores the real `included` set against corrected gold-sets, reports the funnel + budget-capped recall/precision/F1). This supersedes recomputing the old isolated discovery-recall numbers against the corrected gold-sets in isolation — no point fixing a number §4.0 is about to replace. Unchanged blocker elsewhere: `synthesize`'s citation-grounding check still not run against a real project.

---

## 2026-07-14 (session 40, Synthesis) — Reference-implementation survey built across 14 cloned repos (code-vs-paper fidelity audit), synthesis-eval-standard gap documented, wiki/synthesis/ refactored into a single roadmap + three protocol tracks, K17-RGC gold set verified

**2-tier exp:** Conversation moved from a conceptual discussion of literature-review methodology (screening vs. extraction vs. synthesis, thematic vs. narrative-lineage synthesis) into a real code-grounded audit: cloned 14 reference literature-review-automation repos, dispatched parallel agents to extract each system's actual synthesis mechanism and cross-check it against both `deep-dives.md`'s paper-text summaries and each paper's own reported eval — found several concrete paper-vs-code fidelity gaps (SurveyX's "attribute forest" doesn't exist in code, SurveyGen's re-ranking formula doesn't match its stated coefficients, InteractiveSurvey's clustering variable is named `hdbscan_model` but instantiates `AgglomerativeClustering`) — then used that plus a documented "no mature synthesis-eval standard exists" finding to fully refactor `wiki/synthesis/` from two stalled, overlapping planning docs into one entry-point roadmap governing three disjoint corpus-structuring protocols, and closed by verifying the Q-SYNTH pipeline's first blocking prerequisite (the K17-RGC gold set) actually exists.

<details>

- **Conceptual groundwork, not yet code:** walked through what a full literature review requires beyond source collection (screening stages, quality appraisal, extraction, synthesis, PRISMA reporting, gap analysis), then narrowed into synthesis-method taxonomy — thematic clustering (undirected, symmetric) vs. narrative/lineage construction (directed graph, asymmetric "extends/contradicts") — and why screening must precede extraction for cost reasons (screening is a cheap high-recall filter; extraction is the expensive structured pull that shouldn't run on papers likely to be excluded).
- **Corrected my own scope creep mid-session:** when asked to discuss "reference systems" evaluation, I'd pulled in 8 uncloned paper-only entries alongside the actually-cloned repos without flagging the mismatch — user caught it directly ("did you miss the others when you first surfaced these to be cloned?"). Root cause: my original clone-candidate search only grepped `deep-dives.md` for the literal words "github"/"open source," missing papers whose deep-dive text just didn't happen to mention code availability.
- **Web-searched and cloned 6 more repos** (SciReviewGen, LitLLM v1+v2, SurveyX, SurveyGen, SurveyGen-I) plus RobotSearch (found via search after the original clone list missed its actual `ijmarshall/robotsearch` GitHub) — 14 total in `lit-review/reference-systems/`. LiRA and Meow searched but have no public repo (Meow has a HuggingFace dataset only).
- **6 parallel Explore agents** extracted each system's actual synthesis mechanism with file:line citations, cross-checked against paper-reported eval/results pulled from `deep-dives.md`. Concrete findings: AutoSurvey's widely-reused citation-quality metric is a post-hoc LLM-judge check with only ρ≈0.54 correlation to human judgment, a ceiling every downstream adopter (LiRA, SurveyX) inherits without re-validating; SciReviewGen wins on ROUGE but *loses* the human side-by-side (68.9% preferred ground truth vs. 22.2% preferred generated); PROMPTHEUS and InteractiveSurvey both cleanly implement one-cluster-to-one-section synthesis, the strongest concrete precedent found for a Method 1 rebuild.
- **Wrote `background/eval-standard-gap.md`**: no mature synthesis-quality eval standard exists in this literature — no shared benchmark, no validated per-axis metric for the "synthesis"/"critical analysis" construct specifically (the two systems that measure it separately, SurveyGen-I and SurveyX, never validate that sub-score against human judgment independently from the aggregate). Direct positioning material for the Synthesis paper's own related-work section.
- **Assessed honestly, when asked, whether `wiki/synthesis/` amounted to a rigorous investigation: no.** Distinguished rigorous *scoping* (falsifiable hypotheses, clear test case, defined success criteria — present) from rigorous *investigation* (execution + results — absent; Q-SYNTH had zero code written, zero prerequisites checked).
- **Refactored `wiki/synthesis/` end-to-end** given that assessment: merged `experiment-spec.md` + `methods-comparison.md` (overlapping, both unstarted) into `q-synth-plan.md`; pulled `litdiscover/phase-representation-roadmap.md` in as a third parallel track (`representation-learning-plan.md`) on the user's own instinct that it was "a subroutine alternative" to the other two; moved `litdiscover/lineages/` into `background/lineages/` as the LLM-text-native control condition; wrote `roadmap.md` as the single entry point (goal, 3-track status table, per-track next action, what "rigor" means before any track counts as a result). Corrected an overstated claim of my own along the way — `lineages/`'s explicit-citation-graph work does use real graph topology (connected components via union-find), just far shallower than Q-SYNTH's Leiden/power-law/embedding stack, not "no graph topology" as I'd first said.
- **User made parallel manual moves** (`reference-implementation-survey.md` → `background/` directly, `related-work-figure-mockup.md` → `lit-review/robust-literature-discovery/drafts/`) and separately began an equivalent `discovery/` restructure of `litdiscover/`'s own roadmap files — fixed cross-reference paths broken by the two moves I was told about; flagged (not fixed) that `INDEX.md`'s LitDiscover table still points at pre-move `discovery/` paths, since the user said they'd handle that restructure themselves.
- **Verified the K17-RGC gold set actually exists** — not at `q-synth-plan.md`'s guessed path (`projects/kahle-simplicial-geometry/`, which doesn't exist), but at `live-survey-eval/data/gold-sets/K17-RGC_gold.json`: 52 entries (matches the already-logged 56→52 data-quality fix), all with S2 IDs, 49/52 with DOIs directly. Updated `q-synth-plan.md`'s and `roadmap.md`'s blocking-prerequisites/next-action accordingly — first blocker now cleared.

</details>

**Next:** build the K17-RGC 1-hop subgraph from the verified gold set and run Leiden once — cheaper than waiting on the still-unmet planner/architect sprint-planning prerequisites, and would give a first read on whether Q-SYNTH's central hypothesis is worth formalizing further. Separately, still open: LitDiscover's own pre-existing top blocker (running `litdiscover synthesize`'s citation-grounding check against a real project) remains unaddressed and now several sessions old.

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
