# citation-networks

Research workspace for "Recognizing Signature Patterns and Phases of Time-Varying Networks"
Supervisor: Xiaobai Sun | Started: Sept 2024

Three thesis contributions, each its own project:
1. Temporal embedding of citation networks
2. Backward influence mapping
3. Quantitative phase characterization

See [`wiki/research-program.md`](wiki/research-program.md) for the full narrative overview — the guide below is quick orientation only.

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

Each stage's output feeds the next. LitDiscover finds the papers; Zeitgeist's methods describe how they're structured; Synthesis points those methods at a LitDiscover result to see if the whole thing works end to end.

## Structure

```
citation-networks/
├── wiki/                          # Shared project wiki (session logs, decisions, open questions)
├── zeitgeist/                     # Zeitgeist: temporal embedding, phase characterization (own repo: github.com/davidcagoh/zeitgeist)
├── lit-review-bot/
│   ├── litdiscover/                   # LitDiscover engine (own repo: github.com/davidcagoh/litdiscover), pip installable
│   ├── paper/                         # RLD paper (own repo: github.com/davidcagoh/robust-literature-discovery)
│   └── reference-systems/             # 14 cloned reference literature-review-automation systems + deep-dives.md
└── deprecated-bot/                # Older, inactive literature-review variant (own repo: automated-lit-reviews — deleted from GitHub)
```

## Status (see wiki for full detail)

| Project | Status | Target |
|---|---|---|
| [LitDiscover](wiki/litdiscover/) | Desk-rejected by IP&M — redo in progress. Discovery/screening eval redesigned around an end-to-end recall/precision metric | Information Processing & Management (redo) |
| [Zeitgeist](wiki/zeitgeist/) | Active — first full draft written, figures done | COMPLEX NETWORKS 2026 |
| [Synthesis](wiki/synthesis/) | Three parallel tracks (graph-native, embedding-native, text-native control) | Post-Zeitgeist thesis chapter |

## Setup

`zeitgeist/`, `lit-review-bot/litdiscover/`, and `lit-review-bot/paper/` are each their own git
repo (gitignored here, not submodules — see rationale below). After cloning `citation-networks`,
clone them separately:

```bash
git clone https://github.com/davidcagoh/zeitgeist.git
git clone https://github.com/davidcagoh/litdiscover.git lit-review-bot/litdiscover
git clone https://github.com/davidcagoh/robust-literature-discovery.git lit-review-bot/paper
```

Kept as independent repos (rather than submodules) because `litdiscover` and `zeitgeist` are both
actively developed in place — including a standalone PyPI publish cycle for `litdiscover` — and a
submodule's pinned-commit pointer would drift constantly against that.

## Wiki

Start at [`wiki/INDEX.md`](wiki/INDEX.md) — session logs, decisions, and open questions per project.
