# Review contract TDD evidence

This report records the implementation tranche derived from the review-engine plan and the canonical `related-work-guides/RELATED_WORK_WRITING_GUIDE.md`.

## User journeys

- As a researcher, I want to choose Sufficient Related Work, Comprehensive Survey, or Systematic Review so the system applies the right coverage contract.
- As a researcher, I want a projected token/API envelope before searching so I can decide whether to spend more for confidence.
- As a researcher, I want a reproducible protocol with questions, criteria, sources, cutoff, and update policy.
- As a researcher, I want discovery routes recorded separately so I can inspect how the corpus was gathered.
- As a researcher, I want an explicit corpus checkpoint audit so I know whether screening and source acquisition are complete enough to proceed.
- As a researcher, I want the broader review audit to state which stopping checks passed, not just a single readiness label.
- As a researcher, I want to move selected papers between the workbench and Zotero without exposing credentials to the browser.

## Guarantees

| # | Guarantee | Test | Result |
|---|---|---|---|
| 1 | Review modes and resource envelopes reject invalid values and expose mode-specific estimates. | `backend/tests/test_review_modes.py` | PASS |
| 2 | Selected review mode persists on the brief and run. | `backend/tests/test_review_modes.py::test_project_and_run_persist_the_selected_review_mode` | PASS |
| 3 | Protocol fields persist, validate, and synchronize the brief mode. | `backend/tests/test_protocol.py` | PASS |
| 4 | Multi-route discovery records route provenance and one usage event per route. | `backend/tests/test_discovery.py::test_discovery_can_run_multiple_named_routes_with_separate_usage_events` | PASS |
| 5 | Corpus audit reports route execution, screening, source-text readiness, and limitations. | `backend/tests/test_discovery.py::test_coverage_audit_explains_corpus_checkpoint_readiness` | PASS |
| 6 | Frontend mode selection sends the selected contract and expands routes for broader modes. | `frontend/tests/workbench.test.tsx` | PASS |
| 7 | Frontend validates protocol and corpus-audit API responses. | `frontend/tests/api.test.ts` | PASS |
| 8 | Broader review audits emit a stopping certificate with route, screening, and source checks. | `backend/tests/test_discovery.py::test_broader_coverage_audit_emits_stopping_certificate` | PASS |
| 9 | Frontend parses stopping certificates and exposes credential-safe Zotero actions. | `frontend/tests/api.test.ts`, `frontend/tests/workbench.test.tsx` | PASS |
| 10 | PRISMA reports identify, screen, include, and exclude counts from recorded events. | `backend/tests/test_protocol.py::test_prisma_report_reconciles_protocol_search_and_screening_flow` | PASS |
| 11 | Citation expansion persists directional network edges and exposes them through the graph/client contracts. | `backend/tests/test_discovery.py::test_citation_expansion_persists_directional_edges_and_provenance`, `frontend/tests/api.test.ts` | PASS |
| 12 | Researchers can launch backward/forward citation expansion from each corpus paper. | `frontend/tests/workbench.test.tsx` | PASS |
| 13 | An on-demand living update reuses the saved mode/routes, records its timestamp, and reports new papers. | `backend/tests/test_discovery.py::test_on_demand_living_update_records_timestamp_and_new_papers` | PASS |
| 14 | Paid providers are blocked until a project records approver identity, justification, and non-replicability evidence. | `backend/tests/test_discovery.py::test_paid_provider_requires_explicit_non_replicable_approval`, `frontend/tests/api.test.ts` | PASS |
| 15 | Generated substantive review sentences retain exact evidence-span IDs alongside paper citations. | `backend/tests/test_pipeline.py::test_fixture_pipeline_preserves_complete_claim_provenance` | PASS |
| 16 | Researchers can edit generated prose while preserving its claim and evidence-span links. | `backend/tests/test_pipeline.py::test_grounded_review_sentence_can_be_edited_without_losing_evidence_links`, `frontend/tests/workbench.test.tsx` | PASS |
| 17 | Citation expansion supports bounded multi-hop traversal and reports a stopping reason. | `backend/tests/test_discovery.py::test_multi_hop_citation_expansion_stops_at_exhausted_frontier`, `frontend/tests/api.test.ts` | PASS |
| 18 | Co-citation expansion derives shared-reference neighbors locally and records derivation provenance. | `backend/tests/test_discovery.py::test_co_citation_expansion_derives_shared_reference_neighbors`, `frontend/tests/workbench.test.tsx` | PASS |
| 19 | Comprehensive/systematic discovery includes a distinct foundational/seminal route with auditable query provenance. | `backend/tests/test_discovery.py::test_seminal_route_records_foundational_query_provenance`, `frontend/tests/workbench.test.tsx` | PASS |
| 20 | Comprehensive/systematic discovery includes an explicit adjacent-fields route for cross-disciplinary coverage. | `backend/tests/test_discovery.py::test_cross_disciplinary_route_records_adjacent_fields_query`, `frontend/tests/workbench.test.tsx` | PASS |
| 21 | Zotero imports prefer a published record over a preprint while retaining the preprint as alternate provenance. | `backend/tests/test_zotero.py::test_zotero_prefers_published_record_but_retains_preprint_provenance` | PASS |
| 22 | Corpus audits expose candidate yield and unique-paper yield for every executed discovery route. | `backend/tests/test_discovery.py::test_coverage_audit_explains_corpus_checkpoint_readiness`, `frontend/tests/api.test.ts` | PASS |
| 23 | Discovery preserves provider citation-count and publication-date signals through the API and screening UI. | `backend/tests/test_discovery.py::test_discovery_persists_candidates_and_route_provenance`, frontend type/lint checks | PASS |
| 24 | PRISMA reporting reconciles identified records, deduplicated records, screening, retrieval, inclusion, and exclusion in the systematic-review UI. | `backend/tests/test_protocol.py::test_prisma_report_reconciles_protocol_search_and_screening_flow`, `frontend/tests/api.test.ts`, `frontend/tests/workbench.test.tsx` | PASS |
| 25 | Live source-text papers with grounded topical overlap receive a conservative cross-paper relation and comparative synthesis claim. | `backend/tests/test_sources.py::test_live_pipeline_builds_conservative_cross_paper_relation` | PASS |
| 26 | A project cannot create a second active pipeline while an earlier run is working or awaiting a human checkpoint. | `backend/tests/test_review_modes.py::test_pipeline_rejects_a_second_active_run_until_the_first_is_resolved` | PASS |
| 27 | Public HTTP(S) text sources can be fetched into the corpus with provenance while private targets and redirects are rejected. | `backend/tests/test_sources.py::test_fetches_public_source_url_with_provenance_and_blocks_private_targets`, frontend API/UI checks | PASS |
| 28 | Fetched HTML is reduced to visible UTF-8 text before evidence extraction, excluding head, script, style, and template content. | `backend/tests/test_sources.py::test_fetches_public_source_url_with_provenance_and_blocks_private_targets` | PASS |
| 29 | Fetched PDFs are bounded and converted to text with a versioned `pypdf` parser before evidence extraction. | `backend/tests/test_sources.py::test_extracts_text_from_bounded_pdf_bytes` | PASS |
| 30 | Coverage audits report whether each executed route has publication-date and citation-count signals for its candidate papers. | `backend/tests/test_discovery.py::test_coverage_audit_explains_corpus_checkpoint_readiness`, frontend API/UI contract checks | PASS |
| 31 | Recent, seminal, and survey routes apply deterministic publication-date, citation-count, and survey-term ordering before provenance ranks are recorded. | `backend/tests/test_discovery.py::test_seminal_route_orders_candidates_by_citation_signal` | PASS |
| 32 | URL acquisition deduplicates existing DOI/title identities and attaches repeat source fetches to the canonical corpus paper. | `backend/tests/test_sources.py::test_url_ingestion_deduplicates_existing_paper_identity` | PASS |
| 33 | Candidate screening records a transparent relevance rationale and derives a bounded fallback score from query overlap and available route signals. | `backend/tests/test_discovery.py::test_discovery_persists_candidates_and_route_provenance` | PASS |
| 34 | Discovery enforces the saved protocol cutoff date, retains only records at or before it, and reports how many provider candidates were filtered. | `backend/tests/test_protocol.py::test_discovery_enforces_protocol_cutoff_and_reports_filtered_candidates` | PASS |
| 35 | PRISMA search provenance preserves cutoff-filtered records, and the systematic-review UI exposes that count. | `backend/tests/test_protocol.py::test_discovery_enforces_protocol_cutoff_and_reports_filtered_candidates`, `frontend/tests/api.test.ts`, `frontend/tests/workbench.test.tsx` | PASS |
| 36 | Backward/forward citation expansion applies the saved protocol cutoff and reports filtered network candidates. | `backend/tests/test_discovery.py::test_citation_expansion_enforces_protocol_cutoff`, `frontend/tests/api.test.ts` | PASS |
| 37 | Cross-disciplinary discovery executes bounded adjacent-field, interdisciplinary-methods, and adjacent-application queries under one auditable route. | `backend/tests/test_discovery.py::test_cross_disciplinary_route_records_adjacent_fields_query` | PASS |
| 38 | The default live adapter fans out across free Semantic Scholar and OpenAlex sources and marks each candidate with its provider provenance. | `backend/tests/test_discovery.py::test_openalex_provider_maps_work_metadata_and_abstract`, `backend/tests/test_discovery.py::test_multi_source_provider_merges_and_marks_provider_provenance`, `backend/tests/test_discovery.py::test_app_wires_free_multi_source_discovery_by_default` | PASS |
| 39 | OpenAlex forward citation expansion maps citing works through the same provider adapter and provenance path. | `backend/tests/test_discovery.py::test_openalex_provider_expands_forward_citations` | PASS |

