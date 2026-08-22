# LitDiscover

## Question

Can a field be recovered from a few seed papers with useful end-to-end recall
and precision under an explicit discovery budget?

## Current state

The engine and external evaluation infrastructure exist, but the primary
evaluation has been redefined around the final screened corpus rather than raw
graph reachability. A human-steered pipeline remains a candidate replacement
for the engine's discovery stage. No formal comparison between them is running.

## What we know

- [Raw traversal recall without screening produced only 0.03–0.45% implied
  precision](../../archive/wiki-legacy/litdiscover/litdiscover.md).
- [Co-citation replicated as the strongest non-traversal signal](../../archive/wiki-legacy/evaluation.md)
  across live surveys and the independent SYNERGY corpus.
- Chaining can outperform isolated operator unions, but the effect of filtering
  depends on which operator follows it.

## Open

- Whether the manual pipeline should replace the engine.
- The real citation-grounding precision of synthesis on a non-fixture project.

## Next

Run the existing citation-grounding check on one real project and record the
measured precision before redesigning synthesis further.

[Detailed archived record](../../archive/wiki-legacy/litdiscover/litdiscover.md)
