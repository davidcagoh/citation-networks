# Discovery protocol log

Source of truth for **what configurations of the discovery algorithm/protocol have been tried and
whether they were kept** — distinct from `session-log.md` (chronological narrative of everything
that happened) and `litdiscover.md` (current status + the single benchmark table). This file is
where you look when deciding what to try next, before opening a session log to reconstruct it.

Two tables:
- **Protocol variants** — conceptual-level designs (which mechanisms run, how combined). One row
  per distinct design, verdict = where it landed.
- **Run log** — concrete trials of those variants against real data. One row per actual run.

Update this whenever a new variant is tried or a verdict changes — don't let it drift back into
prose-only session-log entries.

---

## Building blocks

Operators and modes referenced by shorthand in the composition table below.

**Operators** (candidate-producing mechanisms — `OperatorResult(candidates, edges, stats)`):

| Code | Operator | Derives query from | Live signal (isolated, see Run log) |
|---|---|---|---|
| `BWD` | backward_traversal | paper's own refs (PDF-first, S2 fallback) | +5/+2/+0 gold across 3 surveys |
| `FWD` | forward_traversal | paper's own citers (S2 only) | +0/+1/+0 |
| `CO` | co_citation | seed set's citers' shared refs | **+4/+19/+2 — best, only nonzero on every survey** |
| `AUTH` | author_expansion | paper set's own authors | +0/+7/+0 |
| `VENUE` | venue_expansion | paper set's own venue + year window | 0/0/0 |
| `RECENCY` | recency_search | caller-supplied query string | +1/0/0 |
| `EMBED` | embedding_search | S2 SPECTER recommendations | 0/0/0 |
| `KEYWORD` | keyword search (manual pipeline only, not one of the 7) | human-chosen query, iterated | not benchmarked against gold — see manual pipeline row |

**Modes** (control/workflow choices, not candidate-producing):

