from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


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
                    "creators": [{"creatorType": "author", "firstName": "A", "lastName": "Researcher"}],
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
