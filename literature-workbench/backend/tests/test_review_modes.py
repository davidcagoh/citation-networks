from pathlib import Path

from fastapi.testclient import TestClient

from app.domain import ResourceEnvelope, ScopePreviewRequest
from app.main import create_app


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
