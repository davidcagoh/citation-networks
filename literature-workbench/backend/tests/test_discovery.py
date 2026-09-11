from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.main import create_app
from app.models import (
    CitationEdge,
    CorpusMembership,
    DiscoveryEvent,
    EvidenceSpan,
    Paper,
    ProviderApproval,
    ReviewProtocol,
    ReviewSentence,
    ScientificRelation,
    SourceDocument,
    SynthesisClaim,
    UsageCostEvent,
)
from app.services.discovery import (
    DiscoveryCandidate,
    DiscoveryProviderError,
    MultiSourceDiscoveryProvider,
    OpenAlexProvider,
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
    citation_count: int | None = None
    publication_date: str | None = None


class FakeHTTPResponse:
    def __init__(self, payload: dict) -> None:
        import json

        self.body = json.dumps(payload).encode()

    def __enter__(self) -> "FakeHTTPResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.body


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
                citation_count=420,
                publication_date="2025-01-15",
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

    def related(self, external_id: str, direction: str, limit: int) -> list[FakeCandidate]:
        assert external_id == "paper-1"
        assert direction in {"backward", "forward"}
        return [
            FakeCandidate(
                external_id="paper-3",
                title="Earlier Memory Systems",
                authors=["C. Researcher"],
                year=2023,
                venue="Prior Venue",
                doi="10.1234/earlier-memory",
                abstract="An earlier study.",
                source_uri="https://example.test/paper-3",
                score=0.7,
            )
        ][:limit]


class PaidDiscoveryProvider(FakeDiscoveryProvider):
    name = "paid-search"
    requires_approval = True


class ChainDiscoveryProvider(FakeDiscoveryProvider):
    def related(self, external_id: str, direction: str, limit: int) -> list[FakeCandidate]:
        candidates = {
            "paper-1": "paper-3",
            "paper-3": "paper-4",
        }
        next_id = candidates.get(external_id)
        if next_id is None:
            return []
        return [
            FakeCandidate(
                external_id=next_id,
                title=f"Memory Study {next_id}",
                authors=["Network Researcher"],
                year=2022,
                venue="Network Venue",
                doi=None,
                abstract=f"Abstract for {next_id}.",
                source_uri=f"https://example.test/{next_id}",
                score=0.5,
            )
        ][:limit]


class CutoffCitationProvider(FakeDiscoveryProvider):
    def related(self, external_id: str, direction: str, limit: int) -> list[FakeCandidate]:
        return [
            FakeCandidate(
                external_id="before-citation-cutoff",
                title="Earlier cited memory study",
                authors=["Network Researcher"],
                year=2025,
                venue="Network Venue",
                doi=None,
                abstract="An earlier cited study.",
                source_uri="https://example.test/before-citation-cutoff",
                score=0.7,
                publication_date="2025-12-31",
            ),
            FakeCandidate(
                external_id="after-citation-cutoff",
                title="Later cited memory study",
                authors=["Network Researcher"],
                year=2026,
                venue="Network Venue",
                doi=None,
                abstract="A later cited study.",
                source_uri="https://example.test/after-citation-cutoff",
                score=0.6,
                publication_date="2026-01-01",
            ),
        ][:limit]


class SignalOrderProvider(FakeDiscoveryProvider):
    def search(self, query: str, limit: int) -> list[FakeCandidate]:
        return [
            FakeCandidate(
                external_id="low-impact",
                title="Recent Memory Study",
                authors=["A. Researcher"],
                year=2024,
                venue="Test Venue",
                doi=None,
                abstract="A memory study.",
                source_uri="https://example.test/low",
                score=0.2,
                citation_count=4,
                publication_date="2024-01-01",
            ),
            FakeCandidate(
                external_id="high-impact",
                title="Foundational Memory Study",
                authors=["B. Researcher"],
                year=2020,
                venue="Test Venue",
                doi=None,
                abstract="A foundational memory study.",
                source_uri="https://example.test/high",
                score=0.9,
                citation_count=400,
                publication_date="2020-01-01",
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
        cited_paper = next(
            paper for paper in corpus["papers"] if paper["title"] == "Memory Systems"
        )
        assert cited_paper["citation_count"] == 420
        assert cited_paper["publication_date"] == "2025-01-15"

        with app.state.database.session() as database:
            paper = database.scalar(select(Paper).where(Paper.doi == "10.1234/memory"))
            assert paper is not None
            assert paper.metadata_provenance["citation_count"] == 420
            assert paper.metadata_provenance["publication_date"] == "2025-01-15"
            event = database.scalar(
                select(DiscoveryEvent).where(DiscoveryEvent.paper_id == paper.id)
            )
            assert event is not None
            assert "citation_count=420" in event.rationale
            assert "publication_date=2025-01-15" in event.rationale

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


def test_seminal_route_orders_candidates_by_citation_signal(tmp_path: Path) -> None:
    app = create_app(
        f"sqlite:///{tmp_path / 'workbench.db'}", discovery_provider=SignalOrderProvider()
    )
    with TestClient(app) as client:
        project_id = client.post(
            "/projects", json={"title": "Memory", "prompt": "Find memory systems"}
        ).json()["id"]
        response = client.post(
            f"/projects/{project_id}/runs/discovery",
            json={"query": "memory", "limit": 2, "routes": ["seminal_search"]},
        )
        assert response.status_code == 201
        with app.state.database.session() as database:
            events = list(
                database.scalars(
                    select(DiscoveryEvent)
                    .where(DiscoveryEvent.project_id == project_id)
                    .order_by(DiscoveryEvent.rank)
                )
            )
            ranked_papers = {
                paper.id: paper.canonical_title
                for paper in database.scalars(select(Paper).where(Paper.project_id == project_id))
            }
            assert ranked_papers[events[0].paper_id] == "Foundational Memory Study"
            assert events[0].rank == 1


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


def test_discovery_can_run_multiple_named_routes_with_separate_usage_events(tmp_path: Path) -> None:
    provider = FakeDiscoveryProvider()
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}", discovery_provider=provider)
    with TestClient(app) as client:
        project_id = client.post(
            "/projects", json={"title": "Memory", "prompt": "Find memory systems"}
        ).json()["id"]
        response = client.post(
            f"/projects/{project_id}/runs/discovery",
            json={
                "query": "agent memory",
                "limit": 1,
                "routes": ["semantic_search", "survey_search", "recent_search"],
            },
        )

        assert response.status_code == 201
        assert response.json()["route_count"] == 3
        assert len(provider.queries) == 3
        with app.state.database.session() as database:
            events = list(
                database.scalars(
                    select(DiscoveryEvent)
                    .where(DiscoveryEvent.project_id == project_id)
                    .order_by(DiscoveryEvent.created_at, DiscoveryEvent.id)
                )
            )
            assert [event.route for event in events] == [
                "semantic_search",
                "survey_search",
                "recent_search",
            ]
            usage = list(
                database.scalars(
                    select(UsageCostEvent).where(UsageCostEvent.project_id == project_id)
                )
            )
            assert len(usage) == 3
            assert sum(event.external_api_calls for event in usage) == 3


def test_seminal_route_records_foundational_query_provenance(tmp_path: Path) -> None:
    provider = FakeDiscoveryProvider()
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}", discovery_provider=provider)
    with TestClient(app) as client:
        project_id = client.post(
            "/projects", json={"title": "Memory", "prompt": "Find memory systems"}
        ).json()["id"]
        response = client.post(
            f"/projects/{project_id}/runs/discovery",
            json={"query": "agent memory", "limit": 1, "routes": ["seminal_search"]},
        )

        assert response.status_code == 201
        assert provider.queries == [
            ("agent memory foundational seminal influential highly cited", 1)
        ]
        with app.state.database.session() as database:
            event = database.scalar(select(DiscoveryEvent))
            assert event is not None
            assert event.route == "seminal_search"


def test_cross_disciplinary_route_records_adjacent_fields_query(tmp_path: Path) -> None:
    provider = FakeDiscoveryProvider()
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}", discovery_provider=provider)
    with TestClient(app) as client:
        project_id = client.post(
            "/projects", json={"title": "Memory", "prompt": "Find memory systems"}
        ).json()["id"]
        response = client.post(
            f"/projects/{project_id}/runs/discovery",
            json={"query": "agent memory", "limit": 1, "routes": ["cross_disciplinary_search"]},
        )

        assert response.status_code == 201
        assert provider.queries == [
            ("agent memory interdisciplinary cross-disciplinary adjacent fields", 1),
            ("agent memory interdisciplinary methods", 1),
            ("agent memory applications in adjacent fields", 1),
        ]


