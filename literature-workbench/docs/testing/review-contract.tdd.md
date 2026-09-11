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
| 40 | OpenAlex backward citation expansion follows bounded referenced-work metadata links and maps the resulting records. | `backend/tests/test_discovery.py::test_openalex_provider_expands_backward_references` | PASS |
| 41 | Multi-source discovery records provider attempts and exposes partial fan-out failures in the coverage audit and Corpus UI. | `backend/tests/test_discovery.py::test_coverage_audit_reports_partial_multi_source_fanout`, frontend API/UI contract checks | PASS |
| 42 | End-to-end multi-source discovery preserves each originating provider in canonical paper metadata and candidate events. | `backend/tests/test_discovery.py::test_multi_source_project_records_originating_provider_names` | PASS |
| 43 | Comprehensive/systematic stopping certificates require complete publication-date coverage for recent routes and citation-count coverage for seminal routes. | `backend/tests/test_discovery.py::test_broader_coverage_audit_emits_stopping_certificate`, `backend/tests/test_discovery.py::test_broader_audit_rejects_missing_latest_and_seminal_signals` | PASS |
| 44 | Scope preview separates discovery fan-out calls, pipeline-budget calls, and their total, reflecting mode and provider count. | `backend/tests/test_scope.py::test_scope_preview_returns_transparent_scope_and_budget`, frontend scope-preview UI/type checks | PASS |
| 45 | Comprehensive/systematic stopping certificates require the survey route to return at least one review-, survey-, or benchmark-like work. | `backend/tests/test_discovery.py::test_broader_coverage_audit_emits_stopping_certificate`, `backend/tests/test_discovery.py::test_broader_audit_rejects_missing_latest_and_seminal_signals` | PASS |
| 46 | Comprehensive/systematic stopping certificates require every configured discovery provider to complete every required route; partial fan-out remains incomplete. | `backend/tests/test_discovery.py::test_comprehensive_audit_requires_all_providers_on_required_routes` | PASS |
| 47 | Coverage audits report marginal new-paper yield and route overlap so later discovery routes can be inspected for diminishing returns. | `backend/tests/test_discovery.py::test_coverage_audit_explains_corpus_checkpoint_readiness`, frontend parser/UI checks | PASS |
| 48 | Multi-source usage accounting records one external call per provider attempt, matching the scope-preview fan-out estimate and budget enforcement. | `backend/tests/test_discovery.py::test_multi_source_search_usage_counts_each_provider_attempt` | PASS |
| 49 | Coverage audits expose directional citation/co-citation expansion counts, graph edges, and network-discovered papers for inspectable saturation diagnostics. | `backend/tests/test_discovery.py::test_citation_expansion_persists_directional_edges_and_provenance`, frontend parser/UI checks | PASS |
| 50 | Discovery requests enforce their external-call budget before any provider request is made, returning a clear 429 when the planned fan-out would exceed the cap. | `backend/tests/test_discovery.py::test_discovery_enforces_the_requested_external_call_budget` | PASS |
| 51 | Acquisition attempts eligible discovered direct full-text links through the injected safe fetcher, records fetched/failed counts, and preserves abstract fallback. | `backend/tests/test_sources.py::test_acquisition_fetches_eligible_discovered_full_text_links` | PASS |
| 52 | Discovery responses report actual external fan-out calls so callers can reconcile provider usage with the preview and cap. | `backend/tests/test_discovery.py::test_multi_source_search_usage_counts_each_provider_attempt`, `frontend/tests/api.test.ts` | PASS |
| 53 | Compatibility aliases normalize to canonical review contracts at project, protocol, and pipeline boundaries, preserving comprehensive checkpoints for `thorough`. | `backend/tests/test_review_modes.py::test_compatibility_mode_aliases_normalize_to_canonical_contracts` | PASS |
| 54 | Auto-acquired full-text documents use a distinct full-text extractor/section identity in evidence provenance rather than being mislabeled as abstract evidence. | `backend/tests/test_sources.py::test_acquisition_fetches_eligible_discovered_full_text_links` | PASS |
| 55 | The Corpus workflow displays the discovery request's external API-call count alongside candidate and cutoff counts. | `frontend/tests/api.test.ts`, `frontend/tests/workbench.test.tsx` | PASS |
| 56 | Fetched plain-text source documents outrank abstracts during document selection and receive full-text evidence provenance in the pipeline. | `backend/tests/test_sources.py::test_fetches_public_source_url_with_provenance_and_blocks_private_targets` | PASS |
| 57 | PRISMA `screened` counts only corpus records with an explicit screening decision and excludes unresolved candidates. | `backend/tests/test_protocol.py::test_prisma_screened_count_excludes_unresolved_candidates` | PASS |
| 58 | A published Zotero record promotes a previously discovered preprint while retaining the preprint identity in alternate provenance. | `backend/tests/test_zotero.py::test_zotero_published_record_promotes_discovered_preprint` | PASS |
| 59 | Corpus audits distinguish selected records with full text from selected records supported only by abstracts, and the UI exposes both counts. | `backend/tests/test_discovery.py::test_coverage_audit_explains_corpus_checkpoint_readiness`, frontend parser/UI checks | PASS |
| 60 | PRISMA `reports_not_retrieved` counts selected records without full-text source documents; abstract-only records are not treated as retrieved reports. | `backend/tests/test_protocol.py::test_prisma_report_reconciles_protocol_search_and_screening_flow` | PASS |
| 61 | Systematic-review stopping certificates require selected reports to be retrieved as full text; comprehensive surveys retain a separate abstract-only diagnostic. | `backend/tests/test_discovery.py::test_systematic_audit_requires_retrieved_reports` | PASS |
| 62 | Survey hits rank ahead of non-survey results by review-signal strength, then citation/date signals; general routes use deterministic provider-score tie-breaking. | `backend/tests/test_discovery.py::test_survey_route_orders_review_hits_by_strength_and_citations`, `backend/tests/test_discovery.py::test_seminal_route_orders_candidates_by_citation_signal` | PASS |
| 63 | Cross-provider records with normalized DOI or title identities collapse into one canonical corpus paper while retaining separate discovery evidence. | `backend/tests/test_discovery.py::test_discovery_deduplicates_normalized_cross_provider_identity` | PASS |
| 64 | Unicode-safe title identity normalization keeps distinct non-Latin paper titles separate during cross-provider discovery. | `backend/tests/test_discovery.py::test_discovery_does_not_collapse_distinct_non_latin_titles` | PASS |
| 65 | Comprehensive scope accounting includes the general, systematic/meta-analytic, and umbrella/tutorial survey query families in discovery-call estimates. | `backend/tests/test_discovery.py::test_survey_route_queries_cover_multiple_review_families`, `backend/tests/test_scope.py::test_scope_preview_returns_transparent_scope_and_budget` | PASS |
| 66 | Coverage audits preserve exact executed query strings per route, and the Corpus UI exposes them while accepting older payloads without query metadata. | `backend/tests/test_discovery.py::test_coverage_audit_explains_corpus_checkpoint_readiness`, `frontend/tests/api.test.ts`, `frontend/tests/workbench.test.tsx` | PASS |
| 67 | Citation-network audits record every expansion attempt and count empty expansions, including co-citation requests with no available graph frontier. | `backend/tests/test_discovery.py::test_coverage_audit_records_empty_network_expansions`, `backend/tests/test_discovery.py::test_citation_expansion_persists_directional_edges_and_provenance` | PASS |
| 68 | Corpus network diagnostics distinguish attempted expansions from empty expansions and expose those saturation signals in the UI, with backward-compatible parsing. | `backend/tests/test_discovery.py::test_coverage_audit_records_empty_network_expansions`, `frontend/tests/api.test.ts`, `frontend/tests/workbench.test.tsx` | PASS |
| 69 | An optional synthesis provider may draft claim wording only after receiving exact evidence text; pipeline-owned evidence-span links remain attached and the default path remains deterministic. | `backend/tests/test_sources.py::test_configured_synthesis_provider_drafts_only_grounded_claims` | PASS |
| 70 | The opt-in OpenAI Responses adapter sends evidence-bounded prompts with storage disabled and parses final prose without exposing credentials. | `backend/tests/test_synthesis.py::test_openai_synthesis_provider_uses_responses_api_and_records_usage` | PASS |
| 71 | Final-prose provider calls, token usage, model identity, and calculated USD spend are persisted in the run stage and project cost ledger. | `backend/tests/test_synthesis.py::test_synthesis_usage_is_recorded_in_project_costs` | PASS |

