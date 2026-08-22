# Slice 1 Specification

Build a local-first Literature Synthesis Workbench vertical slice from the
repository handoff. A researcher can create a project, ingest a deterministic
five-paper fixture corpus, run grounded extraction/relations/planning/writing,
read the resulting review, and inspect the exact evidence behind each claim.

## Required behavior

- Persist projects, briefs, papers, source documents, evidence spans,
  scientific entities and relations, review plans, synthesis claims, review
  sentences, runs, stage runs, and usage/cost events in SQLite.
- Communicate between stages only through validated persisted objects.
- Reject entities or relations whose endpoints/evidence spans are invalid.
- Preserve exact character offsets and verbatim source text for evidence.
- Create synthesis claims before rendering prose and preserve sentence-to-claim
  mappings.
- Provide FastAPI endpoints for project creation, fixture ingestion, pipeline
  execution, project corpus/review retrieval, and claim evidence inspection.
- Provide a compact React/Next.js UI covering Brief, Corpus, Structure, Review,
  and Run/Costs, with a claim-click evidence inspector.
- Record stage status and usage for deterministic fixture calls.
- Mark malformed or absent source text as degraded without aborting the run.

## Acceptance fixture

The bundled five-paper corpus must generate a short, relation-oriented review.
At least 90% of substantive generated sentences must resolve through:

`sentence -> claim -> entity/relation -> evidence span -> source document -> paper`

No network or paid model is required for the acceptance path.

## Deferred

Live discovery, uploaded PDFs, verification repair, asynchronous workers,
budgets, exports, authentication, vector search, and production PostgreSQL.
