from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


def test_ingests_user_supplied_full_text_with_provenance(tmp_path: Path) -> None:
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}")
    with TestClient(app) as client:
        project_id = client.post(
            "/projects", json={"title": "Memory", "prompt": "Survey memory systems"}
        ).json()["id"]
        response = client.post(
            f"/projects/{project_id}/sources/text",
            json={
                "title": "A Full Text Study",
                "authors": ["A. Researcher"],
                "year": 2026,
                "source_uri": "file:///research/full-text.txt",
                "text": "The study evaluates a memory architecture across two workloads.",
            },
        )

        assert response.status_code == 201
        body = response.json()
        assert body["status"] == "included"
        paper_id = body["paper_id"]
        corpus = client.get(f"/projects/{project_id}/corpus").json()
        assert corpus["papers"][0]["id"] == paper_id
        assert corpus["papers"][0]["document_status"] == "complete"

        run = client.post(f"/projects/{project_id}/runs/pipeline")
        assert run.status_code == 201
        review = client.get(f"/projects/{project_id}/review").json()["sentences"]
        assert review[0]["text"] == "The study evaluates a memory architecture across two workloads."


def test_source_ingestion_rejects_blank_text_and_unknown_project(tmp_path: Path) -> None:
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}")
    with TestClient(app) as client:
        assert client.post(
            "/projects/missing/sources/text",
            json={"title": "Source", "source_uri": "file:///source", "text": "Text."},
        ).status_code == 404
        project_id = client.post(
            "/projects", json={"title": "Memory", "prompt": "Survey memory systems"}
        ).json()["id"]
        response = client.post(
            f"/projects/{project_id}/sources/text",
            json={"title": "Empty", "source_uri": "file:///empty", "text": " "},
        )
        assert response.status_code == 422
