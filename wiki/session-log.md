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

**Next:** Run `traverse` again from the enlarged included set (13→366 papers) to expand the citation graph further. Check/raise the Gemini spend cap at ai.studio/spend before attempting `extract`/`synthesize` on this project. Manually tear down the old watchdog launchd job (`~/Library/LaunchAgents/com.litdiscover.watchdog.plist` + `/tmp/litreview_watchdog*` state/logs) — code-side removal is done but host state isn't. Decide whether `mark`'s `get_project` error handling (currently mislabels any exception as "project not found") is worth fixing.

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

> Archived: sessions 29 and earlier (2026-07-07 and before) moved to session-log-archive.md
