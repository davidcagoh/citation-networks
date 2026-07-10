# LitDiscover — Design Decisions

Choices that have already been made and why. Read this before changing any parameter.

---

## Algorithm Parameters

### N_ROUNDS = 2 (not 4)
**Decision date:** ~2026-04-06. Reviewed 2026-04-10.
**Why:** `n-rounds-extension.md` shows round 1 does 85–98% of the work; round 2 adds modest insurance. The hyperparameter sweep (script 08, k_escape=5, yield=0.05, pareto80) shows:

| n_rounds | S1     | S2     | S3     |
|----------|--------|--------|--------|
| 1        | 84.9%  | 97.7%  | 94.3%  |
| 2        | 86.9%  | 98.1%  | 95.3%  |
| 3        | 89.3%  | 98.1%  | 95.6%  |

Round 3 adds 2.4pp for S1 but negligible for S2/S3. Keep n_rounds=2 as canonical. S1's residual gap at 89% is explained by structural miss analysis (§6), not insufficient rounds.

**Open question:** n_rounds=3 as an optional robustness sweep would show S1 reaching ~90–92%.
**Implication:** Script 04b (k=1–5,10) is the canonical experiment, not script 04 (k=5/10/20/50).

### PARETO_P = 80 (suppress top 20% out-degree in forward traversal — simulation only)
**Decision date:** Set in original architecture. Confirmed 2026-04-10.
**Why:** Under yield stopping (the actual operating condition), Pareto threshold significantly affects recall:

| pareto_p | S1 r2  | S2 r2  | S3 r2  |
|----------|--------|--------|--------|
| 50       | 80.4%  | 93.5%  | 91.5%  |
| 70       | 86.6%  | 96.8%  | 94.6%  |
| 80       | 86.9%  | 98.1%  | 95.3%  |
| 90       | 89.0%  | 98.1%  | 96.4%  |
| 95       | 89.7%  | 98.6%  | 96.4%  |
| none     | 100%   | 100%   | 100%   |

(k_escape=5, yield=0.05, n_rounds=2)

**CRITICAL DISTINCTION:** At full depth without yield stopping (fig3), ALL pareto values reach 100% recall. Under yield stopping (operational), the filter genuinely trades recall for corpus size. Fig3 and fig8 tell different stories and both are correct — different operating conditions. The paper must make this explicit.

**SETTLED — what the filter actually does:**
- **APS simulation (scripts 03, 04b, 05, 08)**: filters FORWARD CANDIDATES (citers) by their own **out-degree**. High out-degree citer = survey-like → removed.
- **Production (`traverse.py`)**: filters FRONTIER PAPERS by their **in-degree** (citation_count). Highly-cited frontier paper → skip forward traversal entirely.

The paper should describe the production semantics (in-degree of frontier paper) as the algorithm, and note that the APS simulation approximates it via out-degree of forward candidates. See `simulation-vs-production.md` for full discussion.

### YIELD_THRESHOLD = 0.05
**Why:** 5% new gold / new nodes means 95% of work is wasted. Practical stopping point.
**Implication:** Within-round stopping (yield < 5%) is separate from between-round stopping (fixed N_ROUNDS=2).

### K_ESCAPE = 20
**Why:** 20 new seeds per escape hatch round is enough to restart traversal in the missed region without exploding cost.

### SEED_SIZES = [1, 2, 3, 4, 5, 10]
**Decision date:** ~2026-04-06 (changed from [5, 10, 20, 50])
**Why:** User-facing realism. Most users provide 1–5 seeds. k=10 is the full-coverage anchor.

---

## Experiment Design

### Gold set = bibliography of the survey paper (not the survey paper itself)
**Why:** The survey DOI is the entry point, but the gold set is what the survey cites. The survey DOI is never in its own gold set.
**Implication:** tp_refs at depth 0 = 0 if seeding from survey DOI alone.

### Overlap metric (not "recall")
**Decision date:** ~2026-04-06
**Why:** "Recall" implies you know what you're looking for. "Overlap" (|visited ∩ gold| / |gold|) is the correct term for this setting.
**Status:** ⚠️ Scripts and figures still use "recall" everywhere. Paper text should use "overlap." Scripts can stay as-is.

### APS corpus only (no arXiv, no non-physics)
**Why:** APS provides a complete, closed citation graph. Non-APS papers would break the closed-world assumption needed for exact overlap measurement.
**Important:** 100% of gold refs for all three surveys ARE in the APS corpus. No corpus ceiling — all misses are algorithm failures.

---

## Paper Structure

### Related work moved to §2 (not §6)
**Why:** The argument depends on establishing what doesn't work before showing what does.

