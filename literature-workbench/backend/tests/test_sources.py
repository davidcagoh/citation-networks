from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import create_app
from app.models import EvidenceSpan, ScientificRelation, SourceDocument, SynthesisClaim
from app.services.acquisition import FetchedSource


class FakeSourceFetcher:
    def __init__(self) -> None:
        self.urls: list[str] = []

    def fetch(self, source_uri: str) -> FetchedSource:
        self.urls.append(source_uri)
        text = (
            "<html><head><title>Ignore</title><script>bad()</script></head>"
            "<body><h1>Fetched Study</h1><p>Memory evidence.</p></body></html>"
            if source_uri.endswith(".html")
            else "Fetched paper text with memory evidence."
        )
        return FetchedSource(
            text=text,
            content_type="text/html" if source_uri.endswith(".html") else "text/plain",
            final_uri=source_uri,
        )


def test_ingests_user_supplied_full_text_with_provenance(tmp_path: Path) -> None:
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}")
    with TestClient(app) as client:
        project_id = client.post(
            "/projects", json={"title": "Memory", "prompt": "Survey memory systems"}
        ).json()["id"]
        response = client.post(
            f"/projects/{project_id}/sources/text",
            json={
                "title": "A Full Text Study",
                "authors": ["A. Researcher"],
                "year": 2026,
                "source_uri": "file:///research/full-text.txt",
                "text": "The study evaluates a memory architecture across two workloads.",
            },
        )

        assert response.status_code == 201
        body = response.json()
        assert body["status"] == "included"
        paper_id = body["paper_id"]
        corpus = client.get(f"/projects/{project_id}/corpus").json()
        assert corpus["papers"][0]["id"] == paper_id
        assert corpus["papers"][0]["document_status"] == "complete"

        run = client.post(f"/projects/{project_id}/runs/pipeline")
        assert run.status_code == 201
        review = client.get(f"/projects/{project_id}/review").json()["sentences"]
        assert review[0]["text"] == (
            "The study evaluates a memory architecture across two workloads."
        )
        plan = client.get(f"/projects/{project_id}/plans").json()["plans"][0]
        assert "source text" in plan["thesis"].lower()
        with app.state.database.session() as database:
            span = database.scalar(select(EvidenceSpan))
            assert span is not None
            assert span.extractor_version == "text-heuristic-v1"


def test_source_ingestion_rejects_blank_text_and_unknown_project(tmp_path: Path) -> None:
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}")
    with TestClient(app) as client:
        assert client.post(
            "/projects/missing/sources/text",
            json={"title": "Source", "source_uri": "file:///source", "text": "Text."},
        ).status_code == 404
        project_id = client.post(
            "/projects", json={"title": "Memory", "prompt": "Survey memory systems"}
        ).json()["id"]
        response = client.post(
            f"/projects/{project_id}/sources/text",
            json={"title": "Empty", "source_uri": "file:///empty", "text": " "},
        )
        assert response.status_code == 422


def test_live_pipeline_builds_conservative_cross_paper_relation(tmp_path: Path) -> None:
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}")
    with TestClient(app) as client:
        project_id = client.post(
            "/projects", json={"title": "Memory", "prompt": "Compare memory systems"}
        ).json()["id"]
        for title, text in [
            ("Retrieval Memory", "A memory architecture improves retrieval quality."),
            ("Consolidated Memory", "A memory architecture reduces retrieval interference."),
        ]:
            assert client.post(
                f"/projects/{project_id}/sources/text",
                json={
                    "title": title,
                    "source_uri": f"file:///{title.replace(' ', '-')}",
                    "text": text,
                },
            ).status_code == 201

        response = client.post(f"/projects/{project_id}/runs/pipeline")

        assert response.status_code == 201
        with app.state.database.session() as database:
            relation = database.scalar(
                select(ScientificRelation).where(ScientificRelation.project_id == project_id)
            )
            assert relation is not None
            assert relation.relation_type == "same_topic_different_source"
            assert relation.inference_level == "model_inference"
            assert relation.evidence_span_ids
            claims = list(
                database.scalars(
                    select(SynthesisClaim).where(SynthesisClaim.project_id == project_id)
                )
            )
            assert any(claim.supporting_relation_ids for claim in claims)


def test_fetches_public_source_url_with_provenance_and_blocks_private_targets(
    tmp_path: Path,
) -> None:
    fetcher = FakeSourceFetcher()
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}", source_fetcher=fetcher)
    with TestClient(app) as client:
        project_id = client.post(
            "/projects", json={"title": "Memory", "prompt": "Review memory"}
        ).json()["id"]
        response = client.post(
            f"/projects/{project_id}/sources/url",
            json={"title": "Fetched Memory Study", "source_uri": "https://8.8.8.8/paper.txt"},
        )

        assert response.status_code == 201
        paper_id = response.json()["paper_id"]
        assert fetcher.urls == ["https://8.8.8.8/paper.txt"]
        corpus = client.get(f"/projects/{project_id}/corpus").json()
        assert corpus["papers"][0]["id"] == paper_id
        assert corpus["papers"][0]["source_type"] == "fetched_text"
        with app.state.database.session() as database:
            source = database.scalar(
                select(SourceDocument).where(SourceDocument.paper_id == paper_id)
            )
            assert source is not None
            assert source.source_uri == "https://8.8.8.8/paper.txt"
        assert source.parser == "url-fetch-v1"

        html_response = client.post(
            f"/projects/{project_id}/sources/url",
            json={"title": "HTML Study", "source_uri": "https://8.8.8.8/paper.html"},
        )
        assert html_response.status_code == 201
        html_paper_id = html_response.json()["paper_id"]
        with app.state.database.session() as database:
            html_source = database.scalar(
                select(SourceDocument).where(SourceDocument.paper_id == html_paper_id)
            )
            assert html_source is not None
            assert html_source.source_type == "html"
            assert html_source.text == "Fetched Study Memory evidence."

        blocked = client.post(
            f"/projects/{project_id}/sources/url",
            json={"title": "Private", "source_uri": "http://127.0.0.1/private.txt"},
        )
        assert blocked.status_code == 400
        assert "public" in blocked.json()["detail"]
