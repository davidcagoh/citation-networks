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
| **JASIST** | Journal | ⭐⭐⭐ Good | Longer cycle (6–12 months); no page limit — better for full rewrite. |
| **CIKM / SIGIR 2026** | Conference | ⭐⭐ OK | More competitive; needs stronger retrieval theory framing. |

**Decision (2026-04-21):** Submitting to **JCDL 2026** (June 30 deadline). ICASR 2026 call not yet live; JCDL deadline is concrete and the fit is strong. EasyChair record filed.

---

## Naming: LitDiscover (not "LitReview v2")
**Decision date:** ~2026-04-06
**Why:** "LitReview" sounds like the output (a review). "LitDiscover" is the process (discovery).
**Status:** ✅ Renamed throughout — pyproject.toml, CLI, and paper draft.