def test_citation_expansion_persists_directional_edges_and_provenance(tmp_path: Path) -> None:
    provider = FakeDiscoveryProvider()
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}", discovery_provider=provider)
    with TestClient(app) as client:
        project_id = client.post(
            "/projects", json={"title": "Memory", "prompt": "Find memory systems"}
        ).json()["id"]
        client.post(
            f"/projects/{project_id}/runs/discovery",
            json={"query": "memory", "limit": 1},
        )
        seed_id = client.get(f"/projects/{project_id}/corpus").json()["papers"][0]["id"]

        response = client.post(
            f"/projects/{project_id}/runs/citation-expansion",
            json={"paper_id": seed_id, "direction": "backward", "limit": 10},
        )

        assert response.status_code == 201
        assert response.json()["candidate_count"] == 1
        graph = client.get(f"/projects/{project_id}/graph").json()
        assert graph["citation_edges"] == [
            {
                "source_paper_id": seed_id,
                "target_paper_id": graph["citation_edges"][0]["target_paper_id"],
                "direction": "backward",
                "provider": "fake-search",
            }
        ]
        with app.state.database.session() as database:
            edge = database.scalar(select(CitationEdge))
            assert edge is not None
            assert edge.source_paper_id != edge.target_paper_id
            assert edge.direction == "backward"
            assert edge.provider == "fake-search"
            event = database.scalar(
                select(DiscoveryEvent).where(DiscoveryEvent.route == "citation_backward")
            )
            assert event is not None
            assert event.paper_id == edge.target_paper_id


