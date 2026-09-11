from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import create_app
from app.models import EvidenceSpan, ScientificRelation, SourceDocument, SynthesisClaim
from app.services.acquisition import FetchedSource, SafeSourceFetcher
from app.services.discovery import DiscoveryCandidate


def minimal_pdf(text: str) -> bytes:
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode()
    objects.append(f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream")
    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, payload in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{index} 0 obj\n".encode())
        output.extend(payload)
        output.extend(b"\nendobj\n")
    xref_offset = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode())
    output.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n".encode()
    )
    return bytes(output)


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
        assert client.post(f"/projects/{project_id}/runs/pipeline").status_code == 201

    with app.state.database.session() as database:
        span = database.scalar(select(EvidenceSpan))
        assert span is not None
        assert span.extractor_version == "fulltext-heuristic-v1"


def test_acquisition_fetches_eligible_discovered_full_text_links(tmp_path: Path) -> None:
    class DiscoveryFixture:
        name = "fixture-provider"

        def search(self, query: str, limit: int):
            return [
                DiscoveryCandidate(
                    external_id="fixture-paper",
                    title="Discovered Study",
                    authors=["Researcher"],
                    year=2025,
                    venue="Venue",
                    doi=None,
                    abstract="Abstract fallback.",
                    source_uri="https://example.test/discovered.html",
                    score=0.9,
                )
            ][:limit]

        def related(self, external_id: str, direction: str, limit: int):
            return []

    fetcher = FakeSourceFetcher()
    app = create_app(
        f"sqlite:///{tmp_path / 'workbench.db'}",
        discovery_provider=DiscoveryFixture(),
        source_fetcher=fetcher,
    )
    with TestClient(app) as client:
        project_id = client.post(
            "/projects", json={"title": "Memory", "prompt": "Review memory"}
        ).json()["id"]
        client.post(
            f"/projects/{project_id}/runs/discovery",
            json={"query": "memory", "limit": 1},
        )
        response = client.post(f"/projects/{project_id}/runs/acquisition")

        assert response.status_code == 201
        assert response.json()["fetched_count"] == 1
        assert fetcher.urls == ["https://example.test/discovered.html"]
        corpus = client.get(f"/projects/{project_id}/corpus").json()
        assert corpus["papers"][0]["source_type"] == "html"
        client.patch(
            f"/projects/{project_id}/corpus/{corpus['papers'][0]['id']}",
            json={"status": "included"},
        )
        assert client.post(f"/projects/{project_id}/runs/pipeline").status_code == 201

    with app.state.database.session() as database:
        span = database.scalar(select(EvidenceSpan))
        assert span is not None
        assert span.extractor_version == "fulltext-heuristic-v1"
        assert span.section == "full_text"

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


def test_extracts_text_from_bounded_pdf_bytes() -> None:
    assert SafeSourceFetcher.extract_pdf_text(minimal_pdf("PDF evidence.")) == "PDF evidence."


def test_url_ingestion_deduplicates_existing_paper_identity(tmp_path: Path) -> None:
    fetcher = FakeSourceFetcher()
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}", source_fetcher=fetcher)
    with TestClient(app) as client:
        project_id = client.post(
            "/projects", json={"title": "Memory", "prompt": "Review memory"}
        ).json()["id"]
        payload = {
            "title": "Fetched Memory Study",
            "source_uri": "https://8.8.8.8/paper.txt",
            "doi": "10.1234/memory",
        }
        first = client.post(f"/projects/{project_id}/sources/url", json=payload)
        second = client.post(f"/projects/{project_id}/sources/url", json=payload)

        assert first.status_code == 201
        assert second.status_code == 201
        assert first.json()["paper_id"] == second.json()["paper_id"]
        assert client.get(f"/projects/{project_id}/corpus").json()["paper_count"] == 1
