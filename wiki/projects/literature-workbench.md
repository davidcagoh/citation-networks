# Literature Workbench

## Question

Can one local-first, inspectable system turn a research brief or seed set into
a defensible evidence-grounded literature review?

## Current state

The Workbench is the functional successor to both LitDiscover and Synthesis.
Its architecture spans discovery, acquisition, evidence extraction, scientific
relations, planning, grounded writing, and verification. The deterministic
five-paper fixture path is complete, and live Semantic Scholar discovery now
persists abstract provenance. A user can screen live candidates, build an
abstract-backed grounded review, inspect its evidence, verify claims, edit the
plan, and export Markdown, JSON, or BibTeX. Live extraction is intentionally
conservative: it quotes bounded provider abstracts and does not invent
cross-paper relations or full-text findings.
Scope preview and a persisted per-run paper budget are also available; live
provider calls appear in the cost ledger separately from local deterministic
stages.

No formal experiment is running.

## What we know

- [Discovery must be evaluated at the final screened corpus](../../archive/wiki-legacy/litdiscover/litdiscover.md),
  because high traversal recall can coexist with unusably low precision.
- [A flat text-native partition discarded 20 of 32 real citation edges and
  fabricated three](../../archive/wiki-legacy/synthesis/synthesis.md), so useful
  review structure cannot be assumed from fluent output.
- [No mature independently validated synthesis-quality metric exists](../../archive/wiki-legacy/evaluation.md);
  provenance and claim grounding therefore require explicit evaluation.

## Open

- Whether relation-aware, provenance-preserving planning improves a review over
  a paper-list baseline.
- Which former LitDiscover methods should become live discovery adapters and
  whether they meet explicit recall, precision, cost, and stopping budgets.
- Full-text acquisition, structured model-backed extraction, budget gates, and
  richer verification remain to be implemented before calling the system a
  thorough-review tool.
- Which graph-, embedding-, or text-native representation methods add value in
  the unified planning stage.

## Next

Specify and freeze E001: relation/provenance-backed planning versus a paper-list
baseline on one fixed supplied corpus, then use live abstracts as the first
external-provider smoke test.

## Predecessor records

- [LitDiscover](../../archive/wiki-legacy/litdiscover/litdiscover.md)
- [Synthesis](../../archive/wiki-legacy/synthesis/synthesis.md)
