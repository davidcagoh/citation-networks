import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


def _completed_project(client: TestClient) -> str:
    project_id = client.post(
        "/projects", json={"title": "Memory", "prompt": "Survey memory systems"}
    ).json()["id"]
    assert client.post(f"/projects/{project_id}/fixtures/provenance-corpus").status_code == 201
    assert client.post(f"/projects/{project_id}/runs/pipeline").status_code == 201
    return project_id


def test_exports_markdown_json_and_bibtex(tmp_path: Path) -> None:
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}")
    with TestClient(app) as client:
        project_id = _completed_project(client)

        markdown = client.get(f"/projects/{project_id}/export?format=markdown")
        assert markdown.status_code == 200
        assert markdown.headers["content-type"].startswith("text/markdown")
        assert "# Evidence structure for Memory" in markdown.text
        assert "## From traces to consolidation" in markdown.text

        exported_json = client.get(f"/projects/{project_id}/export?format=json")
        assert exported_json.status_code == 200
        body = exported_json.json()
        assert body["project"]["title"] == "Memory"
        assert len(body["corpus"]) == 5
        assert body["review"]["sentences"]

        bibtex = client.get(f"/projects/{project_id}/export?format=bibtex")
        assert bibtex.status_code == 200
        assert bibtex.headers["content-type"].startswith("application/x-bibtex")
        assert "@article{" in bibtex.text


def test_export_validates_format_and_project(tmp_path: Path) -> None:
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}")
    with TestClient(app) as client:
        assert client.get("/projects/missing/export?format=markdown").status_code == 404
        project_id = client.post(
            "/projects", json={"title": "Memory", "prompt": "Survey memory systems"}
        ).json()["id"]
        invalid = client.get(f"/projects/{project_id}/export?format=pdf")
        assert invalid.status_code == 422
