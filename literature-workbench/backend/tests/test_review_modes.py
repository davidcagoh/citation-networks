from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.domain import ResourceEnvelope, ScopePreviewRequest
from app.main import create_app
from app.models import ResearchBrief, Run


def test_scope_preview_request_supports_the_three_review_contracts() -> None:
    assert ScopePreviewRequest(mode="sufficient").mode == "sufficient"
    assert ScopePreviewRequest(mode="comprehensive").mode == "comprehensive"
    assert ScopePreviewRequest(mode="systematic").mode == "systematic"


def test_resource_envelope_rejects_negative_limits() -> None:
    try:
        ResourceEnvelope(max_external_api_calls=-1)
    except ValueError as exc:
        assert "greater than or equal to 0" in str(exc)
    else:
        raise AssertionError("negative API-call limits must be rejected")


def test_scope_preview_exposes_mode_specific_resource_envelope(tmp_path: Path) -> None:
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}")
    with TestClient(app) as client:
        project_id = client.post(
            "/projects",
            json={"title": "Memory", "prompt": "Survey memory systems for LLM agents"},
        ).json()["id"]

        response = client.post(
            f"/projects/{project_id}/runs/scope-preview",
            json={"mode": "systematic", "max_papers": 100},
        )

        assert response.status_code == 201
        budget = response.json()["budget"]
        assert budget["mode"] == "systematic"
        assert budget["recommended"] is True
        assert budget["max_papers"] == 100
        assert budget["estimated_external_api_calls"] > 1
        assert budget["estimated_input_tokens"] > 0
        assert budget["estimated_cost_usd"] >= 0


def test_scope_preview_rejects_unknown_review_mode(tmp_path: Path) -> None:
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}")
    with TestClient(app) as client:
        project_id = client.post(
            "/projects",
            json={"title": "Memory", "prompt": "Survey memory systems for LLM agents"},
        ).json()["id"]

        response = client.post(
            f"/projects/{project_id}/runs/scope-preview",
            json={"mode": "everything", "max_papers": 20},
        )

        assert response.status_code == 422


def test_project_and_run_persist_the_selected_review_mode(tmp_path: Path) -> None:
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}")
    with TestClient(app) as client:
        project_id = client.post(
            "/projects",
            json={
                "title": "Memory",
                "prompt": "Survey memory systems for LLM agents",
                "review_mode": "systematic",
            },
        ).json()["id"]
        client.post(f"/projects/{project_id}/fixtures/provenance-corpus")
        response = client.post(
            f"/projects/{project_id}/runs/pipeline",
            json={"review_mode": "systematic"},
        )

        assert response.status_code == 201
        assert response.json()["review_mode"] == "systematic"
        with app.state.database.session() as database:
            brief = database.scalar(
                select(ResearchBrief).where(ResearchBrief.project_id == project_id)
            )
            run = database.scalar(select(Run).where(Run.project_id == project_id))
            assert brief is not None and brief.review_mode == "systematic"
            assert run is not None and run.review_mode == "systematic"


def test_broader_review_runs_pause_for_corpus_approval(tmp_path: Path) -> None:
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}")
    with TestClient(app) as client:
        project_id = client.post(
            "/projects",
            json={"title": "Memory", "prompt": "Survey memory", "review_mode": "systematic"},
        ).json()["id"]
        client.post(f"/projects/{project_id}/fixtures/provenance-corpus")

        pending = client.post(
            f"/projects/{project_id}/runs/pipeline",
            json={"review_mode": "systematic"},
        )

        assert pending.status_code == 201
        assert pending.json()["status"] == "awaiting_corpus_approval"
        run_id = pending.json()["id"]
        assert client.get(f"/projects/{project_id}/runs/{run_id}").json()["stages"] == []

        approved = client.post(f"/projects/{project_id}/runs/{run_id}/approve-corpus")
        assert approved.status_code == 201
        assert approved.json()["status"] == "awaiting_structure_approval"
        structure_approved = client.post(
            f"/projects/{project_id}/runs/{run_id}/approve-structure"
        )
        assert structure_approved.status_code == 201
        assert structure_approved.json()["status"] == "completed"
