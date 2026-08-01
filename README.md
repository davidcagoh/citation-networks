# citation-networks

PhD research workspace: three connected projects studying citation networks — LitDiscover
(literature discovery), Zeitgeist (temporal/community structure), Synthesis (applying the two
together). See [`wiki/research-program.md`](wiki/research-program.md) for the full narrative
overview; this file is repo navigation only.

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
│   ├── reference-systems/             # 14 cloned reference literature-review-automation systems + deep-dives.md (moved into wiki/ 2026-08-01 — research material, belongs with the wiki)
│   └── utils/                         # forward_cites.py, verify_refs.py (moved into wiki/ 2026-08-01)
├── zeitgeist/                     # Zeitgeist: temporal embedding, phase characterization (own repo: github.com/davidcagoh/zeitgeist)
├── lit-review-bot/
│   ├── litdiscover/                   # LitDiscover engine (own repo: github.com/davidcagoh/litdiscover), pip installable
│   ├── projects/                      # Research-run project folders (Zotero-backed manual pipeline surveys + LitDiscover-engine-driven runs); projects/_archive/ holds retired ones
│   └── evals/                         # Eval infra: aps-eval/, live-survey-eval/, synergy-eval/ (own repo: github.com/davidcagoh/robust-literature-discovery); manuscript paused, archived under evals/_archive/drafts/
└── deprecated-bot/                # Older, inactive literature-review variant (own repo: automated-lit-reviews — deleted from GitHub)
```

## Status (see wiki for full detail)

| Project | Status | Target |
|---|---|---|
| [LitDiscover](wiki/litdiscover/) | Desk-rejected by IP&M — redo in progress. Discovery/screening eval redesigned around an end-to-end recall/precision metric | Information Processing & Management (redo) |
| [Zeitgeist](wiki/zeitgeist/) | Active — first full draft written, figures done | COMPLEX NETWORKS 2026 |
| [Synthesis](wiki/synthesis/) | Three parallel tracks (graph-native, embedding-native, text-native control) | Post-Zeitgeist thesis chapter |

## Setup

`zeitgeist/`, `lit-review-bot/litdiscover/`, and `lit-review-bot/evals/` are each their own git
repo (gitignored here, not submodules — see rationale below). After cloning `citation-networks`,
clone them separately:

```bash
git clone https://github.com/davidcagoh/zeitgeist.git
git clone https://github.com/davidcagoh/litdiscover.git lit-review-bot/litdiscover
git clone https://github.com/davidcagoh/robust-literature-discovery.git lit-review-bot/evals
```

Kept as independent repos (rather than submodules) because `litdiscover` and `zeitgeist` are both
actively developed in place — including a standalone PyPI publish cycle for `litdiscover` — and a
submodule's pinned-commit pointer would drift constantly against that.

## Wiki

Start at [`wiki/INDEX.md`](wiki/INDEX.md) — session logs, decisions, and open questions per project.
