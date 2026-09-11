# Literature Synthesis Workbench

Local-first research instrument for turning a supplied paper corpus into
structured evidence, scientific relations, an explanatory review plan, and a
claim-level inspectable review.

The bundled five-paper regression fixture is deterministic and makes no network
or paid-model calls. The UI also supports live discovery through Semantic
Scholar when the provider is reachable. Discovered papers are candidates until
screened; including them and choosing “Build grounded review” creates
abstract-backed evidence with explicit provenance. This live path is a
conservative MVP: full-text acquisition and model-backed semantic extraction
are not yet enabled.

Use “Preview scope” to see the transparent focus areas and projected provider
call budget before discovery. The execution ledger also exposes a hard paper
cap for each grounded-review run; discovery usage is recorded separately from
the zero-cost local pipeline stages.

## Run locally

Backend (terminal 1):

```bash
cd backend
uv run --extra dev uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000
```

Frontend (terminal 2):

```bash
cd frontend
npm install
npm run dev -- --hostname 127.0.0.1
```

Open <http://127.0.0.1:3000>. The API is intentionally loopback-only. There is
no authentication in this local single-user slice; do not expose it on a LAN
or public interface.

## Verify

```bash
cd backend
uv run --extra dev pytest tests --cov=app --cov-report=term-missing
uv run --extra dev ruff check app tests

cd ../frontend
npm test
npm run test:coverage
npm run lint
npm run build
```

## Data and secrets

The SQLite database contains plaintext research briefs, source passages, and
generated artifacts. Keep `.data/` private and delete a project through the UI
or API when it is no longer needed. The application never copies shared legacy
`.env` contents. Slice 1 does not require provider credentials.

See [the implementation handoff](lit_review_pipeline_handoff.md) for the full
MVP design and deferred milestones.
