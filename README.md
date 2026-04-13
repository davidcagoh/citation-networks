# citation-networks

Research workspace for "Recognizing Signature Patterns and Phases of Time-Varying Networks"  
Supervisor: Xiaobai Sun | Started: Sept 2024

## Structure

```
citation-networks/
├── wiki/                         # Shared project wiki (session logs, decisions, open questions)
├── citation-dynamics/            # Thesis: temporal embedding, phase characterization, Zeitgeist hypothesis
└── lit-review/
    └── robust-literature-discovery/  # Paper: LLM-based literature discovery (own git repo)
```

## Core Hypothesis (Zeitgeist)

The global APS citation distribution is a mixture of subcommunity distributions, each individually scale-free, corresponding to distinct research generations. BlueRed + SG-t-SNE is the proposed detection method.

## Three Contributions (thesis)

1. Temporal embedding of citation networks
2. Backward influence mapping
3. Quantitative phase characterization

## Pipeline (lit-review → citation-dynamics synthesis)

```
citation-dynamics/          →   robust-literature-discovery/   →   [synthesis — planned]
Understand why the graph        Exploit structure to recover        Apply citation-dynamics
has the structure it does       a topic's literature from           methods to the discovered
(phases, Zeitgeist, embedding)  minimal seeds (89–99% recall)       set → structured lit review
```

## Wiki

See [`wiki/INDEX.md`](wiki/INDEX.md) for session logs, decisions, and open questions.