| Code | Mode | Options tried | Kept |
|---|---|---|---|
| `WORKFLOW` | how stages advance | `staged` (human triggers each step) vs `autopilot` (auto-chain to STABLE) | `staged`, default since 2026-07-09; `autopilot` still opt-in |
| `HUBFILTER` | forward-traversal hub skip | `gini-adaptive` (80th/90th/95th by Gini) vs `fixed-80th` | `gini-adaptive` in production; `fixed-80th` is a simulation-only approximation |
| `COMPOSE` | how multiple operators' outputs combine | `isolated` (each measured alone) vs `chained` (sequential, output feeds next) | `isolated` only — chained tried once, rejected |
| `SCREEN_LLM` | screening backend | `gemini-2.5-flash` vs `llama-3.1-8b-instant` | `gemini-2.5-flash` |
| `HUMAN_STEER` | who drives mode-switching/stopping decisions | `engine` (yield-threshold gate, fully automatic) vs `human` (manual pipeline, judgment call each time) vs **`checkpoint`** (proposed 2026-07-31: autopilot's automation runs each operator to completion, but pauses after every operator finish to surface its output + a proposed next step, human gives go/no-go before continuing — turn-based, not manual-labor) | undecided — this is the live question; `checkpoint` is the direction favored in discussion, not yet built |

---

## Protocol variants (composition shorthand)

| Composition | Tried | Verdict | Why |
|---|---|---|---|
| `BWD + FWD` · `WORKFLOW=autopilot` | 2026-07-08 and earlier, production default until 2026-07-09 | **Demoted** — `WORKFLOW=staged` now default | Silent 0%-yield retry burned ~13 rounds after a spend-cap error; nothing gated the loop except the loop itself. |
| `BWD + FWD` · `WORKFLOW=staged` | Adopted 2026-07-09 | **Kept, current production** | Human+agent eyeballing a keyword-prefiltered list caught ~60 false positives an LLM screen likely would've missed. Rule: never `screen` a queue >~50 without `prefilter` first. |
| `BWD + FWD` alone (any workflow) | Production, ongoing | **Kept but flagged** — pipeline-level precision unverified | 89–98%/73–100% recall headline never had precision checked until 2026-07-14 — implied precision was 0.03–0.45%, since that number is pure graph reachability with zero screening. Fix is an end-to-end metric, not a different operator set. |
| `BWD + FWD + CO + AUTH + VENUE + RECENCY + EMBED` · `COMPOSE=isolated` | Benchmarked live 2026-07-14, all 3 surveys | **Mixed** — `CO` promoted, `EMBED`/`VENUE` demoted | See Run log. `EMBED`/`VENUE` partly confounded by a since-fixed 429-undercounting bug — not fully disambiguated from a true null. |
| `FWD (unfiltered) + [citation-count frontier]` · `COMPOSE=chained` | Tried once, 2026-07-14 | **Rejected — refined below, not overturned for this exact design** | Both recall and precision got worse — noisy corpus, generic hub papers from the unfiltered forward step. |
| `COMPOSE=chained` (BWD/FWD/AUTH/VENUE/CO, 12 sequences × isolated/chained-unfiltered/chained-filtered-by-gold-label) · SYNERGY `Hall_2012` closed corpus | 126-condition sweep, 2026-08-01 | **Chaining works in general; filtering's value is operator-position-dependent, not universal** | Chaining beats isolated-union almost everywhere (`BWD→FWD→AUTH`: 50.5% recall chained vs. 11.9% isolated) — the 2026-07-14 rejection was about *that specific unfiltered design*, not chaining itself. Filtering helps precision a lot when it precedes a high-fan-out operator (`BWD→FWD`: 21.5%→60.7% precision, zero true-positive cost) but can cost real finds when it precedes a low-fan-out one (`FWD→BWD`: lost 2 of 9 marginal gold). See `wiki/evaluation.md` for full numbers. |
| `HUBFILTER=gini-adaptive` (applies to `FWD`) | Production since early v2 | **Kept** | Prevents small-topic projects from starving their traversal frontier under one fixed threshold. |
| `HUBFILTER=fixed-80th` | Simulation only (`N_ROUNDS`/`PARETO_P` sweeps), never production | **Kept as approximation only** | Explicit in `litdiscover.md`: stand-in for tractability, not a claim about production semantics. |
| `SCREEN_LLM=gemini-2.5-flash` | Production | **Kept** | `llama-3.1-8b-instant` tried and rejected — too permissive, high false-include rate. |
| `KEYWORD (iterated) + FWD (age-targeted) + CO (fallback-anchor) + [reconcile]` · `HUMAN_STEER=human` | Dogfooded on 2 surveys, 2026-07-21 (session 44) | **Undecided — gates everything else** | Motivated by `CO` being the one operator with real isolated signal. Surfaced 3 stages the engine has no analog for: citation-verification gate, redundancy reconciliation, yield-based *mode-switching* (not just stopping). Not decided whether these get built into the engine (`HUMAN_STEER=engine`) or the manual path stays primary. |
| `KEYWORD (context-conditioned escape hatch)` | **Proposed 2026-07-31, not yet built or tried** | — | Diagnosed why the existing escape hatch underperforms the manual pipeline's query refinement: it's not human-vs-LLM, it's *starved context*. Today's escape hatch conditions the refinement LLM call on the static `criteria` text only — blind to what actually happened. Proposal: condition it on prior round's screening outcomes (which papers included/excluded and the LLM's stated reason), extraction notes from included papers, and a diff of criteria changes across rounds (what changed and why). Same shape as `keyword_search_operator`'s existing call site (`core/loop.py`'s escape-hatch trigger) — a richer prompt, not a new operator contract. Not started; needs its own isolated benchmark before promotion, same as `CO` got 2026-07-14. Composes with `HUMAN_STEER=checkpoint` below — a checkpoint's human go/no-go at each step is itself free context (accept/reject + why) this richer prompt could condition on next round. |

---

## Run log

