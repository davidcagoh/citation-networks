# Discovery — phase roadmap

**Split out from `research-roadmap.md`** (2026-07-14) — discovery had grown to five subsections
and was crowding out Extraction/Synthesis in the parent doc. This file owns everything about the
discovery phase specifically; `research-roadmap.md` keeps the cross-stage overview and links here.

**§4 rewritten 2026-07-14** as a full IR-methodology experimental design (Cranfield gold standard,
operator-based ablation, ordering, budget-normalized Pareto curves, paired significance testing) —
supersedes the earlier flat "compare some methods" sketch.

**§4 execution (Experiment 1) paused, same day** — real findings, mixed/negative results, see the
⏸ box at the top of §4 for the summary before reading that section in full.

**§1 rewritten 2026-07-14 (session 39)** from an actual line-by-line read of the production
engine and all 15 evaluation scripts (prompted by wanting to redo Experiment 1 differently) —
supersedes the earlier `background.md`-derived prose. Finds the eval code is three tiers of
production-integration, not one uniform "hand-written simulation" as previously stated: the
closed-corpus track (11 scripts) is zero-integration by design (an online/offline mismatch, not
an oversight); `live-survey-eval/09` is zero-integration because it predates the operator
decomposition (a bounded refactor); `live-survey-eval/10` is genuinely production-integrated,
and 11/12 build on it correctly but through a non-standard sibling-script-loading mechanism.

---

## 1. What's implemented today

