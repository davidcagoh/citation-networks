# Research Program Overview

This program studies citation networks in three connected stages, plus two newer ideas that grew out of doing the work.

## The pipeline

```
 ┌───────────────┐        ┌────────────────┐        ┌───────────────┐
 │  LitDiscover  │        │   Zeitgeist     │        │   Synthesis   │
 │               │        │                 │        │               │
 │  Recover a    │  ───▶  │  Resolve the    │  ───▶  │  Apply that   │
 │  field's full │        │  structure      │        │  structure to │
 │  paper set    │        │  inside a       │        │  a recovered  │
 │  from a few   │        │  citation graph │        │  set, and see │
 │  seed papers  │        │  (communities,  │        │  if it reads  │
 │               │        │  power laws,    │        │  as real      │
 │               │        │  time windows)  │        │  research     │
 │               │        │                 │        │  threads      │
 └───────────────┘        └────────────────┘        └───────────────┘
```

Each stage's output feeds the next. LitDiscover finds the papers; Zeitgeist's methods describe how they're structured; Synthesis is where those methods get pointed at a LitDiscover result to see if the whole thing actually works end to end.

Two further ideas — citation motifs and a different way of resolving communities — came out of working on stages 1 and 2, and aren't part of either paper yet.

```
 ┌────────────────────┐              ┌────────────────────────────┐
 │  Citation Motifs    │◄────────────►│  Hierarchical Dirichlet    │
 │  (how ideas spread) │  same signal │  Process (soft community    │
 │                     │              │  resolution)                │
 └────────────────────┘              └────────────────────────────┘
```

---

## 1. LitDiscover

Recovers the full paper set behind a research topic by following citations outward from one or a few seed papers, instead of relying on keyword search. Tested against real published surveys — recovers 85–98%+ of their bibliographies depending on how many seeds you start from.

**Where it stands:** Shipped and installable (`pip install litdiscover`). The paper has been through four venues — most recently desk-rejected by an IR journal, because the literature review behind it needs more recent, LLM-era baselines. The core method isn't in question; the survey work supporting it needs redoing.

**What could strengthen it:** the traversal now exports the full graph it explored — every paper it looked at, not just the ones it kept, plus which round each one was found in. That makes it possible to actually show the algorithm working: which papers it pulled in, which it rejected, and when — instead of just reporting a final recall number.

## 2. Zeitgeist

The original project with Xiaobai. The idea: a citation network's overall power-law shape isn't one process — it's a mixture of several, one per research community, each with its own citation rate and its own active time window.

**Where it stands:** First full draft written (10 pages, targeting COMPLEX NETWORKS 2026). On a 700K-paper physics dataset: 446 communities found, 25 sampled communities each individually fit a power law, with meaningfully different exponents across communities, and most stayed active for under 20 years. This is a real, working result currently under review.

**What could strengthen it:** the result relies on every paper being assigned to exactly one community. In practice, papers often belong to more than one thread at a time, and the current method requires choosing in advance how finely to split communities. A different approach — a Hierarchical Dirichlet Process — would let papers belong to multiple threads at once and let the number of threads emerge from the data, rather than being fixed upfront. This is also the more general problem behind why a lot of literature-review tooling struggles to say cleanly what "a field" even is.

## 3. Synthesis

The connecting piece: take a paper set LitDiscover recovered, run Zeitgeist's methods on it, and check whether the resulting groups look like real research threads to someone who knows the area.

**Where it stands:** Fully specified (test case: 56 papers on random geometric complexes, 100% recovered), but not yet built. Deliberately on hold until Zeitgeist's paper is submitted, so the two results don't validate each other.

This is where the LitDiscover and Zeitgeist improvements above actually meet — the new traversal export is already in the format Synthesis needs, and a smaller, single-topic paper set is exactly where soft community membership should matter most, since that's where a paper genuinely bridging two threads is most likely to show up.

---

## Two further ideas

**Citation motifs.** A handful of structural patterns in a citation graph that might indicate *how* an idea entered a field: one paper starting a whole line of work, several people arriving at the same idea independently without citing each other, an idea imported from outside the field, and two fields that grow together by citing each other — a method and the benchmark built to test it, for example.

**Soft community resolution (Hierarchical Dirichlet Process).** The same idea driving the Zeitgeist strengthener above, generalized: model community membership as a mixture rather than a single label. This is what would actually make the fourth motif — two fields growing together — visible in the first place, since a hard partition either merges such a pair into one cluster or splits it without marking anything unusual about the split.

Both are logged as future directions, not active work — the plan is to return to them once the three main pieces above are submitted.
