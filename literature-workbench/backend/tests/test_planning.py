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
        assert client.get(f"/projects/{project_id}/plans").json()["plans"][0]["title"] == "Edited review"


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
            json={"title": "x", "thesis": "x", "organizing_principle": "x", "sections": []},
        )
        assert invalid.status_code == 422
        assert foreign.status_code == 404
