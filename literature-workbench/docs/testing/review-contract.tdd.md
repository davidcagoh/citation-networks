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

## Validation evidence

- RED checkpoints were created before each production implementation slice.
- Backend: `uv run pytest -q` → 65 passed.
- Backend coverage: `uv run pytest --cov=app --cov-report=term-missing` → 87.20%, above the 80% requirement.
- Backend lint: `uv run ruff check app tests` → PASS.
- Frontend: `npm test -- --run` → 44 passed.
- Frontend lint: `npm run lint` → PASS.
- Frontend types: `npx tsc --noEmit` → PASS.

## Known gaps

- Backward and forward citation expansion are implemented; multi-hop traversal, co-citation, and stopping rules for network saturation remain future work.
- Paid-provider approval is enforced at discovery boundaries; an approved provider adapter still must be configured before use. Zotero import/export is available through server-side credentials.
- Full-text acquisition remains conservative; abstract-backed evidence cannot certify subtle comparisons.
- The narrative checkpoint exists for broader modes; generated prose is now editable with claim/evidence links preserved. Richer paragraph-level generation and section-level editing remain future work.
- Living-review updates are currently on-demand and synchronous; scheduled refresh jobs remain future work.
