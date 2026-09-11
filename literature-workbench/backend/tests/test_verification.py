from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import create_app
from app.models import SynthesisClaim, VerificationIssue


def _completed_project(client: TestClient) -> str:
    project_id = client.post(
        "/projects", json={"title": "Memory", "prompt": "Survey memory systems"}
    ).json()["id"]
    assert client.post(f"/projects/{project_id}/fixtures/provenance-corpus").status_code == 201
    assert client.post(f"/projects/{project_id}/runs/pipeline").status_code == 201
    return project_id


def test_verification_passes_for_grounded_fixture(tmp_path: Path) -> None:
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}")
    with TestClient(app) as client:
        project_id = _completed_project(client)
        response = client.post(f"/projects/{project_id}/runs/verification")

        assert response.status_code == 201
        assert response.json()["issue_count"] == 0
        assert client.get(f"/projects/{project_id}/verification").json()["issues"] == []


def test_verification_flags_unsupported_claim_and_allows_resolution(tmp_path: Path) -> None:
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}")
    with TestClient(app) as client:
        project_id = _completed_project(client)
        with app.state.database.session() as database:
            claim = database.scalar(select(SynthesisClaim).where(SynthesisClaim.project_id == project_id))
            assert claim is not None
            claim.supporting_evidence_span_ids = []

        response = client.post(f"/projects/{project_id}/runs/verification")
        assert response.status_code == 201
        assert response.json()["issue_count"] == 1
        issue = client.get(f"/projects/{project_id}/verification").json()["issues"][0]
        assert issue["severity"] == "high"
        assert issue["status"] == "open"
        assert "evidence" in issue["message"]

        resolved = client.patch(
            f"/projects/{project_id}/verification/{issue['id']}",
            json={"status": "resolved"},
        )
        assert resolved.status_code == 200
        assert resolved.json()["status"] == "resolved"

        with app.state.database.session() as database:
            assert database.scalar(select(VerificationIssue.status).where(VerificationIssue.id == issue["id"])) == "resolved"
