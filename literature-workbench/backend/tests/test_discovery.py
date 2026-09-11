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
        assert corpus["papers"][0]["citation_count"] == 420
        assert corpus["papers"][0]["publication_date"] == "2025-01-15"

        with app.state.database.session() as database:
            paper = database.scalar(select(Paper).where(Paper.doi == "10.1234/memory"))
            assert paper is not None
            assert paper.metadata_provenance["citation_count"] == 420
            assert paper.metadata_provenance["publication_date"] == "2025-01-15"

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
            ("agent memory interdisciplinary cross-disciplinary adjacent fields", 1)
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
