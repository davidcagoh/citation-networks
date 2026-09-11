from dataclasses import dataclass
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.main import create_app
from app.models import CorpusMembership, DiscoveryEvent, Paper


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
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}", discovery_provider=FakeDiscoveryProvider())
    with TestClient(app) as client:
        project_id = client.post(
            "/projects", json={"title": "Memory", "prompt": "Find memory systems"}
        ).json()["id"]
        path = f"/projects/{project_id}/runs/discovery"

        assert client.post(path, json={"query": " ", "limit": 10}).status_code == 422
        assert client.post(path, json={"query": "memory", "limit": 0}).status_code == 422
        assert client.post(path, json={"query": "memory", "limit": 101}).status_code == 422