### Miss analysis placed BEFORE main results (§6 before §8)
**Why:** Primes the reader to understand the residual gap before seeing the 89–98% headline numbers.

### APS validation reframed as §8, live experiments as §7
**Why:** APS is controlled benchmark (closed corpus, known gold). Live experiments (Kahle + Galesic) are the operational claim. Paper is primarily about a usable system, so live comes first.

---

## Fig9 dropped entirely (2026-04-10)
**Decision:** Remove fig9a–d from the paper. §6 space repurposed for live experiment results.
- **fig9b:** Vacuous — depth-2 screen yield (0.3–1.5%) falls below even the lowest tested yield threshold (1%). One-sentence methods note sufficient.
- **fig9a:** Covered by fig8c.
- **fig9c:** Covered by fig4 (stacked bar showing round contribution).
- **fig9d:** Covered by fig8b (depth×pareto heatmap).

## Yield threshold = safety valve, not tuning knob (2026-04-10)
**Decision:** Yield threshold gets one sentence in methods, no standalone claim or figure.
**Wording:** "We set yield threshold at 5%; any value above ~1% produces identical results for these survey types, as depth-2 screen yield (0.3–1.5%) falls below any practical threshold."

---

## Venue

| Venue | Type | Fit | Notes |
|---|---|---|---|
| **ICASR 2026** | Conference/Workshop | ⭐⭐⭐⭐ Best | Dedicated to automated systematic reviews. 2025 was July Potsdam. Watch for 2026 call. |
| **ALTARS 2026/2027** | Workshop @ TheWebConf | ⭐⭐⭐ Very Good | AI in Technology-Assisted Review. April 2026 Copenhagen may be past deadline. |
| **JCDL 2026/2027** | Conference | ⭐⭐⭐ Good | Digital libraries + IR; systematic review automation in scope. |
| **JASIST** | Journal | ⭐⭐⭐ Good | Rolling submission; broad info-science scope. Reformatted 2026-07-06, superseded by TOIS same day. |
| **CIKM / SIGIR 2026** | Conference | ⭐⭐ OK | More competitive; needs stronger retrieval theory framing. |
| **ACM TOIS** | Journal | ⭐⭐⭐⭐ Best on paper | IR-specific scope, exact match, 24% acceptance, ~2mo/review round, no mandatory APC — but enforces a ~20-page minimum (excl. refs) that this 12-page paper doesn't meet. Abandoned 2026-07-06. |
| **Information Processing & Management** | Journal | ⭐⭐⭐⭐ **Active target** | Strong IR scope, and better content fit than JASIST/TOIS: IP&M explicitly spans both system-level (algorithmic) and human-centered research, matching this paper's systems-with-empirical-validation framing. No page-length floor. Weaker/noisier turnaround data (~5.9mo, low SciRev satisfaction) but that's normal journal latency, not a red flag specific to this venue. |
| **Research Synthesis Methods** | Journal | ⭐⭐⭐⭐ Very Good (topically) | Ruled out: mandatory $3,400 APC, no waiver available. |

**Decision (2026-04-21):** Submitting to **JCDL 2026** (June 30 deadline). ICASR 2026 call not yet live; JCDL deadline is concrete and the fit is strong. EasyChair record filed.

**Update (2026-07-06): JCDL 2026 deadline missed — not submitted.** EasyChair record existed but paper was never sent by June 30. Rechecked venue landscape same day:
- **ALTARS 2026** deadline was Jan 23, 2026 — also already passed (workshop itself is June 30, 2026, Dubai, co-located w/ TheWebConf).
- **ICASR 2026** — no event announced yet (2025 ran July; possible 2026 announcement could still land later this year — watch for it).
- **JASIST** — journal, rolling submission, no fixed deadline. Only venue currently open.
- **JCDL 2027** — next-cycle fallback, ~11 months out.

**Decision (2026-07-06): targeting JASIST.** Reformatted paper from ACM sigconf to plain `article` class — see `lit-review/robust-literature-discovery/paper-drafts/archive/jasist-submission/litdiscover_jasist.tex`. Compiles clean (0 errors, 0 undefined refs), 21 pages double-spaced, ~5200 words body (well under 7,000-word JASIST cap). Solo-authored: dropped Xiaobai Sun as second author (no contribution to this paper; her work is cited where relevant instead). Still open: cover letter, ORCID already have, ScholarOne submission, GenAI-use declaration required by JASIST.