def test_on_demand_living_update_records_timestamp_and_new_papers(tmp_path: Path) -> None:
    provider = FakeDiscoveryProvider()
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}", discovery_provider=provider)
    with TestClient(app) as client:
        project_id = client.post(
            "/projects",
            json={
                "title": "Memory",
                "prompt": "Find memory systems",
                "review_mode": "comprehensive",
            },
        ).json()["id"]

        response = client.post(
            f"/projects/{project_id}/runs/living-update",
            json={"limit": 2},
        )

        assert response.status_code == 201
        body = response.json()
        assert body["route_count"] == 5
        assert body["new_paper_count"] == 2
        assert body["last_updated_at"]
        with app.state.database.session() as database:
            protocol = database.scalar(
                select(ReviewProtocol).where(ReviewProtocol.project_id == project_id)
            )
            assert protocol is not None
            recorded_at = datetime.fromisoformat(body["last_updated_at"]).replace(tzinfo=None)
            assert recorded_at == protocol.updated_at


def test_paid_provider_requires_explicit_non_replicable_approval(tmp_path: Path) -> None:
    app = create_app(
        f"sqlite:///{tmp_path / 'workbench.db'}", discovery_provider=PaidDiscoveryProvider()
    )
    with TestClient(app) as client:
        project_id = client.post(
            "/projects", json={"title": "Memory", "prompt": "Find memory systems"}
        ).json()["id"]
        path = f"/projects/{project_id}/runs/discovery"

        blocked = client.post(path, json={"query": "memory", "limit": 1})
        assert blocked.status_code == 403
        assert "explicit project approval" in blocked.json()["detail"]

        approval = client.post(
            f"/projects/{project_id}/provider-approvals",
            json={
                "provider": "paid-search",
                "approved_by": "David Goh",
                "justification": "Provides licensed full-text indexing.",
                "non_replicable_reason": "The licensed index is unavailable through public APIs.",
            },
        )
        assert approval.status_code == 201
        assert approval.json()["approved"] is True

        allowed = client.post(path, json={"query": "memory", "limit": 1})
        assert allowed.status_code == 201
        with app.state.database.session() as database:
            record = database.scalar(select(ProviderApproval))
            assert record is not None
            assert record.provider == "paid-search"


def test_multi_hop_citation_expansion_stops_at_exhausted_frontier(tmp_path: Path) -> None:
    app = create_app(
        f"sqlite:///{tmp_path / 'workbench.db'}", discovery_provider=ChainDiscoveryProvider()
    )
    with TestClient(app) as client:
        project_id = client.post(
            "/projects", json={"title": "Memory", "prompt": "Find memory systems"}
        ).json()["id"]
        client.post(
            f"/projects/{project_id}/runs/discovery",
            json={"query": "memory", "limit": 1},
        )
        seed_id = client.get(f"/projects/{project_id}/corpus").json()["papers"][0]["id"]

        response = client.post(
            f"/projects/{project_id}/runs/citation-expansion",
            json={"paper_id": seed_id, "direction": "backward", "limit": 10, "depth": 3},
        )

        assert response.status_code == 201
        assert response.json()["candidate_count"] == 2
        assert response.json()["depth_reached"] == 2
        assert response.json()["stopping_reason"] == "frontier_exhausted"