| Date | What ran | Config | Result | Verdict/note |
|---|---|---|---|---|
| 2026-07-14 | Closed-corpus canonical result (`eval/04b`) | Old Pareto filter (bug: filtered candidates by their own out-degree, not the frontier's) → fixed | Recall 93.5%→99.6% mean, mean corpus size 3.1× smaller after fix | Real filter-design bug, not a config choice — but changed what "the Pareto filter" means going forward. Left `05_miss_analysis.py`'s canonical condition with zero misses, so Fig 7 has nothing to plot — paused, unresolved paper-facing decision. |
| 2026-07-14 | Original system's own validation, precision checked for the first time | 73–100% recall headline (pre-existing), screening added post-hoc | Implied precision 0.03–0.45% | The finding that reframed everything below it — precision's denominator is discovery-dependent, so isolated recall numbers aren't defensible evidence alone. |
| 2026-07-14 | Live 7-operator isolated benchmark, all 3 surveys (K17-RGC n=56, Ge21-HSS n=202, Le25-GLLM n=57), single-pass | Each operator run independently, no chaining | backward: +5/+2/+0 gold · forward: +0/+1/+0 · **co-citation: +4/+19/+2** · author: +0/+7/+0 · embedding: 0/0/0 · venue: 0/0/0 · recency: +1/0/0 | Co-citation → promote. Embedding/venue → demote (partly confounded by a 429-undercounting bug on author/embedding calls during this run, since fixed — not fully disambiguated from a true null result). n=3, directional not powered. |
| 2026-07-14 | Naive chained composition, follow-up to above | Unfiltered forward traversal + citation-count frontier selection, sequential | Both recall and precision *worse* than isolated operators | Rejected. Root cause: noisy corpus from unfiltered forward step surfaces generic hub papers. |
| 2026-07-21 (session 44) | Manual pipeline run #1 — A-Share Strategy Survey | Keyword search (4 rounds) → curate/extract (graduated depth) → forward citation (age-targeted) → co-citation (fallback-anchor) → reconciliation pass (ad hoc, not pre-planned) | 26 pre-existing notes + growth to 38 Zotero items; reconciled 5 overlapping candidates → ~3-4 real mechanisms; found the single strongest execution-gap evidence (18% IC inflation / −0.44 Sharpe from price-limit contamination) | Liked the forward-citation age-targeting rule and the reconciliation pass enough to flag both as missing engine stages. Round 3 (plain keyword) showed the stopping signal (declining yield) working as expected. |
| 2026-07-21 (session 44) | Manual pipeline run #2 — Trading Eval Methodology Survey | Same stages, seeded from a sibling project's bibliography | 12 items, 2 dropped as unverifiable/likely-hallucinated citations (caught by the verification gate) | Verification gate validated as load-bearing, not a nice-to-have — caught real hallucinated citations mid-run. |
| 2026-08-01 | SYNERGY `Hall_2012` isolated 5-operator baseline (BWD/FWD/AUTH/VENUE/CO-via-`FWD∘BWD`), top_k seeds, k∈{1,2,3} | `evals/synergy-eval/scripts/eval/01_isolated_baseline.py`, real production operators via `source="local_corpus"` | CO best recall/precision balance (19–29% recall, 49–65% precision) · FWD unexpectedly strong (37% recall @k=3) vs. dead on live S2 | CO's standout status now corroborated on a second, independent corpus, not a fluke of the live-survey benchmark. FWD's live-S2 weakness is corpus-shape-dependent (open-web noise), not universal — closed-corpus FWD stays inside an already-topic-filtered pool. |
| 2026-08-01 | SYNERGY `Hall_2012` composition sweep, 12 sequences × 3 `COMPOSE` modes × 9 seed conditions, full per-stage diagnostics | `evals/synergy-eval/scripts/eval/02_composition_sweep.py`, 55/55 tests, TDD throughout | Best: `BWD→FWD→CO→VENUE` chained-unfiltered k=3, 76.2% recall/27.2% precision. `FWD→FWD` dead everywhere (~1% recall). Any `VENUE`-terminated sequence craters precision (13–27% vs. 44–80%) | See `COMPOSE=chained` row above and `wiki/evaluation.md` for the full write-up. Caught and fixed a bug in the overlap diagnostic mid-build (structurally guaranteed 0.0, not a null result) before reporting any numbers. |

---

## Reading order for "what should the algorithm actually be"

1. Protocol variants table above — what's been tried at the design level and where it landed.
2. `litdiscover.md`'s Discovery section — current benchmark table + the end-to-end-metric gap that's still unbuilt.
3. `manual-pipeline-retrospective.md` — the fullest single account of what a human actually does that the engine doesn't yet.
