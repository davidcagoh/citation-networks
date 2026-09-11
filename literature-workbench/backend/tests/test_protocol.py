from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import create_app
from app.models import ResearchBrief
from app.services.discovery import DiscoveryCandidate


class ProtocolDiscoveryProvider:
    name = "protocol-search"

    def search(self, query: str, limit: int) -> list[DiscoveryCandidate]:
        return [
            DiscoveryCandidate(
                external_id="paper-1",
                title="Study for memory",
                authors=["Researcher"],
                year=2025,
                venue="Test Venue",
                doi=None,
                abstract="Abstract.",
                source_uri="https://example.test/memory-1",
                score=0.9,
            ),
            DiscoveryCandidate(
                external_id="paper-2",
                title="Follow-up for memory",
                authors=["Researcher"],
                year=2024,
                venue="Test Venue",
                doi=None,
                abstract="Abstract.",
                source_uri="https://example.test/memory-2",
                score=0.8,
            ),
        ][:limit]


def test_project_protocol_is_created_and_can_be_updated(tmp_path: Path) -> None:
    app = create_app(
        f"sqlite:///{tmp_path / 'workbench.db'}", discovery_provider=ProtocolDiscoveryProvider()
    )
    with TestClient(app) as client:
        project_id = client.post(
            "/projects",
            json={"title": "Memory", "prompt": "Survey memory", "review_mode": "systematic"},
        ).json()["id"]

        initial = client.get(f"/projects/{project_id}/protocol")
        assert initial.status_code == 200
        assert initial.json()["review_mode"] == "systematic"
        assert initial.json()["research_questions"] == ["Survey memory"]

        update = client.put(
            f"/projects/{project_id}/protocol",
            json={
                "review_mode": "comprehensive",
                "research_questions": ["Which memory mechanisms improve retrieval?"],
                "inclusion_criteria": ["Peer-reviewed or openly archived primary studies"],
                "exclusion_criteria": ["Opinion pieces without empirical or formal evidence"],
                "sources": ["zotero", "openalex", "semantic-scholar"],
                "cutoff_date": "2026-09-10",
                "update_policy": "on_demand",
            },
        )

        assert update.status_code == 200
        body = update.json()
        assert body["research_questions"] == ["Which memory mechanisms improve retrieval?"]
        assert body["cutoff_date"] == "2026-09-10"
        assert body["update_policy"] == "on_demand"
        assert body["updated_at"]
        with app.state.database.session() as database:
            stored_brief = database.scalar(
                select(ResearchBrief).where(ResearchBrief.project_id == project_id)
            )
            assert stored_brief is not None
            assert stored_brief.review_mode == "comprehensive"


def test_protocol_requires_questions_and_valid_update_policy(tmp_path: Path) -> None:
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}")
    with TestClient(app) as client:
        project_id = client.post(
            "/projects", json={"title": "Memory", "prompt": "Survey memory"}
        ).json()["id"]
        response = client.put(
            f"/projects/{project_id}/protocol",
            json={"research_questions": [], "update_policy": "continuous"},
        )
        assert response.status_code == 422


def test_prisma_report_reconciles_protocol_search_and_screening_flow(tmp_path: Path) -> None:
    app = create_app(
        f"sqlite:///{tmp_path / 'workbench.db'}", discovery_provider=ProtocolDiscoveryProvider()
    )
    with TestClient(app) as client:
        project_id = client.post(
            "/projects",
            json={"title": "Memory", "prompt": "Survey memory", "review_mode": "systematic"},
        ).json()["id"]
        client.post(
            f"/projects/{project_id}/runs/discovery",
            json={"query": "memory", "limit": 2, "routes": ["semantic_search", "recent_search"]},
        )
        corpus = client.get(f"/projects/{project_id}/corpus").json()["papers"]
        client.patch(
            f"/projects/{project_id}/corpus/{corpus[0]['id']}",
            json={"status": "included"},
        )
        client.patch(
            f"/projects/{project_id}/corpus/{corpus[1]['id']}",
            json={"status": "excluded"},
        )

        report = client.get(f"/projects/{project_id}/prisma-report")

        assert report.status_code == 200
        body = report.json()
        assert body["review_mode"] == "systematic"
        assert body["flow"] == {
            "identified": 4,
            "unique_identified": 2,
            "duplicates_removed": 2,
            "screened": 2,
            "reports_sought": 1,
            "reports_not_retrieved": 0,
            "included": 1,
            "excluded": 1,
        }
        assert body["search"]["routes"] == ["semantic_search", "recent_search"]
        assert body["search"]["queries"] == ["memory", "memory recent latest"]
