from __future__ import annotations

import json
import os
from collections.abc import Callable
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from sqlalchemy import select

from app.db import Database
from app.models import (
    CorpusMembership,
    DiscoveryEvent,
    Paper,
    Project,
    SourceDocument,
    UsageCostEvent,
)


class ZoteroError(Exception):
    """Raised when Zotero credentials or transport are unavailable."""


class ZoteroClient:
    name = "zotero"

    def __init__(
        self, opener: Callable[..., object] = urlopen, timeout_seconds: float = 20.0
    ) -> None:
        self.api_key = os.getenv("ZOTERO_API_KEY")
        self.user_id = os.getenv("ZOTERO_USER_ID")
        self.library_type = os.getenv("ZOTERO_LIBRARY_TYPE", "users")
        self.opener = opener
        self.timeout_seconds = timeout_seconds

    def _request(self, method: str, path: str, payload: object | None = None) -> object:
        if not self.api_key or not self.user_id:
            raise ZoteroError("Zotero credentials are not configured")
        body = None if payload is None else json.dumps(payload).encode()
        request = Request(
            f"https://api.zotero.org/{self.library_type}/{self.user_id}/{path}",
            data=body,
            method=method,
            headers={
                "Accept": "application/json",
                "Zotero-API-Key": self.api_key,
                "Zotero-API-Version": "3",
                "Content-Type": "application/json",
            },
        )
        try:
            with self.opener(request, timeout=self.timeout_seconds) as response:
                return json.load(response)
        except Exception as exc:
            raise ZoteroError("Zotero request failed") from exc

    def list_items(self, collection_key: str | None, limit: int) -> list[dict]:
        path = f"collections/{collection_key}/items" if collection_key else "items"
        payload = self._request("GET", f"{path}?{urlencode({'limit': limit, 'format': 'json'})}")
        return payload if isinstance(payload, list) else []

    def create_items(self, items: list[dict], collection_key: str | None) -> int:
        path = f"collections/{collection_key}/items" if collection_key else "items"
        payload = self._request("POST", path, items)
        return len(items) if isinstance(payload, dict) else 0


class ZoteroService:
    def __init__(self, database: Database, client: ZoteroClient) -> None:
        self.database = database
        self.client = client

    def import_items(self, project_id: str, collection_key: str | None, limit: int) -> int:
        with self.database.session() as db:
            if db.get(Project, project_id) is None:
                raise ZoteroError("Project not found")
        items = self.client.list_items(collection_key, limit)
        with self.database.session() as db:
            for item in items:
                data = item.get("data") or {}
                title = str(data.get("title") or "").strip()
                if not title:
                    continue
                doi = data.get("DOI")
                existing = self._find_paper(db, project_id, doi, title)
                if existing is None:
                    creators = data.get("creators") or []
                    authors = [
                        " ".join(
                            filter(None, [creator.get("firstName"), creator.get("lastName")])
                        ).strip()
                        for creator in creators
                        if creator.get("creatorType", "author") == "author"
                    ]
                    year_text = str(data.get("date") or "")[:4]
                    paper = Paper(
                        project_id=project_id,
                        canonical_title=title,
                        authors=[author for author in authors if author],
                        year=int(year_text) if year_text.isdigit() else None,
                        venue=data.get("publicationTitle"),
                        doi=doi,
                        abstract=data.get("abstractNote"),
                        metadata_provenance={
                            "provider": "zotero",
                            "external_id": item.get("key"),
                            "source_uri": data.get("url"),
                            "zotero_key": item.get("key"),
                        },
                    )
                    db.add(paper)
                    db.flush()
                    db.add(CorpusMembership(
                        project_id=project_id, paper_id=paper.id, status="candidate",
                        relevance_score=0.0, relevance_rationale="Imported from Zotero",
                    ))
                    existing = paper
                abstract = (data.get("abstractNote") or "").strip()
                if abstract and db.scalar(select(SourceDocument).where(
                    SourceDocument.paper_id == existing.id,
                    SourceDocument.source_type == "abstract",
                    SourceDocument.source_uri == (data.get("url") or f"zotero://{item.get('key')}"),
                )) is None:
                    db.add(SourceDocument(
                        paper_id=existing.id, source_type="abstract",
                        source_uri=data.get("url") or f"zotero://{item.get('key')}",
                        text=abstract, parsing_quality="complete", parser="zotero-abstract-v1",
                    ))
                db.add(DiscoveryEvent(
                    project_id=project_id, paper_id=existing.id, route="zotero_import",
                    action="candidate", rationale="Imported from Zotero", provider="zotero",
                ))
            db.add(UsageCostEvent(project_id=project_id, provider="zotero", external_api_calls=1))
            return len(items)

    def export_selected(self, project_id: str, collection_key: str | None) -> int:
        with self.database.session() as db:
            if db.get(Project, project_id) is None:
                raise ZoteroError("Project not found")
            papers = list(db.scalars(
                select(Paper).join(CorpusMembership, CorpusMembership.paper_id == Paper.id).where(
                    CorpusMembership.project_id == project_id,
                    CorpusMembership.status.in_(["included", "pinned"]),
                )
            ))
        items = [self._zotero_item(paper) for paper in papers]
        count = self.client.create_items(items, collection_key) if items else 0
        with self.database.session() as db:
            db.add(UsageCostEvent(project_id=project_id, provider="zotero", external_api_calls=1))
        return count

    @staticmethod
    def _find_paper(db, project_id: str, doi: str | None, title: str) -> Paper | None:
        papers = list(db.scalars(select(Paper).where(Paper.project_id == project_id)))
        for paper in papers:
            if doi and paper.doi and paper.doi.casefold() == str(doi).casefold():
                return paper
            if paper.canonical_title.casefold() == title.casefold():
                return paper
        return None

    @staticmethod
    def _zotero_item(paper: Paper) -> dict:
        item = {
            "itemType": "journalArticle",
            "title": paper.canonical_title,
            "creators": [{"creatorType": "author", "name": author} for author in paper.authors],
            "date": str(paper.year) if paper.year else "",
            "publicationTitle": paper.venue or "",
            "DOI": paper.doi or "",
            "abstractNote": paper.abstract or "",
        }
        source_uri = (paper.metadata_provenance or {}).get("source_uri")
        if source_uri:
            item["url"] = source_uri
        return item
