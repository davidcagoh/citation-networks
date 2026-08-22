# citation-networks

PhD research workspace with two active programs: Literature Workbench, the
functional system for literature discovery and synthesis, and Zeitgeist, an
independent analytical study of temporal and community structure in citation
networks. Current scientific state lives in [`wiki/_index.md`](wiki/_index.md);
this file is repo navigation only.

## Programs

- **Literature Workbench** unifies the former LitDiscover and Synthesis
  programs: brief/seeds → discovery → evidence and relations → review plan →
  grounded draft and verification. Its supplied-corpus vertical slice works;
  live discovery remains a deferred milestone.
- **Zeitgeist** is analytical rather than a required pipeline stage. Its
  citation-network results may inform Workbench methods when experimentally
  useful.

## Structure

```
citation-networks/
├── literature-workbench/          # Active local-first discovery + synthesis system
├── wiki/                          # Minimal program/project state + formal experiments
│   └── projects/                      # One small current-state page per active research workstream
├── archive/wiki-legacy/           # Frozen prior wiki, reference systems, and standalone utilities
├── zeitgeist/                     # Zeitgeist: temporal embedding, phase characterization (own repo: github.com/davidcagoh/zeitgeist)
├── lit-review-bot/
│   ├── litdiscover/                   # LitDiscover engine (own repo: github.com/davidcagoh/litdiscover), pip installable
│   ├── projects/                      # Research-run project folders (Zotero-backed manual pipeline surveys + LitDiscover-engine-driven runs); projects/_archive/ holds retired ones
│   └── evals/                         # Eval infra: aps-eval/, live-survey-eval/, synergy-eval/ (own repo: github.com/davidcagoh/robust-literature-discovery); manuscript paused, archived under evals/_archive/drafts/
└── deprecated-bot/                # Older, inactive literature-review variant (own repo: automated-lit-reviews — deleted from GitHub)
```

`literature-workbench/` is intentionally isolated from the legacy engines. It
may load shared credentials by explicit environment-file path in later slices,
but does not import or mutate their databases or application code.

## Status (see wiki for full detail)

| Program | Status | Target |
|---|---|---|
| [Literature Workbench](wiki/projects/literature-workbench.md) | Supplied-corpus provenance slice complete; live discovery and scientific evaluation pending | Unified research instrument |
| [Zeitgeist](wiki/projects/zeitgeist.md) | First full draft written; figures complete | COMPLEX NETWORKS 2026 |

LitDiscover and Synthesis are predecessor programs. Their code, evaluations,
and research records remain available as inputs to the Workbench rather than
active top-level workstreams.

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

Start at [`wiki/_index.md`](wiki/_index.md) for current scientific state and one next action.
[`archive/wiki-legacy/`](archive/wiki-legacy/) holds the frozen detailed record when deeper
context is needed.
