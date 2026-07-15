# utils/

Standalone scratch scripts for working with `.bib` files against the Semantic Scholar Graph
API, independent of any single project's database. Each is self-contained (own S2 client,
own rate limiting) so it can be pointed at any `.bib` file, anywhere.

Both integrated equivalents also exist inside the LitDiscover engine itself
(`lit-review-bot/litdiscover/litdiscover/discovery/forward_cites.py` and `verify.py`, exposed as
the `forward-cites` and `verify` CLI commands) — those operate on a project's own
`papers`/`edges` database tables and reuse LitDiscover's shared S2 client/rate-limit code. Use
the scripts here instead when you just have a loose `.bib` file and no project database, e.g.
sanity-checking a paper's `refs.bib` before submission.

## Setup

```bash
pip install bibtexparser httpx python-dotenv
```

Both scripts read `SEMANTIC_SCHOLAR_API_KEY` from a `.env` file in `utils/` (or the environment).
Without a key, S2's unauthenticated rate limit applies and requests slow down accordingly.

## Scripts

### `verify_refs.py` — is every entry a real, correctly-cited paper?

Resolves each bib entry against S2 (DOI → ArXiv → title search, in that order of preference) and
fuzzy-matches the returned title against the bib title to catch drift, not just missing entries.

```bash
python verify_refs.py references.bib
```

Classifies every entry as `VERIFIED` / `LIKELY` / `UNCERTAIN` / `NOT_FOUND` (in decreasing
confidence) and writes `verification_report.md` next to the bib file. Anything `UNCERTAIN` or
`NOT_FOUND` is also printed to stdout for manual follow-up.

### `forward_cites.py` — who cites each entry?

Resolves each bib entry the same way, then paginates S2's `/paper/{id}/citations` endpoint to
pull every paper that cites it.

```bash
python forward_cites.py references.bib
python forward_cites.py references.bib --min-year 2020 --limit 50
```

Writes `forward_cites_report.md` (top-N citing papers per entry, sorted by citation count) and
`forward_cites_edges.csv` (a flat `source_s2_id, citing_s2_id, ...` edge list, ready to feed into
graph tooling).

## Typical order of use

1. `verify_refs.py` first — confirm the bib file's own entries are correct.
2. `forward_cites.py` second — expand outward one citation hop from a verified bib file.
