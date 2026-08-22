# Manual composable-pipeline retrospective (2026-07-21)

**What this is:** a retrospective on running the manual pipeline described in
`lit-review-bot/projects/china-ashare-strategy-survey/README.md` and
`lit-review-bot/projects/trading-eval-survey/` end-to-end — keyword search → curate/extract →
refine → forward citation → co-citation — explicitly as a dogfooding exercise to figure out
what a LitDiscover replacement or redesign actually needs, rather than to produce a literature
survey as an end in itself (see [[project_litdiscover_replacement_exploration]]-type framing from
the session that started this). Both project READMEs hold the survey content; this file holds
what the run itself taught about the *process*.

## What actually got run

Two Zotero collections (group library `6619241`): `Trading Eval Methodology` (12 items, deep
full-text extraction throughout) and `A-Share Strategy Survey` (38 items, mixed extraction depth —
deep for central papers, abstract-level for peripheral ones). Stages run, in order: initial
keyword search → curate → extract → three further keyword-refinement rounds → forward citation →
co-citation (attempted) → a reconciliation pass that wasn't in the original plan at all.

## Findings that matter for a LitDiscover redesign, not just this survey

**1. A "reconcile for redundancy" stage is missing from the planned pipeline, and turned out to be
necessary.** Five independently-found candidates in the A-share survey (daily momentum, last-hour
momentum, overnight-MAX, day-night institutional timing, turnover-crowding) were flagged as
*possibly* redundant with each other at the moment each was found, then left unresolved for three
rounds. Only a dedicated reconciliation pass — comparing mechanism/horizon/investor-attribution
across notes already in hand, no new search — resolved it (to ~3-4 real independent mechanisms,
not five). This is a distinct stage from curation (which happens per-item, at discovery time) and
from synthesis (which narrates, but doesn't cross-check, findings). LitDiscover's current pipeline
(`SEED → DISCOVER → SCREEN → EXTRACT → SYNTHESIZE`, per `research-roadmap.md` §0) has no analogous
stage — extraction is per-paper, synthesis clusters papers by theme but doesn't explicitly check
whether two differently-themed clusters are secretly describing the same underlying phenomenon.

**2. Forward-citation targeting has a real, non-obvious rule: seminal + old-enough-to-have-a-
citation-trail, not "most relevant" or "most recent."** A 2026 preprint returns ~0 forward
citations regardless of relevance — the citation trail literally hasn't had time to form. This
was learned by trying it wrong first (nearly picked recency as the criterion) before landing on
citation-age as the actual constraint. Worth encoding explicitly if `forward_traversal_operator`
or a future citation-chase stage is parameterized — filtering candidate seed papers by age/citation
count before running forward-traversal on them, not just by topical relevance.

**3. Co-citation as originally conceived (mine an anchor paper's citers for shared references) hit
a real operational wall: a paywalled publisher (Elsevier, via the S2 API) elides the `references`
field for one of the two best-connected anchor papers tried. The practical fallback — mine a
different, openly-accessible, well-cited paper's own reference list instead, in the same topic
neighborhood — worked comparably well. A formalized co-citation operator needs this fallback path
built in, not just a single anchor-paper attempt with no recovery if it 404s on data availability.

**4. Yield-tracking as an explicit stopping criterion, introduced by the user mid-session
("one more search and see if yield is high or mostly overlap"), converged independently on the
same idea LitDiscover's own autopilot loop already formalizes** — `cycle_yield` (new-genuinely-
useful-finds ÷ total candidates this round), gating whether to run another cycle or declare
stable (`core/loop.py`, `yield_threshold`/`stale_rounds` in `research-roadmap.md`/CLAUDE.md). Round
1 (thrust re-search) was high-yield; round 3 (another keyword round) was low-yield/mostly-overlap;
round 4 (co-citation-adjacent) was high-yield again on a different axis (execution-cost data, not
new signals). This is a real, useful signal for when to stop a given search *mode*, but it doesn't
by itself tell you to switch modes (keyword → forward-citation) rather than just stopping — that
mode-switching decision was a user judgment call each time, not something the yield number alone
implied.

**5. A citation-verification gate is mandatory, and catching a failure was informative.** Two
citations in a *different* project's own seed bibliography (`algo-traders/paper/references.bib`)
turned out to be unverifiable/likely-hallucinated — including, pointedly, a citation about LLMs
hallucinating trading strategies. Caught only because each candidate paper was checked against a
real search/resolution before being trusted, not because anything flagged it automatically.
LitDiscover's own `verify` command already does something structurally similar (re-resolves
included papers against S2, flags title drift) — this experience is independent confirmation that
step is load-bearing, not a nice-to-have, and should run on *every* candidate before extraction,
not just as a pre-submission audit of an already-included set.

**6. Single-pass curation has a real false-negative rate.** The single strongest piece of evidence
found for the entire RQ (the mask-first/execution-gap paper, arXiv:2507.07107) was initially
triaged *out* of the survey in the very first curation pass, mislabeled as "general ML." It was
only recovered by chance during an unrelated later broad-search round. A curate stage that only
runs once, on first sight of a candidate, will drop real hits — either curation needs a
lower-precision/higher-recall first pass with a cheap re-review, or excluded items need to stay
visible enough to be re-caught when later themes make their relevance obvious.

**7. Extraction depth should be graduated, and this wasn't planned upfront — it emerged.** Central/
foundational papers got full-text, multi-page extraction; peripheral papers got abstract-level
extraction explicitly flagged as lower-confidence. This proportionality (effort matched to a
paper's centrality to the RQ, decided qualitatively per-paper) was more efficient than uniform-
depth extraction would have been, but "how central is this paper" isn't knowable until after
initial extraction — meaning a two-tier extraction process (cheap first pass, deep second pass
only for papers that turn out to matter) would need its own triggering logic, not a fixed budget
per paper.

**8. Shared/group reference libraries carry contamination risk that needs explicit scoping.** The
Zotero group library used for this survey turned out to already contain ~82 items from an unrelated
concurrent automated job (a "weekly search" for a different, ended competition) — genuinely
on-topic-looking, which made it briefly look like a conflicting concurrent session before being
clarified. Working in dedicated Zotero *collections* (not just the shared library) contained this
correctly once understood, but the disambiguation itself cost real back-and-forth. A pipeline that
writes into shared storage should check for and surface unexpected pre-existing content before
proceeding, not assume a freshly-created collection means a clean slate at the library level too.

## Net read: what should carry forward into a LitDiscover redesign

The four originally-planned stages (keyword search, curate/extract, refine, forward-citation +
co-citation) are all real and each earned their place — but the actually load-bearing pipeline
has at least three more implicit stages this run made visible: **citation verification** (gate,
not audit), **redundancy reconciliation** (cross-check extracted findings against each other, not
just within a single item), and **yield-based mode-switching** (not just yield-based stopping).
None of these are novel insights about research methodology — they're closer to "things an
experienced human researcher does without naming them" — but that's exactly the value of having
dogfooded this manually before deciding what to automate: they're nameable now, and each has a
concrete trigger and failure mode observed directly in this run, not hypothesized.
