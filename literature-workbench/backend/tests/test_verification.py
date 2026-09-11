from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import create_app
from app.models import (
    EvidenceSpan,
    Paper,
    ReviewSentence,
    ScientificEntity,
    SynthesisClaim,
    VerificationIssue,
)


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
            claim = database.scalar(
                select(SynthesisClaim).where(SynthesisClaim.project_id == project_id)
            )
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
            assert database.scalar(
                select(VerificationIssue.status).where(VerificationIssue.id == issue["id"])
            ) == "resolved"


def test_verification_rejects_evidence_from_another_project(tmp_path: Path) -> None:
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}")
    with TestClient(app) as client:
        first = _completed_project(client)
        second = _completed_project(client)
        with app.state.database.session() as database:
            foreign_span = database.scalar(
                select(EvidenceSpan)
                .join(Paper, Paper.id == EvidenceSpan.paper_id)
                .where(Paper.project_id == second)
            )
            claim = database.scalar(
                select(SynthesisClaim).where(SynthesisClaim.project_id == first)
            )
            assert foreign_span is not None and claim is not None
            assert foreign_span is not None
            claim.supporting_evidence_span_ids = [foreign_span.id]

        response = client.post(f"/projects/{first}/runs/verification")
        assert response.status_code == 201
        assert response.json()["issue_count"] == 1


def test_verification_flags_cross_source_claim_without_relation(tmp_path: Path) -> None:
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}")
    with TestClient(app) as client:
        project_id = _completed_project(client)
        with app.state.database.session() as database:
            claim = database.scalar(
                select(SynthesisClaim).where(SynthesisClaim.project_id == project_id)
            )
            assert claim is not None
            claim.inference_level = "cross_source_synthesis"
            claim.supporting_relation_ids = []

        response = client.post(f"/projects/{project_id}/runs/verification")

        assert response.status_code == 201
        assert response.json()["issue_count"] == 1
        issue = client.get(f"/projects/{project_id}/verification").json()["issues"][0]
        assert issue["issue_type"] == "unsupported_synthesis"
        assert issue["severity"] == "medium"


def test_verification_flags_causal_language_for_manual_review(tmp_path: Path) -> None:
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}")
    with TestClient(app) as client:
        project_id = _completed_project(client)
        with app.state.database.session() as database:
            claim = database.scalar(
                select(SynthesisClaim).where(SynthesisClaim.project_id == project_id)
            )
            assert claim is not None
            claim.text = "The method improved retrieval because it consolidated memory."

        response = client.post(f"/projects/{project_id}/runs/verification")

        assert response.status_code == 201
        issues = client.get(f"/projects/{project_id}/verification").json()["issues"]
        assert any(issue["issue_type"] == "causal_language" for issue in issues)


def test_verification_flags_substantive_uncited_review_sentence(tmp_path: Path) -> None:
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}")
    with TestClient(app) as client:
        project_id = _completed_project(client)
        with app.state.database.session() as database:
            database.add(
                ReviewSentence(
                    project_id=project_id,
                    section_title="Manual interpretation",
                    position=999,
                    text="This is an uncited substantive interpretation.",
                    substantive=True,
                    claim_id=None,
                )
            )

        response = client.post(f"/projects/{project_id}/runs/verification")

        assert response.status_code == 201
        issues = client.get(f"/projects/{project_id}/verification").json()["issues"]
        assert any(issue["issue_type"] == "citation_completeness" for issue in issues)


def test_verification_flags_claims_behind_corpus_date_frontier(tmp_path: Path) -> None:
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}")
    with TestClient(app) as client:
        project_id = _completed_project(client)
        with app.state.database.session() as database:
            papers = list(database.scalars(select(Paper).where(Paper.project_id == project_id)))
            for paper in papers:
                paper.year = 2020
            papers[-1].year = 2026
            claim = database.scalar(
                select(SynthesisClaim).where(SynthesisClaim.project_id == project_id)
            )
            assert claim is not None
            source_entity = database.get(ScientificEntity, claim.supporting_entity_ids[-1])
            assert source_entity is not None
            source_entity.extraction_method = "text-heuristic-v1"
            source_paper = database.get(Paper, source_entity.paper_id)
            assert source_paper is not None
            source_paper.year = 2020

        response = client.post(f"/projects/{project_id}/runs/verification")

        assert response.status_code == 201
        issues = client.get(f"/projects/{project_id}/verification").json()["issues"]
        assert any(issue["issue_type"] == "freshness" for issue in issues)
