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

> Archived: sessions 31 and earlier (2026-07-09 and before) moved to session-log-archive.md
