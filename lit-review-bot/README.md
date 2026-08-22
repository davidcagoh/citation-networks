# lit-review-bot/

Shell folder grouping the LitDiscover engine, the eval infrastructure that validates it, and the
research-run project folders that use it (or the manual pipeline that's currently being explored
as a candidate replacement) — related but independently-versioned things kept together here for
convenience, not merged into one repo.

**`paper/` renamed `evals/` 2026-07-31** — the manuscript it was originally built to support is
paused (archived to `evals/_archive/drafts/`), and the folder now holds eval infrastructure more
broadly (`aps-eval/`, `live-survey-eval/`, and a new `synergy-eval/`), not just the one paper's
reproducibility materials.

**`reference-systems/` is archived at
`archive/wiki-legacy/reference-systems/`.** The active wiki now contains only
current scientific state, selective literature, and formal experiments. See
[`../archive/wiki-legacy/reference-systems/`](../archive/wiki-legacy/reference-systems/).

| Folder | What it is | Repo |
|---|---|---|
| [`litdiscover/`](litdiscover/) | The active LitDiscover engine — queue-driven citation-graph traversal, LLM screening, extraction, synthesis. `pip install litdiscover`. | own repo: `github.com/davidcagoh/litdiscover` (private) |
| [`evals/`](evals/) | Eval infrastructure: `aps-eval/` (closed-corpus APS benchmark, formerly `closed-corpus-eval/`), `live-survey-eval/` (3 live surveys), `synergy-eval/` (new 2026-07-31, scaffold only — external SYNERGY-dataset benchmark). The *Robust Literature Discovery from Minimal Seeds* manuscript this repo was built to support is paused, archived at `evals/_archive/drafts/`. | own repo: `github.com/davidcagoh/robust-literature-discovery` (public) |
| [`projects/`](projects/) | Research-run project folders — both LitDiscover-engine-driven runs and the newer Zotero-backed manual pipeline surveys (`china-ashare-strategy-survey/`, `trading-eval-survey/`). `projects/_archive/` holds retired ones; the curated prior-art record lives in `archive/wiki-legacy/reference-systems/deep-dives.md`. | n/a — research artifacts, not tracked here |

`litdiscover/` and `evals/` are gitignored in `citation-networks` (see the root `README.md`
Setup section for clone instructions) — each has its own git history, CI, and (for `litdiscover`)
PyPI publish cycle, so they stay independent rather than submodules.

`deprecated-bot/` (sibling directory, one level up) holds an older, no-longer-active `litreview`
variant — kept for reference, not active use.

## Wiki

Current scientific state lives in [`../wiki/_index.md`](../wiki/_index.md).
The former LitDiscover research record is frozen at
[`../archive/wiki-legacy/litdiscover/litdiscover.md`](../archive/wiki-legacy/litdiscover/litdiscover.md).
