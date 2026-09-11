from dataclasses import dataclass
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.main import create_app
from app.models import (
    CorpusMembership,
    DiscoveryEvent,
    EvidenceSpan,
    Paper,
    ReviewSentence,
    ScientificRelation,
    SourceDocument,
    SynthesisClaim,
    UsageCostEvent,
)


@dataclass(frozen=True)
class FakeCandidate:
    external_id: str
    title: str
    authors: list[str]
    year: int
    venue: str
    doi: str | None
    abstract: str
    source_uri: str
    score: float


class FakeDiscoveryProvider:
    name = "fake-search"

    def __init__(self) -> None:
        self.queries: list[tuple[str, int]] = []

    def search(self, query: str, limit: int) -> list[FakeCandidate]:
        self.queries.append((query, limit))
        return [
            FakeCandidate(
                external_id="paper-1",
                title="Memory Systems",
                authors=["A. Researcher"],
                year=2025,
                venue="Test Venue",
                doi="10.1234/memory",
                abstract="A study of memory systems.",
                source_uri="https://example.test/paper-1",
                score=0.91,
            ),
            FakeCandidate(
                external_id="paper-2",
                title="Memory Systems: A Follow-up",
                authors=["B. Researcher"],
                year=2024,
                venue="Test Venue",
                doi=None,
                abstract="A follow-up study.",
                source_uri="https://example.test/paper-2",
                score=0.82,
            ),
        ][:limit]


def test_discovery_persists_candidates_and_route_provenance(tmp_path: Path) -> None:
    provider = FakeDiscoveryProvider()
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}", discovery_provider=provider)
    with TestClient(app) as client:
        project_id = client.post(
            "/projects", json={"title": "Memory", "prompt": "Find memory systems"}
        ).json()["id"]

        response = client.post(
            f"/projects/{project_id}/runs/discovery",
            json={"query": "agent memory", "limit": 2},
        )

        assert response.status_code == 201
        assert response.json()["candidate_count"] == 2
        assert provider.queries == [("agent memory", 2)]

        corpus = client.get(f"/projects/{project_id}/corpus").json()
        assert corpus["coverage"]["candidates"] == 2
        assert all(item["status"] == "candidate" for item in corpus["papers"])
        assert all(item["discovery_routes"] == ["semantic_search"] for item in corpus["papers"])

        with app.state.database.session() as database:
            assert database.scalar(
                select(func.count()).select_from(DiscoveryEvent).where(
                    DiscoveryEvent.project_id == project_id
                )
            ) == 2
            documents = list(database.scalars(select(SourceDocument)))
            assert len(documents) == 2
            assert {document.source_type for document in documents} == {"abstract"}
            assert {document.parser for document in documents} == {"fake-search-abstract-v1"}
            assert {document.text for document in documents} == {
                "A study of memory systems.",
                "A follow-up study.",
            }
            usage = list(
                database.scalars(
                    select(UsageCostEvent).where(UsageCostEvent.project_id == project_id)
                )
            )
            assert len(usage) == 1
            assert usage[0].provider == "fake-search"
            assert usage[0].external_api_calls == 1
            assert usage[0].run_id is None


def test_discovery_deduplicates_same_provider_result(tmp_path: Path) -> None:
    provider = FakeDiscoveryProvider()
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}", discovery_provider=provider)
    with TestClient(app) as client:
        project_id = client.post(
            "/projects", json={"title": "Memory", "prompt": "Find memory systems"}
        ).json()["id"]
        path = f"/projects/{project_id}/runs/discovery"

        assert client.post(path, json={"query": "memory", "limit": 2}).status_code == 201
        assert client.post(path, json={"query": "memory", "limit": 2}).status_code == 201

        with app.state.database.session() as database:
            assert database.scalar(
                select(func.count()).select_from(Paper).where(Paper.project_id == project_id)
            ) == 2
            assert database.scalar(
                select(func.count()).select_from(CorpusMembership).where(
                    CorpusMembership.project_id == project_id
                )
            ) == 2
            assert database.scalar(
                select(func.count()).select_from(DiscoveryEvent).where(
                    DiscoveryEvent.project_id == project_id
                )
            ) == 4


