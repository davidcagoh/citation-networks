# Literature Workbench operation

## Supported local workflows

1. Enter a project title and research brief.
2. Use **Preview scope** to see the deterministic focus areas and projected
   provider call budget. The preview separates discovery fan-out calls from
   pipeline-budget calls and shows their total.
   The resource envelope is a planning and safety cap: paper count, external
   calls, estimated input/output tokens, and estimated USD spend. The current
   built-in workflow is local plus free-provider, so its estimated and recorded
   USD spend is $0.00; paid providers must be explicitly approved and their
   adapter configured before they can contribute calls.
3. Either run the five-paper fixture, or choose **Discover papers** to query
   the default free multi-source adapter (Semantic Scholar and OpenAlex).
   If the saved protocol has a cutoff date, discovery retains records at or
   before that date and reports the number filtered from the provider result.
   The cross-disciplinary route makes three bounded searches covering adjacent
   fields, interdisciplinary methods, and applications in adjacent fields.
   The survey route makes separate bounded searches for general reviews,
   systematic reviews/meta-analyses, and umbrella/tutorial reviews. Survey
   hits are ranked by explicit review/survey/benchmark signals before
   citation and date tie-breakers; ordinary routes use provider score and
   deterministic metadata tie-breakers.
   The Corpus audit preserves and displays the exact query strings used by
   each route, so a review can be reproduced or challenged at the query level.
   Citation-network audits also record expansion attempts that returned no
   candidates, making an empty frontier visible as evidence of saturation
   rather than indistinguishable from an expansion that was never run.
   Broad-mode stopping certificates additionally require complete date signals
   on the recent route, citation signals on the seminal route, and at least one
   review-, survey-, or benchmark-like work from the survey route. When multiple
   providers are configured, every required route must also complete on every
   provider; the audit remains incomplete if one provider partially fails.
4. Screen live candidates in **Corpus**. Candidates are not sent to the
   pipeline until they are included or pinned.
5. Choose **Build grounded review** in **Run / Costs**. This runs idempotent
   acquisition, provenance-preserving extraction, relation construction,
   planning, writing, and verification.
6. Edit the generated structure. Saving a plan validates all artifact
   references and rewrites the review sections.
7. Select a review sentence to inspect the exact source passage and offsets.
8. Export Markdown, JSON, or BibTeX from the API.

For a live source, use **Fetch public source URL** in Brief with an HTTP(S)
URL serving UTF-8 text, HTML, or a text-extractable PDF. The server records the
requested/final URL, content type, and parser version; private hosts, redirects,
unsupported content, extraction failures, and sources over 5 MB are rejected.

## Source coverage

- Fixture papers provide deterministic full source text and expected evidence.
- Live discovery persists the provider-supplied abstract as an `abstract`
  `SourceDocument`.
- Build-time acquisition also attempts discovered direct `.pdf`, `.html`, and
  `.txt` links through the same safe fetcher. It records attempted, fetched,
  and failed counts; failed acquisition keeps the abstract fallback and marks
  the resulting source coverage as limited.
- Local full text can be attached with
  `POST /projects/{id}/sources/text`, including a user-owned URI and paper
  metadata. It is stored as a `text` `SourceDocument` and enters the same
  pipeline.
- Public text/HTML can be attached with `POST /projects/{id}/sources/url`.
  It is stored as a `fetched_text` or `html` `SourceDocument` after URL safety
  validation; HTML is normalized to visible body text and PDFs are parsed with
  the versioned `pypdf` extractor before evidence extraction. DOI/title matches
  attach to the existing canonical paper rather than creating duplicates.
- Missing text degrades the paper and does not fabricate evidence.

For PRISMA reporting, an abstract alone does not count as a retrieved report:
`reports_not_retrieved` requires a usable text, HTML, or parsed-PDF document.
The same rule gates the systematic-review corpus checkpoint; comprehensive
survey mode reports the source-depth limitation without imposing the
systematic retrieval gate.

The current live extractor is intentionally heuristic: it selects a bounded
first sentence and records whether it came from an abstract or imported text.
Live cross-paper relations use a conservative grounded topical-overlap rule;
they are explicitly marked as model inference and should not be treated as
semantic model extraction. Auto-acquired paper-body evidence is labeled
`fulltext-heuristic-v1` in the `full_text` section so the evidence inspector
distinguishes it from abstract evidence. The fixture relation path remains
deterministic and evidence linked.

An optional `SynthesisProvider` can replace claim wording during the writing
stage, after the structure checkpoint. It
receives the deterministic draft and exact evidence text, while the pipeline
continues to assign evidence-span IDs and verification state. No external
model provider is enabled by default. When explicitly enabled with
`WORKBENCH_ENABLE_OPENAI_SYNTHESIS=1`, the bundled OpenAI Responses adapter
uses `OPENAI_SYNTHESIS_MODEL` (default `gpt-5.6-luna`), sends `store: false`,
and never exposes the credential to the browser. It can read the existing
`WORKBENCH_SHARED_ENV_FILE` for the OpenAI settings, while process environment
variables take precedence. The adapter sends exact extracted evidence as
quoted data, and the pipeline remains responsible for evidence-span links and
verification.

## Operational boundaries

The backend is an unauthenticated loopback service. Keep it bound to
`127.0.0.1`; the SQLite database contains research text and generated output.
Provider credentials are read only from environment variables. Provider
failures return a safe 502 response, while malformed or missing source text is
represented as degraded corpus coverage.

The default multi-source discovery adapter fans out to Semantic Scholar and
OpenAlex, records each result's source provider, and continues with available
results when one source fails. Both providers support citation expansion;
OpenAlex backward expansion is bounded by one metadata request per referenced
work.

Run budgets persist on each pipeline run. The paper cap is enforced before a
run is created; provider calls and local pipeline usage appear separately in
the cost ledger. Runs persist stage artifacts and can be resumed after a
failure. The JSON export includes source documents, evidence spans, relations,
claims, review text, and discovery events.

Discovery also enforces the request's external-call cap before fan-out begins
(100 calls by default for the API request). A multi-source request consumes one
call per configured provider per route query, matching scope-preview estimates;
an over-budget request returns HTTP 429 without contacting a provider.
The discovery response also returns `external_api_calls`, the actual planned
fan-out count for that request, for immediate reconciliation in clients.

Scope-preview dollar estimates use the default Luna planning/writing rate
assumption (currently $0.20 per million input tokens and $1.20 per million
output tokens); they are projections, not a billing guarantee. Actual provider
usage is recorded after each completed stage, and the cost screen identifies
the provider and model used. If synthesis is disabled, the deterministic path
incurs no model-token spend.

## Deferred extensions

Richer multi-object extraction, relation judging, and broader
automated contradiction/causal-language checks are the next
research/engineering extensions. They should preserve the same
source URI, parser/version, evidence-span, and budget contracts.