**Update (2026-07-06, same day): switched from JASIST to ACM TOIS.** Compared JASIST against three other IR/methods venues:
- **ACM TOIS** — scope is a near-exact match ("new principled IR models/algorithms with sound empirical validation"). Official metrics: 24% acceptance rate for in-scope work, median ~2 months per review round. No mandatory APC (hybrid journal).
- **Information Processing & Management** — also strong IR scope fit, but weaker data: ~5.9 months to first decision and 2.0/5 author satisfaction on SciRev (small self-reported sample, so noisy), including a report of same-week desk rejection without review. No mandatory APC.
- **Research Synthesis Methods** — tightest topical match (explicitly names "literature retrieval and information science" in scope) but fully open-access with a **mandatory $3,400 USD APC**, no waiver unless affiliated with a specific list of Dutch institutions. Ruled out on cost.
- **Scientometrics / Journal of Informetrics** — weaker fit, bibliometrics/research-evaluation focused rather than IR-systems focused.

**Decision:** TOIS — best-documented acceptance odds and turnaround, tightest scope match, no forced OA cost. Reformatted again: `paper-drafts/archive/tois-submission/litdiscover_tois.tex`, `\documentclass[manuscript,review,anonymous]{acmart}` (same acmart engine as the old JCDL draft, just `sigconf`→`manuscript` plus `\acmJournal{TOIS}` instead of `\acmConference{}`). Compiles clean, 12 pages, double-anonymous review (author identity hidden from reviewers per ACM journal policy). JASIST draft kept on disk but not the active target.

**Update (2026-07-06, later same day): TOIS abandoned — 20-page minimum.** ScholarOne's TOIS submission form states a minimum manuscript length of ~20 pages excluding references. Our paper is a focused 12-page contribution; hitting 20+ pages genuinely would mean substantial new content (deeper related work, more experiments/ablations), not reformatting. Chose to switch venue rather than pad the paper.

**Decision: targeting Information Processing & Management.** Reconsidered fit directly (not just acceptance/turnaround stats this time): IP&M explicitly positions itself around *both* system-level and human-centered research, meaning it's built to hold a "new algorithm/architecture, validated empirically" paper — a tighter match to LitDiscover's actual content than JASIST's more behavioral/sociotechnical lean. Also has no page-length floor, so no repeat of the TOIS problem. IP&M's own Guide for Authors specifies **APA author-date citations**, not the numbered Vancouver style generically assumed for Elsevier journals — confirmed this before reformatting to avoid the same kind of surprise. Reformatted using elsarticle's `authoryear` class option (critical: omitting it silently defaults to numeric citations even with `\citet`/`\citep` in the source — caught by checking rendered PDF text, not just compile success) and `elsarticle-harv` bibliography style. Added the required CRediT authorship statement and a GenAI-use declaration. Compiles clean, 19 pages, 0 errors. Draft: `paper-drafts/ipm-submission/litdiscover_ipm.tex`.

---

## Naming: LitDiscover (not "LitReview v2")
**Decision date:** ~2026-04-06
**Why:** "LitReview" sounds like the output (a review). "LitDiscover" is the process (discovery).
**Status:** ✅ Renamed throughout — pyproject.toml, CLI, and paper draft.

**Update (2026-07-06): naming completed end-to-end.** Internal package `litreview2` → `litdiscover`, and the GitHub repo itself renamed `automated-lit-reviews-v2` → `litdiscover` (old URL auto-redirects). Reasoning: the `-v2` suffix only made sense internally (v1 is archived, no outside user knows the lineage), and it was inconsistent with the already-renamed package/CLI. PyPI distribution name is also `litdiscover` (matches import name — no split like beautifulsoup4/bs4).

## Engine rework: staged-by-default workflow, autopilot opt-in (2026-07-09)

**Decision:** Flip `run`'s default behavior. Today's fully-unattended traverse→screen→repeat
loop becomes an explicit opt-in (`[loop] mode = "autopilot"` in `project.toml`); the new default
(`mode = "staged"`, or the field simply omitted) breaks the pipeline into individually-triggered
stages that each write an inspectable artifact before the next stage runs.