def test_citation_expansion_enforces_protocol_cutoff(tmp_path: Path) -> None:
    app = create_app(
        f"sqlite:///{tmp_path / 'workbench.db'}", discovery_provider=CutoffCitationProvider()
    )
    with TestClient(app) as client:
        project_id = client.post(
            "/projects",
            json={"title": "Memory", "prompt": "Find memory systems", "review_mode": "systematic"},
        ).json()["id"]
        protocol = client.put(
            f"/projects/{project_id}/protocol",
            json={
                "research_questions": ["Which memory studies exist?"],
                "cutoff_date": "2025-12-31",
            },
        )
        assert protocol.status_code == 200
        client.post(
            f"/projects/{project_id}/runs/discovery",
            json={"query": "memory", "limit": 1},
        )
        seed_id = client.get(f"/projects/{project_id}/corpus").json()["papers"][0]["id"]

        response = client.post(
            f"/projects/{project_id}/runs/citation-expansion",
            json={"paper_id": seed_id, "direction": "backward", "limit": 2},
        )

        assert response.status_code == 201
        assert response.json()["candidate_count"] == 1
        assert response.json()["filtered_count"] == 1
        titles = {
            paper["title"]
            for paper in client.get(f"/projects/{project_id}/corpus").json()["papers"]
        }
        assert titles == {"Memory Systems", "Earlier cited memory study"}


def test_co_citation_expansion_derives_shared_reference_neighbors(tmp_path: Path) -> None:
    provider = FakeDiscoveryProvider()
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}", discovery_provider=provider)
    with TestClient(app) as client:
        project_id = client.post(
            "/projects", json={"title": "Memory", "prompt": "Find memory systems"}
        ).json()["id"]
        client.post(
            f"/projects/{project_id}/runs/discovery",
            json={"query": "memory", "limit": 1},
        )
        seed_id = client.get(f"/projects/{project_id}/corpus").json()["papers"][0]["id"]
        client.post(
            f"/projects/{project_id}/runs/citation-expansion",
            json={"paper_id": seed_id, "direction": "backward", "limit": 1},
        )
        with app.state.database.session() as database:
            seed_edge = database.scalar(select(CitationEdge))
            assert seed_edge is not None
            other = Paper(
                project_id=project_id,
                canonical_title="Another Co-citing Study",
                authors=["D. Researcher"],
                year=2024,
                metadata_provenance={"external_id": "paper-4"},
            )
            database.add(other)
            database.flush()
            database.add(
                CorpusMembership(project_id=project_id, paper_id=other.id, status="candidate")
            )
            database.add(
                CitationEdge(
                    project_id=project_id,
                    source_paper_id=other.id,
                    target_paper_id=seed_edge.target_paper_id,
                    direction="backward",
                    provider="fake-search",
                )
            )

        response = client.post(
            f"/projects/{project_id}/runs/co-citation-expansion",
            json={"paper_id": seed_id, "limit": 10},
        )

        assert response.status_code == 201
        assert response.json()["candidate_count"] == 1
        with app.state.database.session() as database:
            event = database.scalar(
                select(DiscoveryEvent).where(DiscoveryEvent.route == "co_citation")
            )
            assert event is not None
            assert event.paper_id == other.id


def test_coverage_audit_explains_corpus_checkpoint_readiness(tmp_path: Path) -> None:
    provider = FakeDiscoveryProvider()
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}", discovery_provider=provider)
    with TestClient(app) as client:
        project_id = client.post(
            "/projects", json={"title": "Memory", "prompt": "Find memory systems"}
        ).json()["id"]
        client.post(
            f"/projects/{project_id}/runs/discovery",
            json={
                "query": "agent memory",
                "limit": 1,
                "routes": ["semantic_search", "recent_search"],
            },
        )

        audit = client.get(f"/projects/{project_id}/coverage-audit")

        assert audit.status_code == 200
        body = audit.json()
        assert body["status"] == "incomplete"
        assert body["routes"]["executed"] == ["semantic_search", "recent_search"]
        assert body["routes"]["summaries"] == [
            {"route": "semantic_search", "candidate_events": 1, "unique_papers": 1},
            {"route": "recent_search", "candidate_events": 1, "unique_papers": 1},
        ]
        assert body["routes"]["signal_coverage"] == [
            {
                "route": "semantic_search",
                "papers_with_publication_date": 1,
                "papers_with_citation_count": 1,
            },
            {
                "route": "recent_search",
                "papers_with_publication_date": 1,
                "papers_with_citation_count": 1,
            },
        ]
        assert body["screening"]["unresolved_candidates"] == 1
        assert "candidate papers remain unscreened" in body["limitations"]


