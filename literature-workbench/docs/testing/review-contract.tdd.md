# Review contract TDD evidence

This report records the implementation tranche derived from the review-engine plan and the canonical `related-work-guides/RELATED_WORK_WRITING_GUIDE.md`.

## User journeys

- As a researcher, I want to choose Sufficient Related Work, Comprehensive Survey, or Systematic Review so the system applies the right coverage contract.
- As a researcher, I want a projected token/API envelope before searching so I can decide whether to spend more for confidence.
- As a researcher, I want a reproducible protocol with questions, criteria, sources, cutoff, and update policy.
- As a researcher, I want discovery routes recorded separately so I can inspect how the corpus was gathered.
- As a researcher, I want an explicit corpus checkpoint audit so I know whether screening and source acquisition are complete enough to proceed.

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

## Validation evidence

- RED checkpoints were created before each production implementation slice.
- Backend: `uv run pytest -q` → 56 passed.
- Backend coverage: `uv run pytest --cov=app --cov-report=term-missing` → 89.32%, above the 80% requirement.
- Backend lint: `uv run ruff check app tests` → PASS.
- Frontend: `npm test -- --run` → 33 passed.
- Frontend lint: `npm run lint` → PASS.
- Frontend types: `npx tsc --noEmit` → PASS.

## Known gaps

- The current route families still use the configured discovery provider’s search endpoint; backward/forward/co-citation graph traversal is not implemented yet.
- “Comprehensive” and “systematic” are persisted and routed distinctly, but their full stopping certificates and PRISMA flow artifacts remain future work.
- Paid-provider approval gates and Zotero import/write-back are not implemented yet.
- Full-text acquisition remains conservative; abstract-backed evidence cannot certify subtle comparisons.
- The narrative checkpoint and grounded draft-generation stage are not yet implemented.
