from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import create_app
from app.models import Paper


class FakeZoteroClient:
    name = "zotero"

    def __init__(self) -> None:
        self.created: list[dict] = []

    def list_items(self, collection_key: str | None, limit: int) -> list[dict]:
        return [
            {
                "key": "Z1",
                "data": {
                    "itemType": "journalArticle",
                    "title": "Imported Memory Study",
                    "creators": [{
                        "creatorType": "author",
                        "firstName": "A",
                        "lastName": "Researcher",
                    }],
                    "date": "2025-01-01",
                    "publicationTitle": "Test Journal",
                    "DOI": "10.1234/memory",
                    "abstractNote": "A study of memory.",
                    "url": "https://example.test/memory",
                },
            }
        ][:limit]

    def create_items(self, items: list[dict], collection_key: str | None) -> int:
        self.created.extend(items)
        return len(items)


class PublishedPreferenceClient(FakeZoteroClient):
    def __init__(self) -> None:
        super().__init__()
        self.import_number = 0

    def list_items(self, collection_key: str | None, limit: int) -> list[dict]:
        self.import_number += 1
        if self.import_number == 1:
            data = {
                "itemType": "preprint",
                "title": "Preprint Memory Study",
                "date": "2024-01-01",
                "DOI": "10.1234/memory",
                "abstractNote": "The preprint abstract.",
                "url": "https://arxiv.org/abs/1234.5678",
            }
        else:
            data = {
                "itemType": "journalArticle",
                "title": "Published Memory Study",
                "date": "2025-01-01",
                "publicationTitle": "Published Journal",
                "DOI": "10.1234/memory",
                "abstractNote": "The published abstract.",
                "url": "https://publisher.example/memory",
            }
        return [{"key": f"Z{self.import_number}", "data": data}][:limit]


def test_zotero_import_and_export_round_trip_selected_metadata(tmp_path: Path) -> None:
    client = FakeZoteroClient()
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}", zotero_client=client)
    with TestClient(app) as http:
        project_id = http.post(
            "/projects", json={"title": "Memory", "prompt": "Survey memory"}
        ).json()["id"]
        imported = http.post(
            f"/projects/{project_id}/integrations/zotero/import",
            json={"limit": 1, "collection_key": "COLLECTION"},
        )

        assert imported.status_code == 201
        assert imported.json() == {"project_id": project_id, "imported_count": 1, "item_count": 1}
        paper = http.get(f"/projects/{project_id}/corpus").json()["papers"][0]
        assert paper["title"] == "Imported Memory Study"
        assert http.patch(
            f"/projects/{project_id}/corpus/{paper['id']}", json={"status": "included"}
        ).status_code == 200

        exported = http.post(
            f"/projects/{project_id}/integrations/zotero/export",
            json={"collection_key": "COLLECTION"},
        )

        assert exported.status_code == 201
        assert exported.json() == {"project_id": project_id, "exported_count": 1}
        assert client.created[0]["title"] == "Imported Memory Study"
        assert client.created[0]["DOI"] == "10.1234/memory"


def test_zotero_import_validates_limit_and_unknown_project(tmp_path: Path) -> None:
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}", zotero_client=FakeZoteroClient())
    with TestClient(app) as http:
        assert http.post(
            "/projects/missing/integrations/zotero/import", json={"limit": 0}
        ).status_code == 422


def test_zotero_prefers_published_record_but_retains_preprint_provenance(tmp_path: Path) -> None:
    client = PublishedPreferenceClient()
    app = create_app(f"sqlite:///{tmp_path / 'workbench.db'}", zotero_client=client)
    with TestClient(app) as http:
        project_id = http.post(
            "/projects", json={"title": "Memory", "prompt": "Survey memory"}
        ).json()["id"]
        for _ in range(2):
            response = http.post(
                f"/projects/{project_id}/integrations/zotero/import",
                json={"limit": 1},
            )
            assert response.status_code == 201

    with app.state.database.session() as db:
        papers = list(db.scalars(select(Paper).where(Paper.project_id == project_id)))
        assert len(papers) == 1
        paper = papers[0]
        assert paper.canonical_title == "Published Memory Study"
        assert paper.venue == "Published Journal"
        provenance = paper.metadata_provenance or {}
        assert provenance["publication_status"] == "published"
        assert provenance["zotero_key"] == "Z2"
        assert provenance["alternate_records"] == [{
            "publication_status": "preprint",
            "source_uri": "https://arxiv.org/abs/1234.5678",
            "title": "Preprint Memory Study",
            "zotero_key": "Z1",
        }]