def test_discovery_validates_query_and_limit(tmp_path: Path) -> None:
    app = create_app(
        f"sqlite:///{tmp_path / 'workbench.db'}",
        discovery_provider=FakeDiscoveryProvider(),
    )
    with TestClient(app) as client:
        project_id = client.post(
            "/projects", json={"title": "Memory", "prompt": "Find memory systems"}
        ).json()["id"]
        path = f"/projects/{project_id}/runs/discovery"

        assert client.post(path, json={"query": " ", "limit": 10}).status_code == 422
        assert client.post(path, json={"query": "memory", "limit": 0}).status_code == 422
        assert client.post(path, json={"query": "memory", "limit": 101}).status_code == 422


def test_discovered_abstract_can_flow_to_grounded_review(tmp_path: Path) -> None:
    app = create_app(
        f"sqlite:///{tmp_path / 'workbench.db'}",
        discovery_provider=FakeDiscoveryProvider(),
    )
    with TestClient(app) as client:
        project_id = client.post(
            "/projects", json={"title": "Memory", "prompt": "Find memory systems"}
        ).json()["id"]
        client.post(
            f"/projects/{project_id}/runs/discovery",
            json={"query": "agent memory", "limit": 1},
        )
        paper_id = client.get(f"/projects/{project_id}/corpus").json()["papers"][0]["id"]
        assert client.patch(
            f"/projects/{project_id}/corpus/{paper_id}",
            json={"status": "included"},
        ).status_code == 200

        response = client.post(f"/projects/{project_id}/runs/pipeline")
        assert response.status_code == 201
        assert response.json()["status"] == "completed"

        with app.state.database.session() as database:
            assert database.scalar(
                select(func.count()).select_from(EvidenceSpan).where(
                    EvidenceSpan.paper_id == paper_id
                )
            ) == 1
            assert database.scalar(
                select(func.count()).select_from(SynthesisClaim).where(
                    SynthesisClaim.project_id == project_id
                )
            ) == 1
            sentence = database.scalar(
                select(ReviewSentence).where(ReviewSentence.project_id == project_id)
            )
            assert sentence is not None
            assert sentence.text == "A study of memory systems."
            assert database.scalar(
                select(func.count()).select_from(ScientificRelation).where(
                    ScientificRelation.project_id == project_id
                )
            ) == 0


def test_pipeline_requires_an_included_or_pinned_paper(tmp_path: Path) -> None:
    app = create_app(
        f"sqlite:///{tmp_path / 'workbench.db'}",
        discovery_provider=FakeDiscoveryProvider(),
    )
    with TestClient(app) as client:
        project_id = client.post(
            "/projects", json={"title": "Memory", "prompt": "Find memory systems"}
        ).json()["id"]
        client.post(
            f"/projects/{project_id}/runs/discovery",
            json={"query": "agent memory", "limit": 1},
        )

        response = client.post(f"/projects/{project_id}/runs/pipeline")

        assert response.status_code == 409
        assert "Include or pin" in response.json()["detail"]


def test_acquisition_reports_provider_abstracts_idempotently(tmp_path: Path) -> None:
    app = create_app(
        f"sqlite:///{tmp_path / 'workbench.db'}",
        discovery_provider=FakeDiscoveryProvider(),
    )
    with TestClient(app) as client:
        project_id = client.post(
            "/projects", json={"title": "Memory", "prompt": "Find memory systems"}
        ).json()["id"]
        client.post(
            f"/projects/{project_id}/runs/discovery",
            json={"query": "agent memory", "limit": 2},
        )

        first = client.post(f"/projects/{project_id}/runs/acquisition")
        second = client.post(f"/projects/{project_id}/runs/acquisition")

        assert first.status_code == 201
        assert first.json() == {
            "project_id": project_id,
            "paper_count": 2,
            "available_count": 2,
            "degraded_count": 0,
        }
        assert second.json() == first.json()


def test_pipeline_budget_gate_prevents_oversized_runs(tmp_path: Path) -> None:
    app = create_app(
        f"sqlite:///{tmp_path / 'workbench.db'}",
        discovery_provider=FakeDiscoveryProvider(),
    )
    with TestClient(app) as client:
        project_id = client.post(
            "/projects", json={"title": "Memory", "prompt": "Find memory systems"}
        ).json()["id"]
        client.post(
            f"/projects/{project_id}/runs/discovery",
            json={"query": "agent memory", "limit": 2},
        )
        for paper in client.get(f"/projects/{project_id}/corpus").json()["papers"]:
            assert client.patch(
                f"/projects/{project_id}/corpus/{paper['id']}",
                json={"status": "included"},
            ).status_code == 200

        response = client.post(
            f"/projects/{project_id}/runs/pipeline",
            json={"max_papers": 1},
        )

        assert response.status_code == 409
        assert "budget" in response.json()["detail"].lower()