**Rewritten 2026-07-14 (session 39)** from an actual line-by-line read of `litdiscover/litdiscover/`
(all of `discovery/`, `core/loop.py`, `core/stages.py`) and all 15 evaluation scripts in
`lit-review/robust-literature-discovery/{closed-corpus-eval,live-survey-eval}/scripts/` — not
carried over from `background.md` prose. The engine has moved on since that prose was written
(`intake/` → `discovery/`, 5 new operators shipped) and the eval-script picture it painted
("both eval tracks are hand-written simulations... not a harness that drives `traverse.py`
itself") turns out to be true of only *some* of the eval code, not all of it — the actual
picture is three distinct tiers of production-integration, detailed in §1.2.

### 1.1 The production engine (`litdiscover/discovery/`)

Seven operators, all sharing one contract — `operator(paper_set, ...) -> OperatorResult`
(`candidates`, `edges`, `stats`), defined once in `traverse.py` and imported by `operators.py`:

- **`backward_traversal_operator`** (`traverse.py`) — PDF-first reference extraction
  (PyMuPDF regex over the References section for arXiv IDs / DOIs, parallelised across
  `pdf_workers` threads) with a single S2 `/paper/batch` enrichment call per paper
  (`s2_client.batch_enrich_refs`), falling back to S2 `/references`
  (`s2_client.paginate_edges`) only when PDF extraction yields nothing.
- **`forward_traversal_operator`** (`traverse.py`) — S2 `/citations` only (PDFs can't provide
  this by definition). Takes an explicit `hub_threshold` float; defaults to `inf` (unfiltered) —
  the hub filter is a separate, composable step, not fused in.
- **`pareto_hub_threshold`** (`traverse.py`) — not an operator itself (produces no candidates); a
  modifier. Computes a Gini coefficient over the frontier's citation counts and picks an
  *adaptive* percentile via `adaptive_hub_percentile()`: Gini > 0.70 (power-law) → strict 80th
  pct; 0.50–0.70 → relax to 90th; < 0.50 (uniform/niche) → relax to 95th. `traverse()` (the
  public orchestrator) always calibrates this before running the forward operator.
- **`author_expansion_operator`, `venue_expansion_operator`, `recency_search_operator`,
  `embedding_search_operator`, `co_citation_operator`** (`operators.py`, all added 2026-07-14
  via TDD) — five operators beyond citation traversal. All derive their query from the current
  paper set itself (recurring authors / venues / S2's own SPECTER-embedding recommendations /
  co-citation via citers'-references) except `recency_search_operator`, which necessarily takes
  an explicit caller-supplied query string, since its entire purpose is reaching papers with no
  graph or authorship connection to the current set yet.
- **`s2_client.py`** — the shared infrastructure every operator above (and `pdf_worker.py`,
  `search.py`, `verify.py`, `forward_cites.py`) calls through: one process-wide rate-limit lock
  (`_s2_wait`, `_S2_MIN_INTERVAL = 1.2s`, widened from 1.05s on 2026-07-14 after live 429s under
  the tighter margin), `batch_enrich_refs`, `paginate_edges`, `_normalise_s2`, and a shared
  `_s2_call_count` counter that `budget.py` reads as its cost source of truth.
- **`budget.py`** — `run_with_cost(operator_fn, *args, **kwargs)` measures any operator
  externally (S2-call delta, wall-clock time, candidates returned) with zero changes to the
  operator itself; `recall_per_call()` is pure arithmetic, gold-matching is the caller's job.
- **Supporting, non-operator discovery code:** `search.py` (S2 `/paper/search`, used both as
  the cold-start query and as autopilot's "Escape Hatch"), `pdf_worker.py` (background PDF→ref
  extraction daemon feeding the pending queue during autopilot screening), `verify.py`
  (post-hoc title-drift check against S2, VERIFIED/UNCERTAIN/NOT_FOUND), `forward_cites.py`
  (on-demand "what's citing my included set" check), `relwork.py` (staged workflow's
  human-in-the-loop substitute for autopilot's automatic criteria refinement).
- **Orchestration:** `core/loop.py::run()` is autopilot's yield-gated state machine (SEARCH →
  SCREEN → TRAVERSE → STABLE, described in full in CLAUDE.md); `core/stages.py` holds the
  reusable pipeline stages (`_do_traverse`, `apply_screen_decisions`, `traverse_once`,
  `screen_pending`) both autopilot and the staged CLI commands call into. `traverse()` itself
  (`traverse.py`'s public function) is a thin orchestrator: calibrate the hub threshold, run
  backward + forward, merge — its signature and return shape are a stable contract `core/stages.py`
  and existing tests depend on.

### 1.2 The evaluation code: three tiers of production-integration, not one

The 15 scripts across `closed-corpus-eval/scripts/{eval,sweep}/` (11 scripts) and
`live-survey-eval/scripts/` (4 scripts) do **not** integrate with the production engine
uniformly. Reading them in full shows three distinct tiers:

**Tier 0 — `closed-corpus-eval/` (all 11 scripts): zero litdiscover imports, by design.**
Every script — `eval/01_extract_ground_truth.py` through `eval/06_publication_figures.py`,
`sweep/03b_depth_pareto_grid.py` through `sweep/08_hyperparameter_sweep.py` — is fully
standalone. None import anything from the `litdiscover` package, and there is no shared helper
module between the 11 scripts either: each one that needs a traversal re-derives the
`cites`/`cited_by` adjacency index from the raw APS citation CSV and re-implements the
bidirectional-BFS-plus-Pareto-filter-plus-yield-stop loop from scratch. That loop appears **six
times** with small, undocumented drift between copies: `eval/03_traversal_simulation.py`
(4 strategy variants), `eval/04b_cold_start_lowseed.py` (the paper's canonical experiment),
`eval/05_miss_analysis.py`, `sweep/04_cold_start_simulation.py` (superseded by 04b, but never
deleted — its output was never regenerated after 04b changed the seed-size/round-count scope,
which silently broke `sweep/07_elbow_analysis.py`'s dependency on it), `sweep/07_rounds_sweep.py`,
`sweep/08_hyperparameter_sweep.py`. `04b`'s own docstring is explicit that this is intentional,
not an oversight: production filters frontier papers by in-degree *before* forward traversal
against a live, heterogeneous, cross-disciplinary S2 corpus; these scripts filter by out-degree
percentile on already-collected citers *after* the fact, against a closed, single-discipline
(APS physics) corpus — a different filtering point and a different distributional assumption,
chosen deliberately for the closed-corpus regime.

Secondary evidence of the same "answers the strategy question, not the code-path question"
character: the Pareto-percentile grid is enumerated four different, mutually inconsistent ways
across the 11 scripts (`eval/03`'s 8 values, `sweep/03b`'s 8-plus-`"bidir"`,
`sweep/08`'s 11-value grid including 60/95/`None`); "no filter" is encoded three different ways
(dict key `"bidir"`, Python `None`, and the sentinel integer `999` in `sweep/08`'s output CSV);
the canonical seed size k=5 used in `04b`/`05`/`08` is silently k=20 in
`sweep/07_rounds_sweep.py`; and the survey color palette is redeclared with inconsistent
variable names and occasionally inconsistent hex values in six separate scripts.

**Tier 1 — `live-survey-eval/09_live_validation.py`: also zero litdiscover imports, but for a
different reason — it predates the 2026-07-14 operator-decomposition refactor.** 1057 lines,
fully standalone: its own S2 client (own `_s2_wait` at `_S2_MIN_INTERVAL=1.05` vs. production's
now-1.2s; own `S2_FIELDS` that omits `abstract`), its own disk cache, its own
`bidir_pareto_traversal_live` (a **flat, non-adaptive** `PARETO_P=80` with no Gini calibration —
production's `adaptive_hub_percentile` can relax to 90th/95th for low-Gini corpora, 09 never
does), and backward traversal that is S2-`/references`-only (no PDF-first extraction — a real
semantic divergence from `backward_traversal_operator`, not just duplicated code). It also
builds a two-tier gold-matching scheme (exact S2-ID, then rapidfuzz fuzzy-title fallback,
`FUZZY_THRESHOLD=92`) that reports both `recall_exact` and `recall_upper_bound` — except
`run_survey()`'s actual output-writing path never calls the function that does the fuzzy tier
(`compute_recall()`); it sets `recall_upper_bound = recall_exact` directly (line ~1015) with a
stale comment claiming otherwise. The fuzzy-matching capability exists in the file and is dead
in practice. One more silent gap: `data/seeds/K17-RGC_seeds.json` has only 1 of the 3 seeds
`SURVEYS[...]["seed_pdfs"]` configures resolved — every downstream script (10, 11, 12) that
reads this file inherits a degraded K17-RGC baseline without flagging it.

**Tier 2 — `live-survey-eval/10_operator_benchmark.py`: the actual integration point.**
Imports `litdiscover.discovery.operators` (all 5 non-traversal operators, plus `_normalise_paper`
and `_get_json`), `litdiscover.discovery.traverse` (`backward_traversal_operator`,
`forward_traversal_operator`, `OperatorResult`), and `litdiscover.discovery.budget`
(`run_with_cost`, `recall_per_call`, `CostMetrics`) — every operator call in this script goes
through real production code with real cost accounting, not a reimplementation. What it does add
independently: its own `SURVEYS` config dict (same 3 survey keys as 09's, but carrying
`topic_query`/`since_year` instead of PDF paths — no shared source with 09's dict, kept in sync
only by hand), and gold-matching that is **exact-S2-ID-only** — 09's fuzzy tier-2 has no
counterpart here, so 09's recall numbers and 10's recall numbers are not directly comparable
even for the same survey.

**`live-survey-eval/11_redundancy_check.py` and `12_chained_composition.py`** build on 10
correctly at the operator level but reach it via `importlib.util.spec_from_file_location` —
dynamically loading and executing `10_operator_benchmark.py`'s whole module body as a sibling
script, not a normal package import (there is no importable shared module in `scripts/`). Both
inherit 10's exact-match-only gold logic this way. Both also independently reimplement the same
"rank accumulated candidates by `citation_count` desc, take top N" frontier-selection pattern
inline (11's `ROUND2_FRONTIER_CAP` slice, 12's `run_chained()` ranking) rather than sharing one
helper — the third occurrence of that specific pattern in the whole 15-script codebase.

### 1.3 Why these three tiers can't just be merged as-is (corrected 2026-07-14, same session)

**Correction:** an earlier version of this section called Tier 0's separation from production "an
online/offline mismatch" and suggested it would "likely always be a methodology proxy." That
overstated the case — it conflated a real, bounded engineering gap with an accidental
implementation choice that isn't actually forced by anything. Restated:

**Tier 0 (closed-corpus) is the same algorithm, blocked from reuse by one real refactor plus one
accidental divergence — not an architectural wall.**
- *Real, bounded:* `s2_client.py`'s `paginate_edges`/`batch_enrich_refs` are hardcoded to make
  live `httpx` calls — there's no interface between the operators and the network, so the
  operators can't currently be pointed at anything else. The fix is an ordinary refactor: define
  a `GraphSource` protocol (`get_references(id)`, `get_citations(id)`, `get_citation_count(id)`)
  that `s2_client`'s functions implement today, then add a second implementation backed by the
  closed corpus's `cites`/`cited_by` adjacency index (already built once per script by `eval/01`
  and re-derived independently 9 more times downstream — this refactor would also kill that
  duplication). Inject the source into `backward_traversal_operator`/`forward_traversal_operator`/
  `pareto_hub_threshold` instead of importing `s2_client` directly. Real work, ordinary shape.
- *Accidental, not forced:* the closed-corpus scripts filter hub papers *post-hoc*, by percentile
  of already-collected candidates' local out-degree; production filters *before* expansion, by a
  frontier paper's own citation count. Nothing about the closed corpus requires this — `eval/02`
  already computes per-paper in-degree across the full APS graph, so a pre-expansion filter
  matching production's exact logic (skip forward-traversing a frontier paper whose own in-degree
  clears the Gini-calibrated percentile) is directly buildable from data already on hand. The two
  implementations just diverged because they were written independently, not because the closed
  corpus demands a different filter point.
- *What does NOT go away after this refactor:* closed-corpus in-degree is bounded by the ~710K-
  paper APS-physics-only corpus; production's `citation_count` is a paper's global count across
  all of S2. Even with identical code and an aligned filter point, "hub-ness" relative to a
  narrow single-discipline corpus is a different number than hub-ness relative to the live
  full index — recall/precision numbers from the two tracks still won't be numerically
  comparable post-unification, only *mechanically* comparable (same algorithm, same code path,
  different corpus scope). That's a real, permanent limitation of what "unifying" can buy here —
  but it's a scope-of-corpus issue, not a reason the code paths can't be shared.

**Tier 1 (`09_live_validation.py`) is a bounded refactor, not an architectural mismatch.** It
already hits the live S2 API the same way production does — it just does so through its own
frozen-in-time client and traversal loop, written before `traverse.py` was decomposed into
swappable operators. Rewriting it to call `backward_traversal_operator`/
`forward_traversal_operator`/`pareto_hub_threshold` directly is mechanically straightforward
(no offline/online gap to bridge) and would close every drift flagged above in one pass: the
stale `S2_FIELDS`/rate-limit constants, the missing Gini-adaptive hub calibration, the
PDF-vs-S2-only backward-traversal divergence, and the dead fuzzy-matching branch. The one real
design decision this refactor forces, not yet made: whether recall should include 09's fuzzy
tier-2 title matching at all — right now that choice differs silently between 09 and
10/11/12/should be made once and applied uniformly.

**Tier 2/3 (10, 11, 12) already integrate correctly; what's left is deduplication, not
integration.** The fix here is mechanical: extract `10`'s `_load_gold`/`_load_seed_ids`/
`_fetch_full_paper`/`_recall`/`_precision` and the citation-count frontier-ranking helper into
one real importable module that 11 and 12 import normally, instead of the
`importlib.util.spec_from_file_location` sibling-script-loading trick; reconcile 09's and 10's
independently-hand-maintained `SURVEYS` config dicts into one source; and decide the fuzzy-match
question above once, upstream of all four scripts.

**Net effect on redoing Experiment 1 differently:** any redesign that wants apples-to-apples
recall/precision numbers across closed-corpus and live tracks needs to either accept Tier 0 as a
permanently separate methodology check (most realistic, given the online/offline mismatch), or
scope real engineering time to build the static-corpus adapter before comparing its numbers to
Tier 1-3's. Within the live track, Tier 1 (09) should not be compared to Tier 2/3 (10-12)
output at face value until the fuzzy-match and hub-calibration drift is resolved — they are
currently measuring recall under different, undocumented definitions of "match" and "hub."

### 1.4 Execution — the unification actually happened (2026-07-14, same session)

Following the correction in §1.3 (the closed-corpus/live-S2 split was a bounded engineering
gap, not a permanent wall), the `GraphSource` abstraction was actually built and the migration
carried out — not just scoped:

- **`litdiscover/discovery/graph_source.py` (new):** `GraphSource` protocol, `S2Source` (thin
  adapter — delegates to existing `traverse.py`/`operators.py` code via module-attribute lookup
  specifically so it doesn't break those modules' own existing patched tests — a real subtlety
  caught during implementation: a naive `from module import fn` bound-import would have silently
  stopped seeing test patches on the owning module), `ClosedCorpusSource` (pure in-memory,
  DOI-keyed, no network — `citation_count` = in-degree within the closed corpus, explicitly NOT
  comparable to live S2 `citation_count`, see §1.3's corpus-scope caveat), `_infer_venue_from_doi()`.
  `backward_traversal_operator`, `forward_traversal_operator`, `author_expansion_operator`,
  `venue_expansion_operator` all retrofitted with an optional `source=` param defaulting to
  `S2Source` — zero behavior change for every existing caller. `pareto_hub_threshold` needed no
  changes at all, exactly as predicted (it only ever reads `citation_count` off paper dicts it's
  handed). 32 new tests; **all 227 pre-existing tests pass completely unmodified** — the actual
  proof the live-S2 default path is byte-identical to before. Full suite: 259/259 green.
- **`closed-corpus-eval/scripts/_corpus_loader.py` (new):** centralizes the `cites`/`cited_by`
  adjacency construction that 9 of the 11 closed-corpus scripts each independently re-derived
  from the same CSV (documented in §1.2), plus a `build_closed_corpus_source()` that wires it
  into a `ClosedCorpusSource`.
- **`eval/04b_cold_start_lowseed.py` migrated and promoted to canonical.** Original archived as
  `04b_cold_start_lowseed_legacy.py`. Full 54-condition comparison (3 surveys × 3 seed strategies
  × k∈{1,2,3,4,5,10}): mean recall **93.5% → 99.6%**, mean corpus size **205,021 → 66,023**
  (3.1x smaller), conditions hitting recall=1.000 **3/54 → 49/54**. Root cause, verified by
  inspecting actual depth/round curves, not assumed: the legacy filter discarded newly-found
  *candidate* papers based on the **candidate's own out-degree** — a real design flaw, since a
  genuine gold paper could be excluded purely for citing a lot of things itself, a property
  unrelated to relevance. The corrected filter (matching production exactly) only decides
  whether to expand an already-visited *frontier* paper's citers, based on that frontier paper's
  own citation count — it never discards a candidate on the candidate's own properties. One
  legible trade-off: all 4 conditions that got worse (1.9–4.9pp recall decrease) are in the
  `contaminated`-seed strategy at low k — the condition most dependent on wide, indiscriminate
  exploration to accidentally recover gold papers within the fixed 2-round budget, exactly where
  a more disciplined filter shows its cost first.
- **`eval/05_miss_analysis.py` updated to mirror 04b** (this repo's own explicit rule, since it
  reconstructs the traversal from scratch rather than reading visited sets from the results
  JSON). **Consequence, flagged not silently absorbed:** the canonical k=5/top-k condition now
  has **zero misses** for all 3 surveys, so `06_publication_figures.py`'s Fig 7 ("miss analysis")
  has no data left to plot at that condition — Fig 7 needs a re-anchor to a harder seed condition
  or should be dropped; deliberately left as an open decision, not forced through.
- **`eval/03_traversal_simulation.py` migrated**, with one deliberate design split from 04b's
  migration: this script's whole point is an explicit Pareto-percentile *sweep* (10..90) as a
  controlled variable, but production's `pareto_hub_threshold()` applies a Gini-adaptive override
  that would silently overrule some requested sweep values. Resolution: compute each percentile
  threshold directly (`np.percentile` over the frontier's own `citation_count`, at production's
  actual pre-expansion filter point) and pass it straight to `forward_traversal_operator`'s
  `hub_threshold`, bypassing only the threshold-*selection policy*, not the actual candidate-
  fetching/filtering mechanics, which still come from the real operator.
- **`sweep/07_rounds_sweep.py` migrated** (same engine swap; its pre-existing K_SEED=20 vs.
  the canonical k=5 inconsistency, flagged in §1.2, was left as-is — this migration only swaps
  the traversal engine, not the experimental design).
- **`live-survey-eval/`'s Tier 2/3 cleanup done:** `10_operator_benchmark.py`'s loaders/config/
  metrics (`SURVEYS`, `_load_gold`, `_load_seed_ids`, `_fetch_full_paper`, `_recall`,
  `_precision`, `OPERATORS`, `MARGINAL_ORDER`) extracted into `_shared.py`; `11_redundancy_check.py`
  and `12_chained_composition.py` now `import _shared` normally instead of
  `importlib.util.spec_from_file_location`-loading `10`'s whole module body. Verified all three
  import cleanly via `runpy`.
- **Real-world performance finding, worth recording:** `backward_traversal_operator`'s
  `ThreadPoolExecutor`-per-paper design (built for production's per-round frontier of dozens to
  low hundreds of papers) is measurably slow when driven at closed-corpus BFS scale — `eval/03`'s
  unfiltered `forward`/`bidir` strategies at depth 6 can push the frontier into the hundreds of
  thousands, and thread-submission overhead at that scale made a single script run take on the
  order of 30-40 minutes (vs. `04b`'s ~5-7 minutes for its whole 54-condition grid, since Pareto
  filtering keeps 04b's frontiers much smaller throughout). Not a correctness problem, a real
  cost one — worth a `pdf_workers`-style batch-size cap or a non-threaded code path for
  closed-corpus-scale callers if this becomes a recurring pattern.

**Update, same session — everything above closed out except the .mat blocker and Fig 7:**

- **`sweep/04_cold_start_simulation.py` and `sweep/08_hyperparameter_sweep.py` migrated** (same
  engine swap as `04b`/`eval/03`; `sweep/08` also needed the same Gini-override bypass `eval/03`
  needed, for the same reason — it sweeps `PARETO_P_VALS` as an explicit controlled variable).
  **Neither was run to completion** — `sweep/08` is 1980 configs (660 × 3 surveys), and `eval/03`'s
  migration alone (33 conditions) already took ~30-40 minutes against the production
  `ThreadPoolExecutor`-based operators at this corpus scale before being killed partway through
  (memory climbing toward the system's 16GB ceiling, 56MB free at kill time — not itself a bug,
  just genuine cost at this scale). `sweep/08` at ~60x eval/03's condition count would likely take
  hours. Correctness verified by matching each script's traversal shape line-for-line against the
  already-validated `04b` migration, not by full execution — a deliberate choice once the cost
  became clear, not an oversight.
- **`closed-corpus-eval/scripts/eval/07_operator_benchmark.py` built and run successfully** —
  but scoped to backward/forward/pareto only, not author/venue as originally hoped. The `.mat`
  file's author-DOI linkage turned out to be **genuinely inaccessible, not just effortful to
  parse**: its `authorName`/`doi`/`affiliationName`/`pubDate` fields use MATLAB's `string` type
  wrapped in MCOS object encoding. Confirmed via two independent tools, not just h5py struggling —
  `mat73` (a maintained library built specifically for this MATLAB version) explicitly raises
  `"MATLAB type not supported: string, (uint32)"` on this exact file. The underlying sparse
  matrices (B/C/D/E) decode fine, but without the label strings their indices can't be mapped back
  to real DOIs or author names. Reverse-engineering MATLAB's proprietary MCOS object graph from
  scratch was judged a real, correctness-risky undertaking disproportionate to the value, not
  attempted. The script ran clean end-to-end (single-pass, no BFS loop, seconds not minutes) and
  produced real ablation numbers — e.g. S2_UCG: union recall 33.3%, backward-ablation Δ=+2.5%,
  forward-ablation Δ=+28.0% (forward traversal dominates recall on this survey, backward on
  S1_MIT) — the actual "operators against real closed-corpus data" deliverable, just narrower in
  scope than originally hoped.
- **`live-survey-eval/09_live_validation.py` migrated** — `bidir_pareto_traversal_live()` and
  `escape_hatch_loop_live()` now call the real production operators via `S2Source`, resolving
  frontier papers through 09's own `fetch_paper()` (so its disk cache is still used). This closes
  Tier 1's drift from production named in §1.3: backward traversal is now genuinely PDF-first
  (not S2-`/references`-only), and the Pareto filter now applies at production's actual point
  (pre-expansion, frontier's own `citation_count`, Gini-calibrated) instead of post-hoc on
  collected citers' `reference_count`. **Not run to completion** — a full 3-survey live run
  spends real S2 API quota and time, deliberately not spent without a specific reason to; verified
  via import/syntax checks only, following the same "fix without forcing a full rerun" call made
  for the sweep scripts above. The dead fuzzy-match branch and the `09` vs. `10`-`12` recall
  definition question (§1.3) remain genuinely open — this migration didn't touch either.

**Resolved this session, not left dangling** — each of the three items below was framed as "open"
in an earlier draft of this note, but each already has an explicit decision behind it, made
during this session, not a gap waiting on someone:

1. **Fig 7's zero-misses consequence** — user's explicit call: leave `05`/`06` as they stand,
   revisit after reviewing everything else this session changed (asked directly, this was one of
   three options offered; "pause" was chosen over "re-anchor to a harder condition" or "drop
   Fig 7"). Status: **deferred by decision, not unresolved by omission.** `05_miss_analysis.py`
   and `06_publication_figures.py` are both left exactly as they were at that decision point —
   `05` re-run with the corrected engine (0 misses at k=5/top-k, documented above), `06` untouched.
   Next session should start here if the paper needs Fig 7 resolved before submission.
2. **Running `eval/03`/`sweep/04`/`sweep/08`/`live-survey-eval/09` to full completion** — user's
   explicit call, given directly after watching `eval/03` cost ~30-40 minutes and climb toward the
   system's memory ceiling: "can we just fix them without trying to rerun the full thing?" Status:
   **decided against, not merely deferred.** All four are migrated, syntax/logic-verified against
   the already-validated `04b`/`05` pattern, and deliberately not executed to completion. Re-run
   only if a specific reason to spend that time/API budget arises (e.g. the paper actually needs
   updated `eval/03`/`sweep/08` figures) — this is a cost decision to revisit then, not a
   forgotten step now.
3. **The `.mat` file's author data** — not a scheduling gap, a **confirmed technical dead end**
   with external evidence: `mat73` (a maintained library built specifically for this MATLAB
   version) explicitly rejects the file's `authorName`/`doi` fields as an unsupported type. Status:
   **investigated and closed as blocked**, not pending investigation. Reopening it requires new
   input this session didn't have access to — an official MATLAB export of the same data, or
   locating an original tabular/CSV source upstream — not more effort on the same approach.

None of the three block anything else in this roadmap; they're recorded here so a future session
doesn't have to re-derive why each one stopped where it did.

---

## 2. Who else touches the discovery problem, and how

Drawn from `deep-dives.md`'s 27 method entries + `lineages/` — every discovery *mechanism* another
tool actually uses, grouped by family, not repeating each paper's full deep-dive. This is what
grounds §4's untested-method list in prior art instead of inventing from scratch.

| Mechanism family | Who does it | How |
|---|---|---|
| **Citation-graph traversal** (closest cousins to LitDiscover) | ProfOlaf | Iterative snowballing (backward refs + forward citations) via Google Scholar/S2/DBLP, human-resolved dedup, chosen over database search on prior evidence it performs as well or better. No formal stopping rule beyond human judgment per iteration. |
| | ResearchRabbit | Co-citation + bibliographic coupling + an undisclosed "AI similarity" signal, over OpenAlex/S2/PubMed. **No published stopping criterion at all** — flagged in independent review (Braun 2024) as a real, literature-confirmed gap, not just an assumed one. Its own two "similar-work" outputs only overlap 3/50 against Connected Papers, evidence that even tools in this same family diverge sharply on what "similar" means. |
| | SurveyGen-I, SurveyGen | Both start from keyword/embedding search, then add **citation/co-citation expansion as a second pass** — SurveyGen-I resolves indirect in-text citations found inside retrieved passages; SurveyGen adds any paper cited by ≥2 already-candidate papers. Neither is graph-traversal-first the way LitDiscover or ProfOlaf are — citation expansion is a supplement to search, not the primary mechanism. |
| | SYMBALS (classical, pre-LLM) | Named precedent for combining snowballing + active-learning screening — same two-mechanism combination LitDiscover uses (traversal + adaptive screening), just without any LLM component. |
| **Keyword/Boolean database search only** (no graph, no embeddings) | Sami et al. SLR-Multiple-AI-Agents | Single LLM-generated Boolean search string against one database (Scopus), no "AND" operator even — a self-acknowledged "sub-optimal" search strategy in the paper's own limitations section. |
| | ReviewGenie | Automated multi-database API search (PubMed, IEEE Xplore, Embase, PsycINFO) with no graph, no embeddings, no active-learning loop — explicitly "cannot surface papers missed by the initial search string." |
| | GEAR-Up | Upgrades the *query itself* — knowledge-graph + LLM-generated query expansion feeding PubMed search, then FAISS re-ranks. Only one database, front-end-only automation (protocol/query formulation), leaves screening/extraction/synthesis untouched. |
| | Scholar Augment | LLM-generated Boolean search string per-database ("expert librarian" framing), auto-downloads via Unpaywall — but the paper's actual contribution and evaluation is downstream extraction, not discovery quality. |
| **Embedding/semantic similarity search over a corpus** | AutoSurvey | Embedding-based retrieval over a fixed offline 530k-paper CS corpus. Ablation shows this is the single most load-bearing mechanism in the whole pipeline — removing retrieval drops citation recall from 83.48%→60.11%, the largest effect in the paper. |
| | SurveyX | Iterative Keyword Expansion Algorithm (clusters retrieved abstracts to grow the keyword pool) querying **both** an offline arXiv corpus and a live Google Scholar crawl, then embedding Top-K + LLM relevance classification. Explicitly built to fix AutoSurvey's offline-only retrieval limitation. |
| | SocLitGen | Three-step hybrid per sub-topic: BM25 coarse screen (top 100) → BGE-M3 vector-embedding rerank (top-K=30) → LLM Chain-of-Thought binary judgment, with automatic iterative re-retrieval (up to 3 rounds) if a sub-topic's validated-literature count falls below threshold. Its own sensitivity check found switching to live Semantic Scholar retrieval (from its private 1.5M-paper corpus) *significantly improved* citation quality — i.e. corpus breadth, not synthesis logic, was its bottleneck. |
| | PROMPTHEUS | arXiv-API keyword query (up to 3000 papers) → Sentence-BERT cosine similarity keeps top 200. Single-source (arXiv only), no graph, no reported precision/recall for this retrieval step at all. |
| **LLM-generated keyword query → external search API** (closest cousin to LitDiscover's own escape hatch) | LitLLM / LitLLMs-are-we-there-yet | LLM summarizes the query abstract into ≤5 keywords, queries S2 + OpenAlex, optionally combined with SPECTER2 embedding retrieval and/or S2's Recommendations API from a seed paper. Their own ablation: combining keyword + SPECTER2 embedding search improves precision ~10% and normalized recall ~30% over either alone — direct evidence that combining discovery mechanisms beats any single one, which is exactly §4's proposed ablation logic. |
| | Human-Centred Research Automation | A Research Topic Agent (LLM-generated topic queries) + Paper Search Agent retrieving from Scopus/arXiv — architecturally the closest analogue to LitDiscover's own "criteria → LLM query → S2 search" escape hatch, just as the *only* discovery mechanism rather than a fallback. |
| **Re-ranking / triage over an already-assembled pool** (not discovery — assumes the candidate pool is given) | ASReview, Bio-SIEVE, LLAssist, TriSem-LLM's screening stage | None of these search for papers at all — each takes an already-retrieved record set (from a standard database search done outside the tool) and re-ranks or classifies it. Relevant to LitDiscover only as a possible **prefilter/screen** technique, not a discovery method — TriSem-LLM's multi-criteria-without-early-exclusion screening design in particular is a candidate technique for `litdiscover prefilter`, not for discovery itself. |
| **No discovery step named at all** | LiRA | Explicitly names this as its own unaddressed future work: "integration of the screening and search criteria definition steps within the pipeline" — i.e. LiRA assumes references are already curated. This is the single sharpest piece of evidence in the whole corpus that discovery-with-recall-guarantees is a genuinely open gap the LLM-native survey-generation cohort has not solved, not just an area LitDiscover happens to have prioritized differently. |

**What this table changes about §3's method list:** every "untested" method named in §3
already has field precedent to build from rather than invent —

- **Semantic embedding search** → SocLitGen's BM25→vector→LLM-CoT cascade and LitLLM's SPECTER2-combined retrieval are both concrete, already-measured recipes (LitLLM: +10% precision/+30% normalized recall from combining keyword + embedding vs. either alone).
- **Author/venue search** → no method in this entire 27-paper survey does either. This is a genuine gap in the field's own related work, not just LitDiscover's — worth flagging as a possible actual novelty angle for the paper, not only an engine feature.
- **Recency-only search** → same: nobody in the corpus addresses "papers too new to be graph-reachable" as a named problem. LiRA's own gap (assumes curated references) and ResearchRabbit's own gap (no stopping criterion) are adjacent but distinct — neither is "can't reach brand-new work," which is specifically a citation-graph-traversal limitation, not a screening or stopping-criterion limitation.
- **Combining methods, not picking one** → LitLLM's own ablation is direct outside evidence that method combination beats any single mechanism, which is exactly what §4 proposes measuring for LitDiscover's own method set.

---

## 3. The bet we've been making, named explicitly

Two discovery mechanisms only, and one of them (the escape hatch) only fires when the other
stalls: **(a)** citation-graph traversal, **(b)** LLM-generated keyword → S2 relevance search.
Everything else is untried:

| Method | Status | Why it might find papers traversal + search can't |
|---|---|---|
| **Semantic embedding search** | Not implemented | S2's `/paper/search` already does *some* embedding/rerank internally (unclear how much — worth confirming precisely what it runs before assuming it's pure keyword match), but there's no explicit embedding-query search against, e.g., the included set's own centroid. We already have a Gemini embedding client wired up for synthesis clustering (`models/gemini-embedding-001`) — reusable for query-time semantic search if S2 or another index exposes embeddings. |
| **Keyword search** | Arguably already covered | S2 `/paper/search` IS keyword/relevance-based; the escape hatch already generates and fires keyword queries at it. Worth clarifying whether "add keyword search" means something distinct from what's there, or whether the real gap is *when* it fires (only as a stale-yield fallback, never proactively alongside traversal). |
| **Author search** | Not implemented | S2 has `/author/{id}/papers` and `/author/search`. A name recurring across the included set is a strong signal that isn't currently exploited — traversal only follows citation edges, never "this author's other work." |
| **Venue search** | Not implemented | S2 supports venue filtering. Domain-specific venues (e.g. a systematic-review-methodology paper likely also appears in a small set of specific journals) are a distinct signal from citation adjacency. |
| **Recency-only search (e.g. "2026 only")** | Not implemented, and structurally *can't* be reached by traversal at all | Forward traversal requires the paper to already be cited by something; backward requires it to already have indexed references. A paper published this month has neither — it is invisible to both existing mechanisms regardless of tuning. This is the one method that isn't "another way to reach the same papers," it's the only way to reach some papers at all. |

The table above names methods. §4 reframes each as a **retrieval operator** — an interchangeable
module with a common interface — because that's what makes the rest of the experiment design
(ablation, ordering, budget-normalized comparison) possible at all.

---

## 4. Experiment 1 — Multi-Operator Retrieval Benchmark

> **⏸ PAUSED 2026-07-14 — read this box before reading further, and before resuming this thread.**
> Everything below (§4.1-§4.11) was built and run in a single session on 2026-07-14. Real findings
> came out of it, but so did enough compounding methodological gaps that continuing to patch the
> same experimental design stopped being a good use of live-API budget. Summary, most important
> finding first:
>
> 1. **The most important thing this session found has nothing to do with the new operators**: the
>    *original, already-validated* traversal system's headline recall (89-98% closed-corpus,
>    73-100% live-survey — §1) has never had its precision checked. Checked for the first time
>    2026-07-14: implied precision is **0.03%-0.45%** (56/31,168, 202/44,577, 42/150,197 papers
>    visited to reach that recall) — because that eval explicitly measures pure graph reachability
>    with no LLM screening in the loop (a gap named in §1 since this file was first split out, but
>    never quantified until today). **This likely matters for how the IP&M submission frames its
>    own headline claim** and should be raised there independent of anything else in this section.
> 2. **3 of 7 candidate operators (embedding search, venue expansion, recency search) found ~0% new
>    gold and ~0% precision on all 3 surveys, in every experiment run** — reproducible, not noise.
>    Don't invest more engineering time in these three without first checking whether that's a
>    genuine absence of value or an implementation gap (S2 API call correctness, query
>    construction) — this was never disambiguated.
> 3. **Co-citation is the one new operator with consistent, real signal** — best precision of
>    anything that fired (10-29%), present in the ablation drop on every survey, and confirmed
>    (§4.6's redundancy check) not to be redundant with cheaper alternatives.
> 4. **Naive chained composition made both recall and precision *worse*** than independent-union,
>    and the failure mode was diagnosed precisely (unfiltered forward traversal explodes the
>    corpus; ranking it by raw citation count for frontier selection then hands downstream
>    operators generic hub papers, not relevant ones) — a real, actionable lesson even though the
>    experiment itself didn't complete cleanly.
> 5. **Why paused, not fixed-and-continued:** every fix attempted here revealed a deeper fairness
>    problem underneath it (single-hop operators vs. the original system's multi-round loop; raw
>    recall vs. budget-normalized recall; naive frontier selection). The right redesign is a
>    budget-normalized comparison (§4.7, scoped from the start, never built) rather than another
>    patch on raw-recall comparisons — worth doing with a clear head in a future session, not by
>    continuing to spend live S2 API budget on the same design mid-fatigue.
> 6. **n=3 surveys throughout** — nothing in §4 was ever at statistical power regardless of any of
>    the above; treat every number here as directional.
>
> §1-3 above (what's implemented today, prior-art survey, the original two-mechanism bet) are
> untouched by this pause — they predate 2026-07-14 and aren't in question. Scripts
> (`10_operator_benchmark.py`, `11_redundancy_check.py`, `12_chained_composition.py`) and data
> stay in the repo, reusable if this resumes.

The IR community has spent decades building evaluation methodology for exactly this class of
problem. This experiment adapts that methodology (the Cranfield paradigm, ablation studies,
Pareto-frontier cost/quality tradeoffs, paired significance testing) to citation-graph discovery,
rather than inventing new evaluation from scratch. The research question is not *"which pipeline
works?"* — it's **"which retrieval operators contribute the most, in what order, at what cost?"**

### 4.1 The reframe: operators, not pipelines

Everything below depends on treating discovery mechanisms as **interchangeable operators** with
one shared interface, not as fixed end-to-end pipelines:

```
operator(current paper set) → candidate papers
```

This is a real change from how the current system is built. `traverse.py` today fuses backward
traversal, forward traversal, and the Pareto filter into one function; the escape hatch is a
second, separately-triggered mechanism. Under this reframe, that's actually **at least three
operators** (backward-traversal, forward-traversal, Pareto-filtered-forward-traversal), each
independently swappable and independently measurable — not one atomic "citation traversal"
method. Decomposing the existing implementation this finely is itself part of the experiment,
not just a framing exercise.

**Operator inventory** (existing + proposed, superseding the flat method list above):

| Operator | Status | Notes |
|---|---|---|
| Backward citation traversal | Implemented (`traverse.py`) | PDF-first, S2-fallback |
| Forward citation traversal | Implemented (`traverse.py`) | S2-only |
| Pareto hub filter (on forward traversal) | Implemented (`traverse.py`) | Gini-adaptive percentile |
| Keyword/relevance search (S2 `/paper/search`) | Implemented (`search.py`) | Currently escape-hatch-only, not proactive |
| LLM query rewriting/keyword generation | Implemented (`screen/llm.py`'s `generate_search_query`) | Feeds the keyword-search operator above |
| Embedding/semantic search | ✅ Implemented (`operators.py::embedding_search_operator`, 2026-07-14) | Uses S2's own SPECTER-embedding Recommendations API (`/recommendations/v1/papers/forpaper/{id}`) rather than hosting our own embedding index — verified live before implementing (response key is `recommendedPapers`, not `data`) |
| Author expansion | ✅ Implemented (`operators.py::author_expansion_operator`, 2026-07-14) | S2 `/author/search` + `/author/{id}/papers`; best-effort name resolution (exact match, else most-published candidate) — name disambiguation is a real unsolved limitation, not this operator's problem to solve |
| Venue expansion | ✅ Implemented (`operators.py::venue_expansion_operator`, 2026-07-14) | S2 venue filter + a year window derived from the input set's own year range, so it doesn't pull in a venue's entire multi-decade history |
| Recency-only search | ✅ Implemented (`operators.py::recency_search_operator`, 2026-07-14) | The one operator structurally unreachable by any graph method; takes an explicit query string (same one the LLM escape hatch already generates) since it can't derive from the paper set |
| Co-citation / bibliographic-coupling retrieval | ✅ Implemented (`operators.py::co_citation_operator`, 2026-07-14) | ResearchRabbit's actual mechanism (§2), reusing `paginate_edges` — seeds' citers' own reference lists, candidate kept if it co-occurs across ≥`min_co_occurrence` citers. Intrinsically more expensive (O(seeds × citers)); cost-capped |
| Re-ranking (post-retrieval) | Not implemented as a discovery step | Exists downstream as `prefilter`/`screen`, not applied to raw operator output before dedup |

### 4.2 Gold standard (Cranfield paradigm)

**We already have one, partially.** The 6 existing surveys (S1-MIT, S2-UCG, S3-TOPO, K17-RGC,
Ge21-HSS, Le25-GLLM) already follow exactly this design: bibliography hidden as ground truth,
retrieval starts from title + a handful of seeds. This experiment reuses that gold standard rather
than building one from scratch — the closed-corpus/live-survey split already done is the hard
part.

**What's missing:** 6 surveys is thin for the paired significance testing in §4.9 — Wilcoxon
signed-rank wants more like 15-20 paired observations for real power. Expanding to that range (new
domains, not just more physics surveys, to avoid overfitting operator choices to one field) is a
prerequisite for §4.9, not for §4.3-§4.8 which can run meaningfully on 6.

### 4.3 Baselines — seed-only and single-operator recall

Before any combination or ablation, establish the floor: recall from seeds alone (no operators
fired), and recall from each operator run in isolation from the same seed set. Every later number
in this experiment is measured relative to these baselines, not in the abstract.

**✅ Run — done 2026-07-14** (`live-survey-eval/scripts/10_operator_benchmark.py`), against all
three live surveys (per §5, non-graph operators can only be validated against live-survey
semantics, not the APS simulation). Reuses the existing gold-sets/seeds JSON from
`09_live_validation.py` unchanged; calls the real production operators
(`litdiscover.discovery.operators` + `traverse.py`'s decomposed operators) via
`budget.run_with_cost()`, not a reimplementation. Results:
`live-survey-eval/data/outputs/operator_benchmark_results.json`.

| Operator | K17-RGC (n=56 gold) | Ge21-HSS (n=202 gold) | Le25-GLLM (n=57 gold) |
|---|---|---|---|
| backward_traversal | +5 gold (5.0/call) | +2 gold (0.67/call) | +0 gold |
| forward_traversal | +0 gold | +1 gold (0.33/call) | +0 gold |
| embedding_search | +0 gold | +0 gold | +0 gold |
| co_citation | +4 gold (0.19/call) | **+19 gold (0.76/call)** | +2 gold (0.06/call) |
| author_expansion | +0 gold | +7 gold (0.39/call) | +0 gold |
| venue_expansion | +0 gold | +0 gold | +0 gold |
| recency_search | +1 gold (1.0/call) | +0 gold | +0 gold |

**Headline finding: co-citation is the only non-traversal operator that adds gold on every single
survey**, and by a wide margin on Ge21-HSS (+19, more than backward+forward traversal combined).
This is a real, reproducible signal that ResearchRabbit's actual mechanism (§2) is legitimately
load-bearing, not just a plausible-sounding untested idea. **Embedding search and venue expansion
found zero new gold on all three surveys** — worth treating as a genuine early negative result
(not proof of no value — see caveats below), not silence.

**Caveats, read before citing these numbers anywhere:**
- This measures single-pass, single-round, isolated-operator recall — not the multi-round
  adaptive escape-hatch loop production actually runs (that's what `09_live_validation.py`'s
  73–100% headline numbers already measure). These numbers answer "does operator X find gold
  traversal alone doesn't," not "what's achievable end-to-end."
- The S2 author-search and recommendations endpoints threw intermittent 429s during this run —
  e.g. `author_expansion` on Le25-GLLM lost a paper's-worth of results to a 429 mid-run. **Root
  cause, verified against S2's own docs (2026-07-14), not the "separate stricter sub-API bucket"
  theory first written here:** a standard S2 API key gets a flat 1 request/second cap *across all
  endpoints* (semanticscholar.org/product/api/tutorial: "using an individual API key automatically
  gives a user a 1 request per second rate across all endpoints") — there's no evidence of a
  distinct, stricter budget for author/recommendations specifically. `s2_client.py`'s shared
  `_s2_wait()` enforces only a 1.05s minimum interval — barely above the 1.0s cap, with no margin
  for network jitter or S2-side window-edge effects, and S2 documents no `Retry-After` header or
  official backoff schedule (only "you've hit the limit, slow down"). That tight margin plus no
  client-side retry-on-429 is the actual cause. Author/embedding recall-per-call numbers above are
  a **lower bound**, not the operator's true ceiling.
- Le25-GLLM ran on 2 resolved seeds, not the configured 3 — one seed's full-record fetch also hit
  a 429 and was silently dropped (`_fetch_full_paper` has no retry). Same root cause as above.
- Seed counts are small (1–3) and survey count is 3 — not yet the §4.9 statistical-testing regime.
  Treat this as a first real signal to act on (build §7 step 6 backoff/retry, prioritize
  co-citation), not a publishable result.
- **✅ Fixed 2026-07-14:** `s2_client._s2_wait()` now retries on 429 with exponential backoff
  (mirrors the pattern `live-survey-eval/scripts/09_live_validation.py` already used successfully
  for its own standalone S2 client), and the shared minimum interval was widened from 1.05s to
  1.2s for a small safety margin. See `litdiscover/discovery/s2_client.py`.

### 4.4 Marginal contribution

Not "which pipeline is best" but "how much recall does each operator add, on top of what's already
found." Run operators in an additive sequence and track the recall curve:

```
seeds only            → recall = 18%
+ keyword search       → recall = 47%   (+29)
+ citation traversal   → recall = 74%   (+27)
+ embedding search     → recall = 86%   (+12)
+ author expansion     → recall = 88%   (+2)
```

(Illustrative numbers — the actual curve is the experiment's output, not an assumption.) This is
the direct answer to "does adding operator X actually help, or is it redundant with what's already
there" — the same question §3's untested-method table raised without a way to measure it.

**✅ Run — done 2026-07-14**, same script/data as §4.3. Sequence used: backward → forward →
embedding → co-citation → author → venue → recency (graph operators first, then non-graph in
roughly ascending cost order — this ordering choice is itself an input to §4.6, not a claimed-best
sequence). Final cumulative recall: K17-RGC 14.3%, Ge21-HSS 11.9%, Le25-GLLM 3.5% — **on every
survey, co-citation is where the curve visibly bends** (K17: 8.9%→14.3%; Ge21: 1.5%→9.9%, the
single largest jump in any survey's curve; Le25: 0.0%→3.5%, its only jump at all). Author expansion
adds a second, smaller bend only on Ge21-HSS (11.9%→9.9%... i.e. +4 after co-citation's +17).
Venue and recency contributed nothing in the marginal sequence on any survey (recency's isolated
K17-RGC hit doesn't survive being added after traversal+co-citation already found the same paper).

### 4.5 Ablation study

Standard leave-one-out: run the full operator set, then each variant with one operator removed
(minus-citation, minus-embedding, minus-keyword, minus-author, minus-venue). The recall drop from
removing an operator is a cleaner signal than that operator's standalone recall — an operator can
have low standalone recall but cause a large drop when removed, if it's finding papers nothing
else reaches (this is the same "marginal recall" concept from the earlier draft, formalized here
as leave-one-out rather than eyeballed).

**✅ Run — done 2026-07-14**, same script as §4.3/§4.4 (`10_operator_benchmark.py`, consolidated —
see note below), derived from the same per-operator candidate sets as a set-difference against the
full union, at zero extra API cost.

| Operator removed | K17-RGC (Δ) | Ge21-HSS (Δ) | Le25-GLLM (Δ) |
|---|---|---|---|
| backward_traversal | **−7.1%** | 0.0% | 0.0% |
| forward_traversal | 0.0% | 0.0% | 0.0% |
| embedding_search | 0.0% | 0.0% | 0.0% |
| co_citation | **−5.4%** | **−7.9%** | **−3.5%** |
| author_expansion | 0.0% | −2.0% | 0.0% |
| venue_expansion | 0.0% | 0.0% | 0.0% |
| recency_search | 0.0% | 0.0% | 0.0% |

**Confirms §4.3/§4.4's finding from a different angle: co-citation is the only non-traversal
operator with a nonzero recall drop on every survey**, the largest drop of any operator on two of
three (Ge21-HSS, Le25-GLLM), and second only to backward traversal on K17-RGC (where a single seed
makes backward traversal structurally load-bearing). Embedding, venue, and recency contributed a
literal zero-recall-impact ablation result on all three surveys in this run — the strongest
negative signal yet for those three, though still only n=3 surveys.

**Script consolidation, done alongside this run:** the previous version of `10_operator_benchmark.py`
re-invoked every operator a second time inside the §4.4 marginal-contribution loop, since none of
these operators actually take the accumulated/expanding corpus as input (all depend only on the
fixed seed set) — that made the second invocation both wasteful (2x API cost) and inconsistent
(S2 search results vary slightly call-to-call, observed directly: K17-RGC's `recency_search` found
+1 gold on one run and +0 on an immediate rerun with an unchanged query). Now every operator runs
exactly once per survey; §4.3, §4.4, and §4.5 are all derived from that single set of candidate
sets via union/difference. This also confirmed the 429-retry-with-backoff fix (§7 step 6) is
working live — `[s2-retry]` traces fired and recovered successfully three times during this run
(on `_get_json` and `_fetch_edges`), not just inferred from before/after call counts as in the
prior write-up.

**⚠ Precision added after this run, and it changes the picture — see the ⏸ box at the top of §4.**
`10_operator_benchmark.py` was later extended to track precision (`new_gold / candidates`), not
just recall, for every number above. Full-set precision (all 7 operators unioned) turned out to be
**0.3%-4.7%** across the three surveys — i.e. 95-99.7% of the union's candidates are not gold. The
ablation deltas above are still real (co-citation's drop holds), but "the union recalls 12-13.5%"
reads very differently once you know it costs 700-1700+ candidates to get there. Per-operator
precision (added same pass): co-citation is also the best-precision operator wherever it fires
(10-29%) — recall and precision agree here, co-citation is the standout on both axes.

### 4.6 Ordering experiment

Operator order plausibly matters because retrieval compounds — the candidate set an operator
receives as input depends on what already ran. Compare, e.g.:

```
Pipeline A:  keyword → citation-traversal → embedding
Pipeline B:  embedding → citation-traversal → keyword
```

Same operators, different order, likely different recall/precision/cost even though the operator
*set* is identical. This is a genuinely open question the current architecture has never tested —
it committed to one order (traversal-first, search-as-fallback) without comparing it to anything.

**Still not run as originally scoped, and now scoped precisely, per the §4.5 consolidation above:**
the current `10_operator_benchmark.py` operators all take the *fixed seed set* as input, never
each other's output — meaning reordering `MARGINAL_ORDER` cannot change final cumulative recall
today, only which step gets "credit" for an overlapping find. A genuine ordering experiment
requires a new execution mode where operator N's input is `seeds ∪ (all prior operators'
candidates)`, so later operators see an expanding corpus.

**Redundancy pre-check run before committing to that build — done 2026-07-14**
(`11_redundancy_check.py`). Before scoping a bigger chained-execution experiment around
co-citation (§4.5's standout operator), checked whether it's actually redundant with something
cheaper: both co-citation and a 2-round forward traversal hop through the same intermediate set
(seeds' citers), but pull different signal out of it (co-citation looks backward from citers —
their own references, kept if shared by ≥2; multi-round forward traversal looks forward again —
who cites the citers). Ran both from the same seeds on all 3 surveys:

| Survey | Candidate Jaccard | New-gold Jaccard | Multi-round fwd (candidates / new gold) | Co-citation (candidates / new gold) |
|---|---|---|---|---|
| Ge21-HSS | 0.02 | 0.10 | 307 / 3 | 66 / 19 |
| K17-RGC | 0.00 | 0.00 | 203 / 0 | 40 / 4 |
| Le25-GLLM | 0.00 | 0.00 | 1712 / 1 | 143 / 2 |

**Finding: not redundant — the intuition was reasonable to check but wrong.** Candidate and
new-gold overlap are both near-zero on every survey; these two mechanisms are finding almost
entirely disjoint papers, not the same ones via different paths. **Bonus finding, unprompted:**
naive multi-round (depth-2) forward traversal looks like a bad-ROI operator in its own right,
independent of the ordering question — it pulled in 5-12x more candidates than co-citation for
*less* new gold on every survey (worst case Le25-GLLM: 1712 candidates for 1 new gold vs.
co-citation's 143 for 2). This was uncontrolled by the Pareto hub filter in this quick check — see
below, this turned out to matter a great deal once actually built into the chained experiment.

#### §4.6 reframed as four orthogonal questions (2026-07-14) — only the first was scoped to build

An outside review of this plan pushed back usefully: the interesting question isn't "does chained
execution work" (a systems question) but **"how should heterogeneous retrieval operators be
composed?"** — and that decomposes into four genuinely separate questions, most of which don't
need building yet:

1. **Composition** — does chaining operators on the accumulated corpus beat independently running
   each operator from seeds and taking the union? **Attempted — see below; result was negative,
   with a diagnosed cause, not inconclusive.**
2. **Ordering** — given chaining helps, which operator sequence works best? **Still gated on #1** —
   moot given #1's result below.
3. **Frontier selection** — given an accumulated corpus, which papers should feed the next
   operator? **Turned out to be the actual root cause of #1's negative result — see below.**
4. **Stopping criterion** — when should retrieval terminate? Already partially answered by
   production's yield-based stopping and the multi-round live-survey validation
   (`09_live_validation.py`) — a genuinely separate research question, named here as future work.

**Experiment 1 — Composition, formal hypotheses, as actually run:**
- **H0 (null):** running operators sequentially on the accumulated corpus produces no meaningful
  recall increase over independently running each operator from seeds and taking the union.
- **H1 (alternative):** sequential composition lets downstream operators exploit newly-discovered
  papers, finding additional relevant papers the independent-union approach would miss.
- **Design as built** (`12_chained_composition.py`): one growing `accumulated_papers` list; each
  operator in `MARGINAL_ORDER` receives it (not the fixed `seeds`) as input. Frontier-selection
  default used: rank `accumulated_papers` by `citation_count` descending before each operator's own
  `list[:max_N]` cap. Compared against §4.5's `full_recall`/`full_precision` (the independent-union
  arm, already computed, no new run needed for that side).

**Result (Ge21-HSS, the one survey completed before the run was stopped — see below):**

| | Independent union (§4.5) | Chained |
|---|---|---|
| Recall | 12.0% | 7.5% (**−4.5pp**) |
| Precision | 4.7% | 1.1% (**−3.7pp**) |

**Chaining made both metrics worse, and the mechanism is fully diagnosed, not a mystery:**
unfiltered `forward_traversal` (no Pareto hub filter applied in the chain, unlike production)
exploded the corpus past 1,000 papers within two steps. Ranking that noisy corpus by raw
`citation_count` then handed `venue_expansion` a top-10 list dominated by generic mega-cited
papers — its actual queried venues included *Science*, *Physical Review Letters*, *American
Journal of Epidemiology*, *Demography* — completely off-topic for a human-social-sensing survey.
That single step added 407 candidates and **0 new gold**. The run was killed before K17-RGC/
Le25-GLLM completed once this pattern was clear (co-citation, later in the same chain, was about
to spend enormous cost expanding from the same handful of hub papers).

**This also exposed a fairness problem in the whole §4 design, not just the composition
experiment:** every operator-benchmark run in §4.3-§4.6 gives citation traversal exactly **one
hop** (that's what makes it a composable "operator"), but the *original, already-validated*
traversal system (§1) is a **multi-round loop** that earns its 73-100% recall over several rounds
plus an escape hatch. Checking `09_live_validation.py`'s own saved output for the first time
against precision (never done before, for the original system either) found that multi-round
loop's implied precision is **0.03%-0.45%** (56/31,168, 202/44,577, 42/150,197 papers visited to
reach that recall) — because that eval explicitly measures pure graph reachability with **no LLM
screening in the loop** (named as a gap in §1 since this file was split out, but never quantified
until this check). So neither "single-hop operator" nor "unscreened multi-round traversal" is a
fair baseline on its own — comparing raw recall numbers between them (as every experiment in this
file has done) mixes up two different things. The right fix, per both this fairness problem and
the composition failure above, is a **budget-normalized comparison** (§4.7 below, scoped since this
file's creation, never built) rather than another raw-recall patch.

**Status: paused, not abandoned — see the ⏸ box at the top of §4 for the full stopping rationale.**

### 4.7 Retrieval budget (this is where "efficiency" lives)

Every operator has a cost — S2 calls, LLM calls, wall-clock time. An uncontrolled comparison lets
the most expensive combination win by default (more calls → more candidates → higher recall,
trivially). Fix a budget (e.g. 100 S2 queries, 50 embedding searches, 20 LLM calls) and compare
recall **under equal budget**, not recall unconditionally. This is the same yield/cost concept
`traverse.py`'s stopping rule already uses internally, generalized across operators instead of
just within traversal rounds.

**✅ Measurement primitive built — done 2026-07-14, via TDD** (`litdiscover/discovery/budget.py`):
`run_with_cost(operator_fn, *args, **kwargs) -> (OperatorResult, CostMetrics)` measures any
operator externally (S2 calls via a delta on `s2_client`'s shared call counter, wall-clock time,
candidates returned) with zero changes to the operator itself — one wrapper works uniformly
across all 5 operators and `traverse()`. `recall_per_call(cost, new_gold_found)` is the
§4.4/§4.7 metric itself, pure arithmetic — it takes the gold-match count from the caller rather
than knowing about gold standards itself, since that's a §4.2 concern, not a cost-accounting one.
10 new tests, 227/227 passing project-wide. **This is the measurement tool, not the experiment
run** — actually executing recall-under-equal-budget comparisons still needs the gold standard
(§4.2, deferred per §7 step 2) and the operators to run against real included-paper sets, not
just unit-test mocks.

### 4.8 Retrieval curves (Pareto frontiers)

Report curves, not single numbers: recall vs. number of operators fired, recall vs. LLM calls,
recall vs. total papers retrieved. These become Pareto frontiers — for a fixed cost, which
operator combination dominates. This is the natural visualization for §4.6's ordering results and
§4.7's budget results together, not a separate analysis.

### 4.9 Statistical testing

Across the (expanded, per §4.2) survey set, each survey yields a paired (RecallA, RecallB) for any
two operator combinations being compared. Paired t-test if normality assumptions hold; Wilcoxon
signed-rank otherwise (safer default given the sample sizes involved). This is what turns "method
A got higher recall on our 6 surveys" into an actual claim of significance rather than an anecdote
— currently absent from every recall number this project has reported so far, including the
existing 89-98%/73-100% headline results.

### 4.10 What's actually novel about this framing

Most prior work in `deep-dives.md`'s 27-method survey (§2) compares whole *algorithms* against
each other (AutoSurvey vs. SurveyX vs. LitLLM). This experiment compares retrieval *operators* —
a subtler, more useful question: not "which existing tool wins" but "what primitive operations are
necessary to recover a research field, and in what combination." That's closer to systems-design
methodology than typical IR-tool benchmarking, and — per the §2 survey — nobody else in the field
has framed it this way. Worth stating explicitly in the paper as a methodological contribution,
not just an engineering exercise.

### 4.11 Deferred: retrieval as a sequential decision problem

A more ambitious formulation, explicitly **not** in scope for this experiment but worth recording
now rather than losing: model discovery as a sequential decision problem — state = current
discovered paper set, action = choose next operator to fire, reward = new relevant papers found,
termination = marginal recall gain < ε. The question becomes "what is the optimal retrieval
policy," which connects to active search / adaptive IR / RL rather than a fixed ablation. Useful
framing to keep in mind while designing §4.1's operator interface (a clean `operator(state) →
candidates` contract is a prerequisite for this too, so building it well now doesn't foreclose the
option later) — but the policy-learning question itself should wait until §4.3-§4.9 are done and
there's real per-operator marginal-value data to learn a policy from.

---

## 5. Simulation vs. production gap — read before ablating any new method

The APS closed-corpus simulation (`04b_cold_start_lowseed.py`) and the production engine
(`intake/traverse.py`) implement the same core idea with different engineering constraints. Any
new discovery method built and validated in one won't automatically transfer to the other — this
bit the Pareto filter once already and will bite again if a new method is prototyped in whichever
environment is more convenient without checking the other's semantics.

**Same core logic, different expression:**

```
Simulation: traverse (BFS, depth-by-depth) → check yield per depth → stop when yield < 5%
            → escape hatch (top-K graph-neighbours by in-degree) → repeat N_ROUNDS times
Production: traverse (one pass over all included papers) → screen candidates
            → check yield per cycle → escape hatch (LLM-generated query → S2 keyword search)
            → repeat until stable
```

**Where they genuinely diverge — the Pareto filter direction (settled, but worth restating
precisely):**

| Dimension | APS simulation | Production |
|---|---|---|
| Pareto filter target | Forward candidates (citers), filtered by their own **out-degree** | Frontier papers, filtered by their own **in-degree** (citation_count) |
| Filter calibration | Fixed percentile, swept as a hyperparameter | Adaptive — Gini-coefficient of the included set's citation counts picks 80th/90th/95th percentile per round |
| Escape hatch | Top-K graph-neighbours by in-degree (still graph-only) | LLM-generated keyword query against S2 — can reach papers with **no graph path** to the found set at all |
| Ground truth | Known gold bibliography, exact recall | None — screen_yield is a proxy, not a direct recall measurement |

**Concrete failure mode this causes:** a domain survey that cites 400 relevant physics papers but
is itself cited by only 30 papers. Production lets it through (low citation_count → forward
traversal proceeds normally, its 400 refs enter the corpus — correct). The simulation would
instead risk *removing the survey itself* from the forward candidate set, because the filter
there looks at the citer's own out-degree, and a paper with 400 references looks "survey-like" by
that measure. In practice this is rare (the problematic high-out-degree citer usually is a
specialist paper, not a genuine survey), which is why the simulation's recall numbers hold up —
but it means a discovery-method result validated only in the simulation hasn't actually validated
production's filter semantics.

**Why this matters for the §4 ablation:** the simulation's escape hatch is graph-expansion only
— it works on APS because misses happen to sit at BFS distance 1 from the found set. Production's
LLM-keyword escape hatch is strictly stronger because it isn't constrained to the graph at all.
Any of the new methods proposed in §3 (author/venue/recency search) are, by construction,
non-graph methods like the keyword escape hatch — which means **they can only be properly
validated against production's semantics or the live-survey track, not the APS simulation.** The
APS simulation has no way to represent "a paper this method finds that has no citation-graph path
to anything else in the corpus" as a meaningful test case, since its own escape hatch is graph-only.

---

## 6. Discovery's role in the shared cross-stage benchmark

The 6 surveys (S1-MIT, S2-UCG, S3-TOPO, K17-RGC, Ge21-HSS, Le25-GLLM) currently ground-truth
discovery only (recall against each survey's own reference list) — this is the one stage of the
three-stage pipeline (see `research-roadmap.md` §4) that already has this. §4's Experiment 1
reuses the same 6 as its Cranfield-style gold standard rather than requiring new ground truth,
modulo the expansion needed for §4.9's significance testing.

## 7. Open decisions before building any of this

**Sequencing, in order — each step below is a prerequisite for the next, not a menu:**

1. ✅ **Decompose `traverse.py` into the operator interface (§4.1) — done 2026-07-14.**
   `backward_traversal_operator()`, `forward_traversal_operator()`, and
   `pareto_hub_threshold()` now exist as independently callable functions sharing a common
   `OperatorResult(candidates, edges, stats)` contract; `traverse()` is a thin orchestrator
   composing all three with its public signature/return shape unchanged (verified against
   `core/stages.py`'s call site and the full existing test suite, 181→189 passing with 12 new
   operator-level tests). `forward_traversal_operator()` defaults to `hub_threshold=inf`
   (unfiltered) — the Pareto filter is now opt-in via `pareto_hub_threshold()`'s output, not
   baked into forward traversal itself, which is what makes an unfiltered-forward-traversal
   ablation arm possible without a code fork.
2. **Decide whether to expand the gold standard beyond 6 surveys (§4.2) now or defer it.**
   §4.3-§4.8 (baselines through Pareto curves) can run meaningfully on the existing 6; only §4.9
   (paired significance testing) actually needs the larger set. Expanding now front-loads cost for
   a step that comes last — worth deciding explicitly rather than defaulting to "more data can't
   hurt."
3. ✅ **All five remaining operators built — done 2026-07-14, via TDD.** Author expansion,
   venue expansion, recency-only search, embedding search (S2 Recommendations API), and
   co-citation retrieval (`litdiscover/discovery/operators.py`) all implemented — tests written
   first (confirmed RED against the not-yet-existing functions), then minimal implementation to
   pass (GREEN), no refactor needed. 28 new tests (13 operators + 15 from the first pass),
   217/217 passing project-wide. Every operator's network calls are verified against the live S2
   API before implementation, not guessed (confirmed exact response envelopes for
   `/author/search`, `/author/{id}/papers`, `/paper/search`'s `venue`/`year` filters, and
   `/recommendations/v1/papers/forpaper/{id}` — the last one has a different response key
   (`recommendedPapers`) than the others (`data`), which would have been an easy silent bug to
   ship unverified).
4. ✅ **Precision/budget measurement primitive built — done 2026-07-14, via TDD** (§4.7).
   `litdiscover/discovery/budget.py`'s `run_with_cost()`/`recall_per_call()` — see §4.7 for
   detail. 10 new tests, 227/227 passing project-wide. **Still open:** this is the reusable
   measurement tool, not a completed ablation/ordering result — running an actual
   recall-under-equal-budget comparison (§4.5/§4.6) needs the expanded gold standard (§4.2,
   deferred per step 2) and real operator runs against included-paper sets, not just the unit
   tests' mocked S2 responses.
5. ✅ **Baselines + marginal contribution (§4.3/§4.4) run against all 3 live surveys — done
   2026-07-14** (`live-survey-eval/scripts/10_operator_benchmark.py`). Headline finding:
   **co-citation is the only non-traversal operator that adds gold on every survey**, and by a
   wide margin on Ge21-HSS; embedding search and venue expansion found zero new gold anywhere in
   this run. See §4.3 for the full table and caveats (single-pass isolated-operator numbers, not
   multi-round production recall; intermittent 429s on the author/recommendations sub-APIs
   undercount those operators' true yield — a real gap, not just noise).
6. ✅ **429 retry/backoff added to `s2_client._s2_wait()` and `operators.py`'s raw calls — done
   2026-07-14**, after checking S2's own docs rather than guessing at backoff parameters. A
   standard S2 API key gets a flat 1 req/sec cap *across all endpoints*
   (semanticscholar.org/product/api/tutorial), not a stricter separate budget for
   author/recommendations specifically — the real cause of observed 429s was `_s2_wait()`'s 1.05s
   minimum interval leaving no jitter margin, combined with zero retry-on-429 in `operators.py`'s
   four raw calls (which don't route through `s2_client`'s already-protected `_fetch_edges`). Fix:
   `_get_json()` in `operators.py` now shares `s2_client._fetch_edges()`'s exact tenacity retry
   pattern; minimum interval widened 1.05s→1.2s. Also added a shared `log_retry_attempt()`
   before-sleep callback (in `s2_client.py`, reused by `operators.py` and `search.py`) so retries
   are visible in script output as `[s2-retry] ...` traces instead of silent until success/failure.
7. ✅ **§4.5 ablation (leave-one-out) run — done 2026-07-14**, confirmed retry fix live via real
   `[s2-retry]` traces during the run, and consolidated `10_operator_benchmark.py` to derive
   §4.3/§4.4/§4.5 from one pass per operator instead of re-invoking operators per measurement (see
   §4.5 for the full table). Co-citation is the only operator with a nonzero ablation drop on
   every survey.
8. ✅ **Precision tracking added — done 2026-07-14.** Neither this file's operator work nor the
   *original* multi-round traversal validation (§1) had ever measured precision, only recall.
   Added `_precision()` to `10_operator_benchmark.py`/`12_chained_composition.py` and retroactively
   checked `09_live_validation.py`'s own saved output — see the ⏸ box at the top of §4 and the end
   of §4.6 for what this revealed (full-union precision 0.3-4.7%; original system's multi-round
   recall implies 0.03-0.45% precision, since that eval never screens).
9. ⏸ **§4.6 Composition experiment attempted, then paused — done/stopped 2026-07-14.** Chained
   execution made both recall and precision worse on the one survey completed, root cause
   diagnosed (unfiltered forward traversal + citation-count frontier selection compounding into a
   noisy corpus) — see §4.6's end-of-section writeup. This also surfaced a fairness problem in
   every §4.3-§4.6 comparison (single-hop operators vs. the original system's multi-round loop).
   **Next, if this resumes:** a budget-normalized comparison (§4.7, never built) rather than
   another raw-recall patch — see the ⏸ box at the top of §4 for the full rationale on why this
   is paused rather than continued immediately.