**Why:** Driving litdiscover from a different project (`adaptive-learner`'s WAILS 2026
related-work search, 2026-07-09 — see `open-questions.md`'s "Engine feature requests" section)
surfaced that the automated loop's failure mode (silent 0%-yield retry burning ~13 rounds after a
Gemini spend-cap error) and its screening quality (David: "litdiscover's LLMs aren't that smart")
are the same underlying problem: nothing gates the loop except the loop itself. What actually
worked in that session was a human+agent (Claude, in a chat session) eyeballing a keyword-prefiltered
candidate list together (2017 → 135 candidates, caught ~60 false positives an LLM screen likely
would've missed) — genuinely closer to HITL-with-an-agent than automated screening. Also surfaced
a stronger idea: once some papers are included, mine the closest-match paper's own Related Work
section for framing/grouping and unaddressed context, and use that to hand-refine criteria/keywords
— something pure citation-graph traversal structurally can't recover.

**What changes:**
- `traverse` and `screen` become individually-callable CLI commands (currently interleaved inside
  `loop.py`'s state machine) — `run` under `mode = "staged"` does one traversal cycle and stops.
- New `litdiscover prefilter <slug>` — formalizes the keyword/regex triage validated manually in
  the WAILS session (auto-derives terms from `project.toml`'s `criteria`), ranks by citation
  count, writes a skimmable `<slug>_candidates.md` sized for a chat-session read-through.
- New `litdiscover mark <slug> --include/--exclude/--uncertain <ids> [--note]` — the write-back
  primitive staged mode needs, since `screen/llm.py` is currently the *only* code path that sets
  `papers.status`. Writes to `screening_log` with a new `screener_type` column
  (`'llm' | 'human' | 'prefilter'`) so mixed-mode history stays legible in `verify`/`forward-cites`
  reports.
- New `litdiscover related-work-mine <paper_id>` (already speculative in `open-questions.md`,
  now promoted to the core workflow) — fetches full text where available, extracts just the
  Related Work section. "Closest match" ranking reuses `synthesize`'s existing embedding infra
  (`gemini-embedding-001`), not a new pipeline.
- Autopilot mode's existing automatic criteria-refinement (LLM-proposed, cosine-similarity-guarded)
  stays exactly as-is for `mode = "autopilot"` projects. Staged mode skips it entirely — the
  related-work-mining step replaces it there, and running both would mean the LLM silently
  rewrites criteria out from under a change just made by hand.
- No yield-gating machinery in staged mode — `traverse` just prints a one-line cycle-yield summary
  and exits; the human decides whether another cycle is worth it.
- **No migration needed for existing autopilot-mode projects** — the three watchdog-rotation
  projects (`self-supervised-pretraining`, `automated-lit-review-methodology`, and whichever third
  was in `watchdog.py`'s hardcoded rotation) are being scrapped outright rather than flagged
  `mode = "autopilot"`, since they're stale and can be redone from scratch if ever needed. The
  `launchd` watchdog job itself (`com.litdiscover.watchdog`) is being unloaded/removed as part of
  this change — nothing left for it to poll.

**Status:** ✅ Implemented and merged to `main` same day (2026-07-09), via `planner` + `tdd-guide`
agents, 8 commits, 174 tests passing. `CLAUDE.md`/`README.md` rewritten to describe the new
staged-default/autopilot-opt-in architecture. `screening_log`'s `screener_type`/`note`/`mode`
migration applied directly to the live `litreview-v2` Supabase project. Not yet republished to
PyPI (still v2.0.0). Host-side launchd plist/state teardown still needs to be done manually
(code-side watchdog removal is done, but `~/Library/LaunchAgents/com.litdiscover.watchdog.plist`
and `/tmp/litreview_watchdog*` files are outside the repo and weren't touched).

---

## Distribution: published to PyPI as `litdiscover` (2026-07-06)
**Why:** Goal was "make LitDiscover available for seamless use." Considered three tiers: (1) pip-installable CLI with user-provided Supabase + API keys, (2) a hosted multi-tenant API, (3) do nothing beyond git clone. Chose (1) — the schema is single-tenant (no `user_id`/auth layer), so a hosted service would need real product-engineering (multi-tenancy, billing, rate limiting), a different project from "package the existing engine."
**Status:** ✅ Live at `pypi.org/project/litdiscover/2.0.0/`. `v2.0.0` tagged. `robust-literature-discovery` deliberately NOT renamed or merged into this repo — it's named after the paper (correct convention for a reproducibility repo) and serves a different audience (public, frozen-at-submission, no credentials) than the engine (private, evolving, credentialed).
**Also fixed in this pass:** `citation-dynamics` promoted to its own repo (`github.com/davidcagoh/citation-dynamics`) for the same reason — `citation-networks` should be a thin umbrella, not a mixed-tracking-model monorepo. And a genuinely broken `launchd` watchdog job (stale path, failing silently every 10 min) was caught and fixed while investigating a doc-staleness flag — see session-log session 28.

---

## Tier 1/2 close-hit papers: pull full PDFs, not abstracts-only (2026-07-10)
**Why:** Full text gives an independent read to check Gemini's screening/relevance judgments against, rather than abstracts-only where the LLM's own summary is the only signal available.
**Status:** Decided. Start with 3 of the 7 Tier 1/2 papers — enough to benchmark against before deciding whether to pull the rest.
