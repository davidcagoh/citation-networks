from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app
from app.services.synthesis import StructuredExtraction


def _completed_project(client: TestClient) -> str:
    project_id = client.post(
        "/projects", json={"title": "Memory", "prompt": "Survey memory systems"}
    ).json()["id"]
    assert client.post(f"/projects/{project_id}/fixtures/provenance-corpus").status_code == 201
    assert client.post(f"/projects/{project_id}/runs/pipeline").status_code == 201
    return project_id


def test_plan_can_be_edited_without_rerunning_extraction(tmp_path: Path) -> None:
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}")
    with TestClient(app) as client:
        project_id = _completed_project(client)
        plan = client.get(f"/projects/{project_id}/plans").json()["plans"][0]
        response = client.patch(
            f"/projects/{project_id}/plans/{plan['id']}",
            json={
                "title": "Edited review",
                "thesis": "Failures motivate distinct design responses.",
                "organizing_principle": "failure → response",
                "sections": [
                    {
                        "title": "Failure modes",
                        "purpose": "Describe the motivating failures.",
                        "planned_claim_ids": plan["sections"][0]["planned_claim_ids"],
                        "relation_ids": plan["sections"][0]["relation_ids"],
                        "paper_ids": plan["sections"][0]["paper_ids"],
                    }
                ],
            },
        )

        assert response.status_code == 200
        assert response.json()["title"] == "Edited review"
        assert response.json()["sections"][0]["title"] == "Failure modes"
        persisted = client.get(f"/projects/{project_id}/plans").json()["plans"][0]
        assert persisted["title"] == "Edited review"


def test_plan_update_rejects_invalid_or_foreign_plan(tmp_path: Path) -> None:
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}")
    with TestClient(app) as client:
        first_project = _completed_project(client)
        second_project = _completed_project(client)
        plan = client.get(f"/projects/{first_project}/plans").json()["plans"][0]
        invalid = client.patch(
            f"/projects/{first_project}/plans/{plan['id']}",
            json={"title": "", "thesis": "x", "organizing_principle": "x", "sections": []},
        )
        foreign = client.patch(
            f"/projects/{second_project}/plans/{plan['id']}",
            json={
                "title": "x",
                "thesis": "x",
                "organizing_principle": "x",
                "sections": [{"title": "x", "purpose": "x"}],
            },
        )
        assert invalid.status_code == 422
        assert foreign.status_code == 404


def test_plan_update_rejects_artifact_ids_outside_project(tmp_path: Path) -> None:
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}")
    with TestClient(app) as client:
        project_id = _completed_project(client)
        plan = client.get(f"/projects/{project_id}/plans").json()["plans"][0]
        response = client.patch(
            f"/projects/{project_id}/plans/{plan['id']}",
            json={
                "title": plan["title"],
                "thesis": plan["thesis"],
                "organizing_principle": plan["organizing_principle"],
                "sections": [{
                    **plan["sections"][0],
                    "planned_claim_ids": ["foreign-claim"],
                }],
            },
        )

        assert response.status_code == 422
        assert "claim" in response.json()["detail"]


def test_plan_edit_rewrites_review_sections(tmp_path: Path) -> None:
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}")
    with TestClient(app) as client:
        project_id = _completed_project(client)
        plan = client.get(f"/projects/{project_id}/plans").json()["plans"][0]
        response = client.patch(
            f"/projects/{project_id}/plans/{plan['id']}",
            json={
                "title": plan["title"],
                "thesis": plan["thesis"],
                "organizing_principle": plan["organizing_principle"],
                "sections": [{**plan["sections"][0], "title": "Edited section"}],
            },
        )

        assert response.status_code == 200
        review = client.get(f"/projects/{project_id}/review").json()["sentences"]
        assert review
        assert all(sentence["section_title"] == "Edited section" for sentence in review)


def test_live_plan_uses_extracted_types_instead_of_topic_specific_headings(
    tmp_path: Path,
) -> None:
    class QuantumExtractor:
        def extract_evidence_bundle(self, paper_title: str, source_text: str):
            return [
                StructuredExtraction(
                    "method",
                    "quantum measurement",
                    "The method improves measurement sensitivity.",
                    "The method improves measurement sensitivity",
                ),
                StructuredExtraction(
                    "limitation",
                    "noise",
                    "Noise limits measurement quality.",
                    "noise limitation",
                ),
            ]

        def draft_claim(self, default_text: str, evidence_texts: list[str], claim_type: str):
            return default_text

    app = create_app(
        f"sqlite:///{tmp_path / 'workbench.db'}", synthesis_provider=QuantumExtractor()
    )
    with TestClient(app) as client:
        project_id = client.post(
            "/projects",
            json={"title": "Quantum sensing", "prompt": "Survey quantum sensing methods"},
        ).json()["id"]
        assert client.post(
            f"/projects/{project_id}/sources/text",
            json={
                "title": "Quantum sensing study",
                "source_uri": "file:///quantum-sensing",
                "text": "The method improves measurement sensitivity but has a noise limitation.",
            },
        ).status_code == 201
        assert client.post(f"/projects/{project_id}/runs/pipeline").status_code == 201

        plan = client.get(f"/projects/{project_id}/plans").json()["plans"][0]
        assert "memory" not in plan["title"].lower()
        assert plan["organizing_principle"] == "problem → mechanism → evidence → trade-off"
        assert any(section["title"] == "Methods and mechanisms" for section in plan["sections"])
        assert plan["sections"]