## Validation evidence

- RED checkpoints were created before each production implementation slice.
- Backend: `uv run pytest -q` → 104 passed.
- Backend coverage: `uv run pytest --cov=app --cov-report=term-missing` → see latest run below; above the 80% requirement.
- Backend lint: `uv run ruff check app tests` → PASS.
- Frontend: `npm test -- --run` → 47 passed.
- Frontend lint: `npm run lint` → PASS.
- Frontend types: `npx tsc --noEmit` → PASS.

## Known gaps

- Bounded backward and forward multi-hop expansion and local co-citation derivation are implemented with stopping reasons; richer network-saturation heuristics remain future work.
- Paid-provider approval is enforced at discovery boundaries; an approved provider adapter still must be configured before use. Zotero import/export is available through server-side credentials.
- Zotero DOI/title deduplication prefers published records and retains alternate preprint provenance; richer edition/version reconciliation remains future work.
- Discovery preserves provider citation-count and publication-date signals in provenance and exposes them during screening; they are importance/recency signals, not completeness guarantees.
- Protocol cutoff dates are enforced for discovery and expose filtered counts; records with only an unknown publication date are retained and should be reviewed as a protocol limitation rather than silently discarded.
- The default live adapter combines Semantic Scholar and OpenAlex for search and citation expansion; OpenAlex backward expansion is bounded by one metadata request per referenced work.
- Multi-source audits distinguish complete fan-out from partial fan-out; provider failures remain a limitation rather than being presented as comprehensive coverage. Route audits also expose marginal new-paper yield and overlap as coverage diagnostics.
- Full-text acquisition now supports explicitly requested public HTTP(S) text/HTML/PDF URLs with SSRF, redirect, size, and parser guards; richer HTML extraction remains future work. Abstract-backed evidence cannot certify subtle comparisons.
- The narrative checkpoint exists for broader modes; generated prose is now editable with claim/evidence links preserved. Live cross-paper comparison now uses a conservative grounded overlap heuristic; richer paragraph-level generation and section-level editing remain future work.
- Optional OpenAI Luna final-prose generation is wired through an evidence-bounded Responses adapter and its usage is ledgered; structured extraction and section-level generation remain future work.
- Living-review updates are currently on-demand and synchronous; scheduled refresh jobs remain future work.
