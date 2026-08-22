# Citation Networks

## Question

Can literature discovery and synthesis be unified in an auditable workbench,
and which citation-network structures meaningfully improve its account of a
field?

## Current state

No formal experiment is running. There are two active programs:

| Program | Current state |
|---|---|
| [Literature Workbench](projects/literature-workbench.md) | Unified functional successor to LitDiscover and Synthesis. Its supplied-corpus provenance slice works; live discovery and scientific evaluation remain pending. |
| [Zeitgeist](projects/zeitgeist.md) | Independent analytical program. §§1–4 paper draft complete; awaiting review feedback; post-paper temporal-layout question remains active. |

## What we know

- [Discovery must be evaluated end to end](../archive/wiki-legacy/litdiscover/litdiscover.md):
  high raw traversal recall can coexist with unusably low precision once
  screening is omitted.
- Co-citation is the strongest non-traversal discovery signal tested so far and
  [replicated across the live-survey and SYNERGY evaluations](../archive/wiki-legacy/evaluation.md).
- [The APS citation graph decomposes into temporally localized communities](../archive/wiki-legacy/zeitgeist/codebase-map.md)
  with distinct fitted power-law exponents.
- [No mature independently validated standard currently measures scientific
  synthesis quality](../archive/wiki-legacy/evaluation.md); provenance and claim
  grounding therefore need explicit evaluation rather than proxy fluency scores.

## Open

- Which predecessor discovery methods should become Workbench adapters, and
  whether live discovery meets an explicit end-to-end budget.
- Whether relation-aware, provenance-preserving planning improves synthesis
  quality over a paper-list baseline.
- Which protocol can evaluate synthesis quality without overstating what
  automated metrics establish.

## Next

Specify and freeze E001: a controlled comparison of relation/provenance-backed
review planning against a paper-list baseline on one fixed supplied corpus.

## Detailed evidence — read only when relevant

- Cross-stage evaluation: [`archive/wiki-legacy/evaluation.md`](../archive/wiki-legacy/evaluation.md)
- Detailed legacy navigation: [`archive/wiki-legacy/INDEX.md`](../archive/wiki-legacy/INDEX.md)