def test_broader_coverage_audit_emits_stopping_certificate(tmp_path: Path) -> None:
    provider = FakeDiscoveryProvider()
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}", discovery_provider=provider)
    with TestClient(app) as client:
        project_id = client.post(
            "/projects",
            json={
                "title": "Memory",
                "prompt": "Find memory systems",
                "review_mode": "comprehensive",
            },
        ).json()["id"]
        client.post(
            f"/projects/{project_id}/runs/discovery",
            json={
                "query": "agent memory",
                "limit": 1,
                "routes": [
                    "semantic_search", "survey_search", "recent_search", "seminal_search",
                    "cross_disciplinary_search",
                ],
            },
        )
        corpus = client.get(f"/projects/{project_id}/corpus").json()["papers"]
        for paper in corpus:
            client.patch(
                f"/projects/{project_id}/corpus/{paper['id']}",
                json={"status": "included", "relevance_rationale": "In scope"},
            )

        audit = client.get(f"/projects/{project_id}/coverage-audit").json()

        assert audit["stopping_certificate"]["status"] == "satisfied"
        assert audit["stopping_certificate"]["required_routes"] == [
            "semantic_search",
            "survey_search",
            "recent_search",
            "seminal_search",
            "cross_disciplinary_search",
        ]
        assert audit["stopping_certificate"]["checks"] == {
            "required_routes_executed": True,
            "all_candidates_screened": True,
            "selected_sources_available": True,
        }


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


def test_pipeline_budget_gate_accounts_for_prior_provider_usage(tmp_path: Path) -> None:
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
        client.patch(
            f"/projects/{project_id}/corpus/{paper_id}", json={"status": "included"}
        )

        response = client.post(
            f"/projects/{project_id}/runs/pipeline",
            json={"max_external_api_calls": 0},
        )

        assert response.status_code == 409
        assert "api calls" in response.json()["detail"].lower()


def test_openalex_provider_maps_work_metadata_and_abstract(monkeypatch) -> None:
    requests: list[str] = []

    def fake_urlopen(request, timeout: float):
        requests.append(request.full_url)
        return FakeHTTPResponse(
            {
                "results": [
                    {
                        "id": "https://openalex.org/W123",
                        "title": "A memory study",
                        "publication_year": 2025,
                        "publication_date": "2025-04-02",
                        "doi": "https://doi.org/10.1234/memory",
                        "cited_by_count": 123,
                        "authorships": [
                            {"author": {"display_name": "A. Researcher"}}
                        ],
                        "primary_location": {
                            "landing_page_url": "https://example.test/memory"
                        },
                        "abstract_inverted_index": {"Memory": [0], "works": [1]},
                    }
                ]
            }
        )

    monkeypatch.setattr("app.services.discovery.urlopen", fake_urlopen)
    candidates = OpenAlexProvider(email="researcher@example.test").search("memory", 5)

    assert requests and "search=memory" in requests[0]
    assert "mailto=researcher%40example.test" in requests[0]
    assert candidates[0].external_id == "openalex:W123"
    assert candidates[0].doi == "10.1234/memory"
    assert candidates[0].authors == ["A. Researcher"]
    assert candidates[0].abstract == "Memory works"
    assert candidates[0].citation_count == 123
    assert candidates[0].publication_date == "2025-04-02"


