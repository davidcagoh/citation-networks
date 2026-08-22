# Slice 1 TDD Evidence

## Source and journey

Source: [`lit_review_pipeline_handoff.md`](../../lit_review_pipeline_handoff.md),
Milestone 1.

As a researcher, I can create a project, ingest the bundled five-paper corpus,
run the deterministic pipeline, open the generated review, and inspect exact
source evidence for each substantive claim.

## RED → GREEN evidence

- Backend RED: `uv run --project literature-workbench/backend --extra dev pytest literature-workbench/backend/tests -q`
  collected the tests and failed because `app.main` and `app.db` did not exist.
- Frontend RED: `npm test -- --run` compiled the test target and failed because
  `@/features/workbench/WorkbenchApp` did not exist.
- Backend GREEN: `uv run --extra dev pytest tests --cov=app --cov-report=term-missing -q`
  passes 21 tests with 88.89% total coverage.
- Frontend GREEN: `npm run test:coverage` passes 16 tests with 95.16%
  statements, 83.21% branches, 100% functions, and 98.36% lines.
- Live GREEN: `npm run test:e2e` passes the browser journey; a three-run serial
  repeat also passed 3/3.

Checkpoint commits were deliberately deferred because the governing MVP
workflow requires explicit approval at the pre-commit gate.

## Guarantees

| Guarantee | Evidence | Type | Result |
|---|---|---|---|
| Evidence spans exactly match persisted source offsets | `backend/tests/test_provenance.py` | Unit | PASS |
| Cross-paper/project provenance references are rejected | `backend/tests/test_provenance.py`, `backend/tests/test_hardening.py` | Unit/integration | PASS |
| Five supplied papers produce grounded claims and an inspectable evidence chain | `backend/tests/test_pipeline.py` | Integration | PASS |
| Degraded and replaced documents reconcile downstream artifacts safely | `backend/tests/test_hardening.py` | Integration | PASS |
| Interrupted stages resume without duplicating completed work | `backend/tests/test_hardening.py` | Integration | PASS |
| Project deletion removes its complete owned graph with foreign keys enforced | `backend/tests/test_hardening.py` | Integration | PASS |
| Project state, accessible tabs, and evidence races behave correctly | `frontend/tests/workbench.test.tsx` | Component | PASS |
| API response normalization preserves the frontend contract | `frontend/tests/api.test.ts` | Unit | PASS |
| A live browser can create, run, and inspect a synthesized claim's two exact source spans | `frontend/tests/e2e/review-evidence.spec.ts` | E2E | PASS |

## Additional checks

- `uv run --extra dev ruff check app tests migrations` — PASS
- `npm run lint` — PASS
- `npm run build` — PASS
- Alembic upgrade/check/downgrade and model-schema parity — PASS

Known warning: Starlette currently emits a deprecation warning for its
`httpx`-based `TestClient`; it does not affect test behavior.
