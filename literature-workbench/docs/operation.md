# Literature Workbench operation

## Supported local workflows

1. Enter a project title and research brief.
2. Use **Preview scope** to see the deterministic focus areas and projected
   provider call budget.
3. Either run the five-paper fixture, or choose **Discover papers** to query
   Semantic Scholar.
   If the saved protocol has a cutoff date, discovery retains records at or
   before that date and reports the number filtered from the provider result.
   The cross-disciplinary route makes three bounded searches covering adjacent
   fields, interdisciplinary methods, and applications in adjacent fields.
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

The current live extractor is intentionally heuristic: it selects a bounded
first sentence and records whether it came from an abstract or imported text.
Live cross-paper relations use a conservative grounded topical-overlap rule;
they are explicitly marked as model inference and should not be treated as
semantic model extraction. The fixture relation path remains deterministic and
evidence linked.

## Operational boundaries

The backend is an unauthenticated loopback service. Keep it bound to
`127.0.0.1`; the SQLite database contains research text and generated output.
Provider credentials are read only from environment variables. Provider
failures return a safe 502 response, while malformed or missing source text is
represented as degraded corpus coverage.

Run budgets persist on each pipeline run. The paper cap is enforced before a
run is created; provider calls and local pipeline usage appear separately in
the cost ledger. Runs persist stage artifacts and can be resumed after a
failure. The JSON export includes source documents, evidence spans, relations,
claims, review text, and discovery events.

## Deferred extensions

Model-backed structured extraction, richer relation judging, and broader
automated contradiction/causal-language checks are the next
research/engineering extensions. They should preserve the same
source URI, parser/version, evidence-span, and budget contracts.