def test_multi_source_provider_merges_and_marks_provider_provenance() -> None:
    class LocalProvider:
        def __init__(self, name: str, external_id: str) -> None:
            self.name = name
            self.external_id = external_id

        def search(self, query: str, limit: int) -> list[DiscoveryCandidate]:
            return [
                DiscoveryCandidate(
                    external_id=self.external_id,
                    title=f"{self.name} result",
                    authors=[],
                    year=2025,
                    venue=None,
                    doi=None,
                    abstract=None,
                    source_uri=None,
                    score=None,
                )
            ][:limit]

        def related(self, external_id: str, direction: str, limit: int):
            return []

    provider = MultiSourceDiscoveryProvider(
        [LocalProvider("semantic-scholar", "s2-1"), LocalProvider("openalex", "W1")]
    )

    candidates = provider.search("memory", 5)

    assert [candidate.external_id for candidate in candidates] == ["s2-1", "W1"]
    assert [candidate.provider_name for candidate in candidates] == [
        "semantic-scholar",
        "openalex",
    ]


def test_app_wires_free_multi_source_discovery_by_default(tmp_path: Path) -> None:
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}")

    assert app.state.discovery.provider.name == "multi-source"


def test_coverage_audit_reports_partial_multi_source_fanout(tmp_path: Path) -> None:
    class FailingProvider:
        name = "unavailable-source"

        def search(self, query: str, limit: int):
            raise DiscoveryProviderError("provider unavailable")

        def related(self, external_id: str, direction: str, limit: int):
            return []

    class HealthyProvider:
        name = "available-source"

        def search(self, query: str, limit: int):
            return [
                DiscoveryCandidate(
                    external_id="available-1",
                    title="Available result",
                    authors=[],
                    year=2025,
                    venue=None,
                    doi=None,
                    abstract="Abstract.",
                    source_uri=None,
                    score=None,
                )
            ][:limit]

        def related(self, external_id: str, direction: str, limit: int):
            return []

    provider = MultiSourceDiscoveryProvider([FailingProvider(), HealthyProvider()])
    app = create_app(
        f"sqlite:///{tmp_path / 'workbench.db'}", discovery_provider=provider
    )
    with TestClient(app) as client:
        project_id = client.post(
            "/projects", json={"title": "Memory", "prompt": "Find memory systems"}
        ).json()["id"]
        response = client.post(
            f"/projects/{project_id}/runs/discovery",
            json={"query": "memory", "limit": 1},
        )
        assert response.status_code == 201

        audit = client.get(f"/projects/{project_id}/coverage-audit")

    assert audit.status_code == 200
    assert audit.json()["provider_status"] == [
        {"provider": "unavailable-source", "attempts": 1, "failures": 1},
        {"provider": "available-source", "attempts": 1, "failures": 0},
    ]


def test_openalex_provider_expands_forward_citations(monkeypatch) -> None:
    requests: list[str] = []

    def fake_urlopen(request, timeout: float):
        requests.append(request.full_url)
        return FakeHTTPResponse(
            {
                "results": [
                    {
                        "id": "https://openalex.org/W456",
                        "title": "A citing memory study",
                        "publication_year": 2026,
                        "publication_date": "2026-02-01",
                        "doi": None,
                        "cited_by_count": 2,
                        "authorships": [],
                        "primary_location": {},
                        "abstract_inverted_index": None,
                    }
                ]
            }
        )

    monkeypatch.setattr("app.services.discovery.urlopen", fake_urlopen)
    candidates = OpenAlexProvider().related("openalex:W123", "forward", 1)

    assert "filter=cites%3AW123" in requests[0]
    assert candidates[0].external_id == "openalex:W456"
    assert candidates[0].title == "A citing memory study"


def test_openalex_provider_expands_backward_references(monkeypatch) -> None:
    requests: list[str] = []
    responses = iter(
        [
            FakeHTTPResponse(
                {"referenced_works": ["https://openalex.org/W789"]}
            ),
            FakeHTTPResponse(
                {
                    "id": "https://openalex.org/W789",
                    "title": "A referenced memory study",
                    "publication_year": 2024,
                    "publication_date": "2024-03-01",
                    "doi": None,
                    "cited_by_count": 12,
                    "authorships": [],
                    "primary_location": {},
                    "abstract_inverted_index": None,
                }
            ),
        ]
    )

    def fake_urlopen(request, timeout: float):
        requests.append(request.full_url)
        return next(responses)

    monkeypatch.setattr("app.services.discovery.urlopen", fake_urlopen)
    candidates = OpenAlexProvider().related("openalex:W123", "backward", 1)

    assert requests == [
        "https://api.openalex.org/works/W123",
        "https://openalex.org/W789",
    ]
    assert candidates[0].external_id == "openalex:W789"
