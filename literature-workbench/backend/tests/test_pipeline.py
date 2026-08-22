from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import create_app
from app.models import SourceDocument


def test_fixture_pipeline_preserves_complete_claim_provenance(tmp_path: Path) -> None:
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}")
    with TestClient(app) as client:
        project = client.post(
            "/projects",
            json={"title": "Agent memory", "prompt": "Survey memory systems for LLM agents."},
        ).json()

        ingest = client.post(f"/projects/{project['id']}/fixtures/provenance-corpus")
        assert ingest.status_code == 201
        assert ingest.json()["paper_count"] == 5

        run = client.post(f"/projects/{project['id']}/runs/pipeline")
        assert run.status_code == 201
        assert run.json()["status"] == "completed"

        review = client.get(f"/projects/{project['id']}/review").json()
        substantive = [sentence for sentence in review["sentences"] if sentence["substantive"]]
        assert substantive
        assert sum(bool(sentence["claim_id"]) for sentence in substantive) / len(substantive) >= 0.9

        evidence = client.get(
            f"/projects/{project['id']}/claims/{substantive[0]['claim_id']}/evidence"
        )
        assert evidence.status_code == 200
        body = evidence.json()
        assert body["claim"]["text"] == substantive[0]["text"]
        assert body["evidence"]
        first = body["evidence"][0]
        local_start = first["start_offset"] - first["excerpt_start_offset"]
        local_end = first["end_offset"] - first["excerpt_start_offset"]
        source_excerpt = first["source_excerpt"][local_start:local_end]
        assert first["verbatim_text"] == source_excerpt
        assert first["paper_title"]

        stages = client.get(f"/projects/{project['id']}/runs/{run.json()['id']}").json()["stages"]
        assert [stage["stage"] for stage in stages] == [
            "extraction",
            "relations",
            "planning",
            "writing",
        ]
        assert all(stage["status"] == "completed" for stage in stages)


def test_malformed_fixture_document_degrades_without_aborting(tmp_path: Path) -> None:
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}")
    with TestClient(app) as client:
        project_id = client.post(
            "/projects", json={"title": "Test", "prompt": "Test degraded sources"}
        ).json()["id"]
        client.post(f"/projects/{project_id}/fixtures/provenance-corpus")
        response = client.post(f"/projects/{project_id}/runs/pipeline")
        assert response.status_code == 201
        corpus = client.get(f"/projects/{project_id}/corpus").json()
        assert any(paper["document_status"] == "degraded" for paper in corpus["papers"])


def test_pipeline_skips_a_newly_malformed_core_document(tmp_path: Path) -> None:
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}")
    with TestClient(app) as client:
        project_id = client.post(
            "/projects", json={"title": "Test", "prompt": "Test degraded sources"}
        ).json()["id"]
        client.post(f"/projects/{project_id}/fixtures/provenance-corpus")
        with app.state.database.session() as database:
            documents = list(database.scalars(select(SourceDocument).order_by(SourceDocument.id)))
            documents[1].text = None
            documents[1].parsing_quality = "degraded"

        response = client.post(f"/projects/{project_id}/runs/pipeline")

        assert response.status_code == 201
        assert response.json()["status"] == "completed"
        review = client.get(f"/projects/{project_id}/review").json()
        assert review["sentences"]