## Validation evidence

- RED checkpoints were created before each production implementation slice.
- Backend: `uv run pytest -q` → 82 passed.
- Backend coverage: `uv run pytest --cov=app --cov-report=term-missing` → 84.83%, above the 80% requirement.
- Backend lint: `uv run ruff check app tests` → PASS.
- Frontend: `npm test -- --run` → 46 passed.
- Frontend lint: `npm run lint` → PASS.
- Frontend types: `npx tsc --noEmit` → PASS.

## Known gaps

- Bounded backward and forward multi-hop expansion and local co-citation derivation are implemented with stopping reasons; richer network-saturation heuristics remain future work.
- Paid-provider approval is enforced at discovery boundaries; an approved provider adapter still must be configured before use. Zotero import/export is available through server-side credentials.
- Zotero DOI/title deduplication prefers published records and retains alternate preprint provenance; richer edition/version reconciliation remains future work.
- Discovery preserves provider citation-count and publication-date signals in provenance and exposes them during screening; they are importance/recency signals, not completeness guarantees.
- Protocol cutoff dates are enforced for discovery and expose filtered counts; records with only an unknown publication date are retained and should be reviewed as a protocol limitation rather than silently discarded.
- The default live adapter combines Semantic Scholar and OpenAlex for search and citation expansion; OpenAlex backward expansion is bounded by one metadata request per referenced work.
- Full-text acquisition now supports explicitly requested public HTTP(S) text/HTML/PDF URLs with SSRF, redirect, size, and parser guards; richer HTML extraction remains future work. Abstract-backed evidence cannot certify subtle comparisons.
- The narrative checkpoint exists for broader modes; generated prose is now editable with claim/evidence links preserved. Live cross-paper comparison now uses a conservative grounded overlap heuristic; richer paragraph-level generation and section-level editing remain future work.
- Living-review updates are currently on-demand and synchronous; scheduled refresh jobs remain future work.
