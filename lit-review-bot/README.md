# lit-review-bot/

Shell folder grouping the LitDiscover engine, the paper validating it, and the reference corpus
used to survey the field — three related but independently-versioned things kept together here
for convenience, not merged into one repo.

| Folder | What it is | Repo |
|---|---|---|
| [`litdiscover/`](litdiscover/) | The active LitDiscover engine — queue-driven citation-graph traversal, LLM screening, extraction, synthesis. `pip install litdiscover`. | own repo: `github.com/davidcagoh/litdiscover` (private) |
| [`paper/`](paper/) | *Robust Literature Discovery from Minimal Seeds* — the empirical paper validating LitDiscover on the APS citation corpus (analysis, figures, reproducibility materials). | own repo: `github.com/davidcagoh/robust-literature-discovery` (public) |
| [`reference-systems/`](reference-systems/) | 14 cloned reference literature-review-automation systems (SurveyX, InteractiveSurvey, LitLLM, etc.), plus `deep-dives.md` — a code-grounded survey of how each one actually works, and the source PDFs behind it. Not a repo of its own; individual clones are gitignored external code. | n/a — reference clones, not tracked here |

`litdiscover/` and `paper/` are gitignored in `citation-networks` (see the root `README.md`
Setup section for clone instructions) — each has its own git history, CI, and (for `litdiscover`)
PyPI publish cycle, so they stay independent rather than submodules.

`deprecated-bot/` (sibling directory, one level up) holds an older, no-longer-active `litreview`
variant — kept for reference, not active use.

## Wiki

Research framing, decisions, and open questions for this work live in `wiki/litdiscover/`, not
here — see [`wiki/INDEX.md`](../wiki/INDEX.md#litdiscover) for the current entry points
(`research-roadmap.md`, `discovery-roadmap.md`, `decisions.md`, `open-questions.md`).
