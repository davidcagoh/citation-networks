# Literature Workbench

## Question

Can one local-first, inspectable system turn a research brief or seed set into
a defensible evidence-grounded literature review?

## Current state

The Workbench is the functional successor to both LitDiscover and Synthesis.
Its architecture spans discovery, acquisition, evidence extraction, scientific
relations, planning, grounded writing, and verification. Slice 1 implements a
deterministic vertical path over a supplied five-paper fixture with claim-level
evidence inspection. This establishes engineering behavior, not scientific
improvement. Live discovery and external-model workflows remain pending.

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
- Which graph-, embedding-, or text-native representation methods add value in
  the unified planning stage.

## Next

Specify and freeze E001: relation/provenance-backed planning versus a paper-list
baseline on one fixed supplied corpus.

## Predecessor records

- [LitDiscover](../../archive/wiki-legacy/litdiscover/litdiscover.md)
- [Synthesis](../../archive/wiki-legacy/synthesis/synthesis.md)
