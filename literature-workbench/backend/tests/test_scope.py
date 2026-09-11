from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


def test_scope_preview_returns_transparent_scope_and_budget(tmp_path: Path) -> None:
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}")
    with TestClient(app) as client:
        project_id = client.post(
            "/projects",
            json={"title": "Memory", "prompt": "Survey memory systems for LLM agents"},
        ).json()["id"]

        response = client.post(
            f"/projects/{project_id}/runs/scope-preview",
            json={"mode": "thorough", "max_papers": 30},
        )

        assert response.status_code == 201
        body = response.json()
        assert body["scope"]["query"] == "Survey memory systems for LLM agents"
        assert body["scope"]["mode"] == "thorough"
        assert body["scope"]["suggested_focus"]
        assert body["budget"] == {
            "mode": "comprehensive",
            "recommended": True,
            "max_papers": 30,
            "max_external_api_calls": 180,
            "estimated_external_api_calls": 180,
            "estimated_discovery_api_calls": 18,
            "estimated_pipeline_api_calls": 180,
            "estimated_total_api_calls": 198,
            "estimated_input_tokens": 36_000,
            "estimated_output_tokens": 18_000,
            "estimated_cost_usd": 0.0288,
        }


def test_scope_preview_rejects_unknown_project(tmp_path: Path) -> None:
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}")
    with TestClient(app) as client:
        response = client.post("/projects/missing/runs/scope-preview", json={})
        assert response.status_code == 404
