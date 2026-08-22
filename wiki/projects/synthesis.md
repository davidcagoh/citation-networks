# Synthesis

## Question

Which representation of a recovered paper set best exposes recognizable
research threads, methodological relations, and evidence-backed claims?

## Current state

The graph-native K17-RGC subgraph exists, section-level ground truth is prepared
for the representation comparison, and the LLM-text-native control is complete.
The Literature Workbench now supplies a provenance-preserving deterministic
vertical slice, but that fixture demonstrates engineering behavior rather than
scientific improvement.

## What we know

- [The text-native control lost 20 of 32 real citation edges and fabricated
  three](../../archive/wiki-legacy/synthesis/synthesis.md), showing that a flat
  single-membership partition cannot represent the field's observed topology.
- [No mature independently validated synthesis-quality metric exists](../../archive/wiki-legacy/evaluation.md).
- The full-corpus NST result currently argues against assuming that a
  direction-aware embedding will recover meaningful temporal structure.

## Open

- Whether relation-aware, provenance-preserving planning improves a review over
  a paper-list baseline.
- How to score hierarchical survey structure fairly across representations.
- Whether K17-RGC's APS coverage is sufficient for domain-valid graph claims.

## Next

Specify and freeze E001: relation/provenance-backed planning versus a paper-list
baseline on one fixed supplied corpus.

[Detailed archived record](../../archive/wiki-legacy/synthesis/synthesis.md)
